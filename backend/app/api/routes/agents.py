from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from typing import List, Dict, Any, Optional
import os
import shutil
from pydantic import BaseModel

from app.core.database import get_db
from app.agents.models import Agent, Prompt, PromptVersion, AgentVersion
from app.logs.models import AgentRun
from app.logs.service import logs_service
from app.agents.orchestrator import orchestrator
from app.logging.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/agents", tags=["agents"])

# Pydantic schemas
class AgentCreate(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None
    agent_type: str
    prompt_content: str
    tools_enabled: List[str] = []
    memory_enabled: bool = True
    max_steps: int = 10
    timeout_seconds: int = 120
    model_policy_id: Optional[int] = None

class AgentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    prompt_content: Optional[str] = None
    tools_enabled: Optional[List[str]] = None
    memory_enabled: Optional[bool] = None
    max_steps: Optional[int] = None
    timeout_seconds: Optional[int] = None
    model_policy_id: Optional[int] = None
    status: Optional[str] = None

class RunPayload(BaseModel):
    query: str

@router.get("")
async def list_agents(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Agent).order_by(Agent.name))
    return result.scalars().all()

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_agent(payload: AgentCreate, db: AsyncSession = Depends(get_db)):
    # Check if slug exists
    slug_res = await db.execute(select(Agent).where(Agent.slug == payload.slug))
    if slug_res.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"Agent with slug '{payload.slug}' already exists.")

    try:
        # 1. Create Prompt
        prompt = Prompt(
            name=f"{payload.name} Prompt",
            slug=f"{payload.slug}_prompt",
            description=f"Prompt template for {payload.name}"
        )
        db.add(prompt)
        await db.commit()
        await db.refresh(prompt)

        # 2. Create Prompt Version
        prompt_ver = PromptVersion(
            prompt_id=prompt.id,
            content=payload.prompt_content,
            version=1
        )
        db.add(prompt_ver)
        await db.commit()
        await db.refresh(prompt_ver)

        # 3. Create Agent
        agent = Agent(
            name=payload.name,
            slug=payload.slug,
            description=payload.description,
            agent_type=payload.agent_type,
            prompt_id=prompt.id,
            prompt_version_id=prompt_ver.id,
            tools_enabled=payload.tools_enabled,
            memory_enabled=payload.memory_enabled,
            max_steps=payload.max_steps,
            timeout_seconds=payload.timeout_seconds,
            status="active",
            model_policy_id=payload.model_policy_id
        )
        db.add(agent)
        await db.commit()
        await db.refresh(agent)
        return agent
    except Exception as e:
        logger.exception("Failed to create agent", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to create agent: {str(e)}")

@router.get("/{agent_id}")
async def get_agent(agent_id: int, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = res.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found.")
    
    # Retrieve active prompt text
    prompt_text = ""
    if agent.prompt_version_id:
        p_res = await db.execute(select(PromptVersion).where(PromptVersion.id == agent.prompt_version_id))
        p_ver = p_res.scalar_one_or_none()
        if p_ver:
            prompt_text = p_ver.content
            
    # Serialize with prompt text
    data = dict(agent.__dict__)
    data.pop("_sa_instance_state", None)
    data["prompt_content"] = prompt_text
    return data

@router.put("/{agent_id}")
async def update_agent(agent_id: int, payload: AgentUpdate, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = res.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found.")

    try:
        # Handle prompt update
        if payload.prompt_content is not None and agent.prompt_id:
            # Query current version
            p_res = await db.execute(
                select(PromptVersion)
                .where(PromptVersion.prompt_id == agent.prompt_id)
                .order_by(PromptVersion.version.desc())
            )
            last_ver = p_res.scalars().first()
            next_version = (last_ver.version + 1) if last_ver else 1

            new_ver = PromptVersion(
                prompt_id=agent.prompt_id,
                content=payload.prompt_content,
                version=next_version
            )
            db.add(new_ver)
            await db.commit()
            await db.refresh(new_ver)
            agent.prompt_version_id = new_ver.id

        # Update remaining fields
        for field, val in payload.dict(exclude_unset=True).items():
            if field != "prompt_content":
                setattr(agent, field, val)

        await db.commit()
        await db.refresh(agent)
        return agent
    except Exception as e:
        logger.exception("Failed to update agent", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to update agent: {str(e)}")

@router.delete("/{agent_id}")
async def delete_agent(agent_id: int, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = res.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found.")

    try:
        await db.delete(agent)
        await db.commit()
        return {"success": True, "message": "Agent deleted successfully."}
    except Exception as e:
        logger.exception("Failed to delete agent", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to delete agent: {str(e)}")

@router.post("/{agent_id}/run")
async def run_agent(
    agent_id: int,
    payload: RunPayload,
    background: bool = Query(False),
    db: AsyncSession = Depends(get_db)
):
    # Verify agent exists
    res = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = res.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found.")

    if background:
        # Schedule Celery background job
        from app.jobs.worker import execute_agent_run
        
        # 1. Create running AgentRun row
        agent_run = AgentRun(
            agent_id=agent.id,
            input_query=payload.query,
            status="pending"
        )
        db.add(agent_run)
        await db.commit()
        await db.refresh(agent_run)

        # 2. Trigger Celery Task
        execute_agent_run.delay(agent_run.id, payload.query)
        logger.info("Enqueued background agent run Celery job", run_id=agent_run.id)
        return {
            "success": True,
            "message": "Agent run enqueued in Celery queue.",
            "agent_run_id": agent_run.id,
            "status": "pending"
        }
    else:
        # Synchronous execution
        try:
            result = await orchestrator.execute_run(
                agent_id=agent_id,
                query=payload.query,
                db=db
            )
            return result
        except Exception as e:
            logger.exception("Synchronous agent run failed", agent_id=agent_id)
            raise HTTPException(status_code=500, detail=f"Agent run failed: {str(e)}")

@router.get("/runs/{run_id}")
async def get_run_status(run_id: int, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(AgentRun).where(AgentRun.id == run_id))
    run = res.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Agent run not found.")
    return run

@router.get("/runs/{run_id}/steps")
async def get_run_steps(run_id: int, db: AsyncSession = Depends(get_db)):
    steps = await logs_service.get_agent_steps(run_id, db)
    tool_calls = await logs_service.get_tool_calls(run_id, db)
    llm_calls = await logs_service.get_llm_calls(db, agent_run_id=run_id, limit=500)
    
    unified_steps = list(steps)
    for call in llm_calls:
        content = f"Provider: {call['provider']}\nModel: {call['model']}\nLatency: {call['latency_ms']}ms\nTokens: {call['prompt_tokens']} in / {call['completion_tokens']} out\nStatus: {call['status']}"
        if call.get('failure_reason'):
            content += f"\nFailure: {call['failure_reason']}"
        if call.get('fallback_reason'):
            content += f"\nFallback: {call['fallback_reason']}"
            
        unified_steps.append({
            "id": f"llm_{call['id']}",
            "step_number": "-", 
            "action_type": "llm_call" if call['status'] == 'success' else "llm_error",
            "content": content,
            "created_at": call["created_at"],
            "metadata": call
        })
        
    # Sort chronologically
    unified_steps.sort(key=lambda x: x["created_at"] if x["created_at"] else "")

    return {
        "steps": unified_steps,
        "tool_calls": tool_calls
    }

@router.post("/workspace/upload")
async def upload_workspace_file(file: UploadFile = File(...)):
    from app.tools.registry import WORKSPACE_DIR
    try:
        os.makedirs(WORKSPACE_DIR, exist_ok=True)
        safe_name = os.path.basename(file.filename)
        filepath = os.path.join(WORKSPACE_DIR, safe_name)
        
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        return {"success": True, "message": f"File '{safe_name}' uploaded successfully to workspace.", "filename": safe_name}
    except Exception as e:
        logger.exception("Failed to upload file to workspace", error=str(e))
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")

from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.agents.models import Agent, AgentVersion, PromptVersion
from app.logs.models import AgentRun
from app.agents.base import BaseAgent
from app.logging.logger import get_logger

logger = get_logger(__name__)

class AgentOrchestrator:
    """Service class responsible for launching agent runs and saving state snapshots."""

    async def execute_run(
        self,
        agent_id: int,
        query: str,
        db: AsyncSession,
        user_id: int = None,
        workflow_run_id: int = None,
        history: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        logger.info("Orchestrator executing agent run", agent_id=agent_id, query=query)
        
        # 1. Fetch active agent config
        res = await db.execute(select(Agent).where(Agent.id == agent_id))
        agent = res.scalar_one_or_none()
        if not agent:
            raise ValueError(f"Agent with ID {agent_id} does not exist.")

        # 2. Get active prompt text
        prompt_content = ""
        if agent.prompt_version_id:
            prompt_res = await db.execute(
                select(PromptVersion).where(PromptVersion.id == agent.prompt_version_id)
            )
            p_ver = prompt_res.scalar_one_or_none()
            if p_ver:
                prompt_content = p_ver.content
        
        # 3. Create or find AgentVersion snapshot
        # For simplicity we generate a version or fetch existing version count
        ver_res = await db.execute(
            select(AgentVersion)
            .where(AgentVersion.agent_id == agent.id)
            .order_by(AgentVersion.version.desc())
        )
        last_ver = ver_res.scalars().first()
        version_num = (last_ver.version + 1) if last_ver else 1

        agent_version = AgentVersion(
            agent_id=agent.id,
            name=agent.name,
            description=agent.description,
            agent_type=agent.agent_type,
            prompt_content=prompt_content,
            model_policy_id=agent.model_policy_id,
            tools_enabled=agent.tools_enabled,
            memory_enabled=agent.memory_enabled,
            max_steps=agent.max_steps,
            timeout_seconds=agent.timeout_seconds,
            version=version_num
        )
        db.add(agent_version)
        await db.commit()
        await db.refresh(agent_version)

        # 4. Create AgentRun entry
        agent_run = AgentRun(
            agent_id=agent.id,
            agent_version_id=agent_version.id,
            user_id=user_id,
            workflow_run_id=workflow_run_id,
            input_query=query,
            status="running"
        )
        db.add(agent_run)
        await db.commit()
        await db.refresh(agent_run)

        # 5. Instantiate Agent worker
        agent_runner = BaseAgent(
            name=agent.name,
            agent_type=agent.agent_type,
            system_prompt=prompt_content,
            allowed_tools=agent.tools_enabled,
            max_steps=agent.max_steps,
            timeout_seconds=agent.timeout_seconds,
            model_policy_id=agent.model_policy_id
        )

        # 6. Execute loop (can run synchronously or in celery)
        try:
            result = await agent_runner.run(
                query=query,
                agent_run_id=agent_run.id,
                db=db,
                history=history
            )
            return {
                "agent_run_id": agent_run.id,
                "status": result["status"],
                "output": result["output"],
                "steps_count": result["steps_count"],
                "elapsed_seconds": result["elapsed_seconds"]
            }
        except Exception as e:
            logger.exception("Agent run execution failed in orchestrator", run_id=agent_run.id)
            agent_run.status = "failed"
            agent_run.output_response = f"Execution Error: {str(e)}"
            await db.commit()
            raise

orchestrator = AgentOrchestrator()

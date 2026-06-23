from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.workflows.models import Workflow, WorkflowRun, WorkflowStep
from app.workflows.engine import validate_dag
from app.logging.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/workflows", tags=["workflows"])

class WorkflowCreate(BaseModel):
    name: str
    description: Optional[str] = None
    definition_json: Dict[str, Any]

class WorkflowRunPayload(BaseModel):
    query: str

@router.get("")
async def list_workflows(db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Workflow).order_by(Workflow.name))
    return res.scalars().all()

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_workflow(payload: WorkflowCreate, db: AsyncSession = Depends(get_db)):
    try:
        # Validate DAG dependencies
        validate_dag(payload.definition_json)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"DAG validation failed: {str(exc)}")

    try:
        workflow = Workflow(
            name=payload.name,
            description=payload.description,
            definition_json=payload.definition_json,
            status="active"
        )
        db.add(workflow)
        await db.commit()
        await db.refresh(workflow)
        return workflow
    except Exception as e:
        logger.exception("Failed to create workflow", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create workflow definition.")

@router.get("/{workflow_id}")
async def get_workflow(workflow_id: int, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Workflow).where(Workflow.id == workflow_id))
    wf = res.scalar_one_or_none()
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found.")
    return wf

@router.post("/{workflow_id}/run")
async def run_workflow(
    workflow_id: int,
    payload: WorkflowRunPayload,
    db: AsyncSession = Depends(get_db)
):
    # Verify workflow exists
    res = await db.execute(select(Workflow).where(Workflow.id == workflow_id))
    workflow = res.scalar_one_or_none()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found.")

    try:
        # 1. Create WorkflowRun log row
        run = WorkflowRun(
            workflow_id=workflow.id,
            status="pending",
            input_data={"query": payload.query}
        )
        db.add(run)
        await db.commit()
        await db.refresh(run)

        # 2. Trigger background worker execution
        from app.jobs.worker import execute_workflow_run
        execute_workflow_run.delay(run.id)
        
        logger.info("Enqueued workflow execution", run_id=run.id)
        return {
            "success": True,
            "workflow_run_id": run.id,
            "status": "pending"
        }
    except Exception as e:
        logger.exception("Failed to initiate workflow run", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to trigger workflow execution.")

@router.get("/runs/{run_id}")
async def get_workflow_run_status(run_id: int, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(WorkflowRun).where(WorkflowRun.id == run_id))
    run = res.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Workflow run not found.")
    
    # Fetch step logs
    steps_res = await db.execute(
        select(WorkflowStep).where(WorkflowStep.workflow_run_id == run.id).order_by(WorkflowStep.started_at)
    )
    steps = steps_res.scalars().all()
    
    return {
        "run": run,
        "steps": steps
    }

@router.post("/runs/{run_id}/resume")
async def resume_workflow_run(run_id: int, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(WorkflowRun).where(WorkflowRun.id == run_id))
    run = res.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Workflow run not found.")

    if run.status != "waiting_approval":
        raise HTTPException(status_code=400, detail="Workflow is not paused waiting for approval.")

    try:
        # Find the approval step and mark completed
        step_res = await db.execute(
            select(WorkflowStep)
            .where(WorkflowStep.workflow_run_id == run.id, WorkflowStep.status == "waiting_approval")
        )
        step = step_res.scalar_one_or_none()
        if step:
            step.status = "completed"
            step.output_data = {"approved": True, "output": "Approved by user"}
            step.completed_at = datetime.utcnow()
            
        run.status = "pending"
        await db.commit()

        # Trigger background task again to process next nodes
        from app.jobs.worker import execute_workflow_run
        execute_workflow_run.delay(run.id)
        
        return {"success": True, "message": "Workflow run resumed."}
    except Exception as e:
        logger.exception("Failed to resume workflow run", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to resume workflow.")

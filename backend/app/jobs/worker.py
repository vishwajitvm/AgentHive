from celery import Celery
import asyncio
from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.agents.orchestrator import orchestrator
from app.workflows.engine import workflow_executor
from app.logging.logger import get_logger

logger = get_logger(__name__)

celery_app = Celery("agenthive", broker=settings.redis_url, backend=settings.redis_url)

@celery_app.task(name="agenthive.ping")
def ping():
    return "pong"

async def _execute_agent_run_async(agent_run_id: int, query: str):
    async with AsyncSessionLocal() as db:
        from app.logs.models import AgentRun
        from sqlalchemy import select
        res = await db.execute(select(AgentRun).where(AgentRun.id == agent_run_id))
        agent_run = res.scalar_one_or_none()
        if not agent_run:
            logger.error("AgentRun not found inside Celery job", run_id=agent_run_id)
            return

        agent_run.status = "running"
        await db.commit()

        try:
            await orchestrator.execute_run(
                agent_id=agent_run.agent_id,
                query=query,
                db=db,
                workflow_run_id=agent_run.workflow_run_id
            )
        except Exception as e:
            logger.exception("Celery agent run task failed", run_id=agent_run_id)

async def _execute_workflow_run_async(workflow_run_id: int):
    async with AsyncSessionLocal() as db:
        try:
            await workflow_executor.execute_run(workflow_run_id, db)
        except Exception as e:
            logger.exception("Celery workflow run task failed", run_id=workflow_run_id)

@celery_app.task(name="agenthive.execute_agent_run")
def execute_agent_run(agent_run_id: int, query: str):
    logger.info("Starting background agent run task", run_id=agent_run_id)
    asyncio.run(_execute_agent_run_async(agent_run_id, query))

@celery_app.task(name="agenthive.execute_workflow_run")
def execute_workflow_run(workflow_run_id: int):
    logger.info("Starting background workflow run task", run_id=workflow_run_id)
    asyncio.run(_execute_workflow_run_async(workflow_run_id))

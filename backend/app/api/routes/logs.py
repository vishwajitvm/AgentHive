from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.logs.service import logs_service

router = APIRouter(prefix="/logs", tags=["logs"])

@router.get("/runs")
async def get_runs(
    agent_id: Optional[int] = None,
    status: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    return await logs_service.get_agent_runs(db, agent_id, status, limit, offset)

@router.get("/llm-calls")
async def get_llm_calls(
    agent_run_id: Optional[int] = None,
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    return await logs_service.get_llm_calls(db, agent_run_id, limit)

@router.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_db)):
    return await logs_service.get_system_stats(db)

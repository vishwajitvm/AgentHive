from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.agents.multi_agent import multi_agent_engine
from app.logging.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/orchestrate", tags=["orchestration"])

class MultiAgentRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="User prompt or task instruction")
    pattern: str = Field("router", description="Orchestration pattern: supervisor, swarm, router, auto")
    target_agents: Optional[List[str]] = Field(None, description="Optional list of candidate agent slugs or IDs")
    initial_agent: Optional[str] = Field(None, description="Starting agent slug for swarm pattern")
    use_parallel_llm: bool = Field(False, description="Enable speculative parallel LLM racing")
    max_handoffs: int = Field(5, description="Max handoff depth for swarm pattern")

class MultiAgentResponse(BaseModel):
    success: bool
    status: str
    pattern: str
    selected_agent: Optional[str] = None
    subtasks: Optional[List[Dict[str, Any]]] = None
    subagent_results: Optional[List[Dict[str, Any]]] = None
    handoff_chain: Optional[List[str]] = None
    response: str
    execution_time_seconds: float
    details: Optional[Dict[str, Any]] = None

@router.post("", response_model=MultiAgentResponse)
async def orchestrate_multi_agent(
    payload: MultiAgentRequest,
    db: AsyncSession = Depends(get_db)
):
    """Executes multi-agent dynamic orchestration across Supervisor, Swarm, or Router patterns."""
    logger.info("Received multi-agent orchestration request", pattern=payload.pattern, prompt=payload.prompt[:50])
    try:
        result = await multi_agent_engine.orchestrate(
            query=payload.prompt,
            db=db,
            pattern=payload.pattern,
            target_agents=payload.target_agents,
            initial_agent=payload.initial_agent,
            use_parallel_llm=payload.use_parallel_llm,
            max_handoffs=payload.max_handoffs
        )
        return MultiAgentResponse(
            success=result.get("success", True),
            status=result.get("status", "completed"),
            pattern=result.get("pattern", payload.pattern),
            selected_agent=result.get("selected_agent"),
            subtasks=result.get("subtasks"),
            subagent_results=result.get("subagent_results"),
            handoff_chain=result.get("handoff_chain"),
            response=result.get("response", ""),
            execution_time_seconds=result.get("execution_time_seconds", 0.0),
            details=result.get("details")
        )
    except Exception as e:
        logger.exception("Multi-agent orchestration endpoint error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Multi-agent orchestration failed: {str(e)}"
        )

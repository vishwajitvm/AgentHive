from sqlalchemy.ext.asyncio import AsyncSession
from app.agents.seeder import SPECIALIZED_AGENTS, initialize_agents as seeder_initialize_agents
from app.logging.logger import get_logger

logger = get_logger(__name__)

DEFAULT_AGENTS = SPECIALIZED_AGENTS

async def initialize_agents(db: AsyncSession):
    """Pre-populates/upserts the database with default specialized agent roles and prompt versions on startup."""
    await seeder_initialize_agents(db)

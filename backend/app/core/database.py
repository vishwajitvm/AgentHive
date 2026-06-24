from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from sqlalchemy import text
from app.core.config import settings
from app.logging.logger import get_logger

logger = get_logger(__name__)

# Create async engine for PostgreSQL connection
engine = create_async_engine(
    settings.database_url,
    echo=settings.app_debug,
    future=True,
)

# Async session maker
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

Base = declarative_base()

async def get_db():
    """Dependency generator for database sessions."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def init_db():
    """Initializes database extensions and creates all metadata tables."""
    try:
        async with engine.begin() as conn:
            # Enable pgvector extension before creating tables
            logger.info("Initializing pgvector database extension...")
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            
            # Import models to ensure they are registered on Base
            from app.core.models import User, Secret, AuditLog
            from app.agents.models import Agent, AgentVersion, Prompt, PromptVersion
            from app.llm.models import ModelProvider, ModelPolicy
            from app.workflows.models import Workflow, WorkflowRun, WorkflowStep
            from app.logs.models import AgentRun, AgentStep, LLMCall, ToolCall
            from app.memory.models import Memory
            from app.tools.models import Tool
            
            logger.info("Creating all database tables...")
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Database initialization completed successfully.")
    except Exception as e:
        logger.exception("Failed to initialize database", error=str(e))
        raise

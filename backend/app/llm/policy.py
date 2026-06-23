from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.llm.models import ModelPolicy
from app.core.config import settings
from app.logging.logger import get_logger

logger = get_logger(__name__)

async def get_active_policy(db: AsyncSession) -> ModelPolicy:
    """Retrieves the active routing policy or creates a default one if none exists."""
    try:
        result = await db.execute(select(ModelPolicy).where(ModelPolicy.is_active == True))
        policy = result.scalar_one_or_none()
        if policy:
            return policy

        # No active policy in DB, look for any policy
        result = await db.execute(select(ModelPolicy))
        policy = result.scalar_one_or_none()
        if policy:
            policy.is_active = True
            await db.commit()
            return policy

        # Create default policy using config settings
        logger.info("No LLM policy found in database. Creating default active policy.")
        default_policy = ModelPolicy(
            name="Default Fallback Policy",
            primary_provider=settings.default_primary_provider,
            secondary_provider=settings.default_secondary_provider,
            fallback_order=settings.default_fallback_order,
            max_input_tokens=settings.default_max_input_tokens,
            max_output_tokens=settings.default_max_output_tokens,
            timeout_seconds=settings.default_llm_timeout_seconds,
            retry_count=2,
            is_active=True,
        )
        db.add(default_policy)
        await db.commit()
        await db.refresh(default_policy)
        return default_policy
    except Exception as e:
        logger.exception("Failed to retrieve LLM policy. Returning system default overrides.", error=str(e))
        # Return a temporary non-db instance as fallback
        return ModelPolicy(
            name="System Config Fallback",
            primary_provider=settings.default_primary_provider,
            secondary_provider=settings.default_secondary_provider,
            fallback_order=settings.default_fallback_order,
            max_input_tokens=settings.default_max_input_tokens,
            max_output_tokens=settings.default_max_output_tokens,
            timeout_seconds=settings.default_llm_timeout_seconds,
            retry_count=2,
            is_active=True
        )

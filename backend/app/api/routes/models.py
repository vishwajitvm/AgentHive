from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.llm.models import ModelProvider, ModelPolicy
from app.core.models import Secret
from app.core.security import encrypt_secret
from app.logging.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/models", tags=["models"])

# Pydantic schemas
class ProviderPayload(BaseModel):
    provider_name: str
    provider_type: str
    base_url: Optional[str] = None
    default_model: str
    api_key: Optional[str] = None
    enabled: bool = True

class PolicyPayload(BaseModel):
    name: str
    primary_provider: str
    secondary_provider: str
    fallback_order: str
    max_input_tokens: int = 12000
    max_output_tokens: int = 2048
    timeout_seconds: int = 60
    retry_count: int = 2

@router.get("/providers")
async def list_providers(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ModelProvider).order_by(ModelProvider.provider_name))
    providers = result.scalars().all()
    # Mask secret references for safety
    serialized = []
    for prov in providers:
        item = dict(prov.__dict__)
        item.pop("_sa_instance_state", None)
        item["has_key"] = prov.api_key_secret_id is not None
        item.pop("api_key_secret_id", None)
        serialized.append(item)
    return serialized

@router.post("/providers")
async def configure_provider(payload: ProviderPayload, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(ModelProvider).where(ModelProvider.provider_type == payload.provider_type))
    provider = res.scalar_one_or_none()

    try:
        secret_id = None
        # Handle API key encryption if supplied
        if payload.api_key:
            enc_key = encrypt_secret(payload.api_key)
            secret = Secret(
                name=f"{payload.provider_type}_api_key",
                encrypted_value=enc_key
            )
            db.add(secret)
            await db.commit()
            await db.refresh(secret)
            secret_id = secret.id

        if provider:
            # Update existing provider
            provider.provider_name = payload.provider_name
            provider.base_url = payload.base_url
            provider.default_model = payload.default_model
            provider.enabled = payload.enabled
            if secret_id:
                provider.api_key_secret_id = secret_id
        else:
            # Create new provider record
            provider = ModelProvider(
                provider_name=payload.provider_name,
                provider_type=payload.provider_type,
                base_url=payload.base_url,
                default_model=payload.default_model,
                enabled=payload.enabled,
                api_key_secret_id=secret_id
            )
            db.add(provider)
        
        await db.commit()
        await db.refresh(provider)
        return {"success": True, "provider_id": provider.id}
    except Exception as e:
        logger.exception("Failed to configure provider", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to configure provider: {str(e)}")

@router.get("/policies")
async def list_policies(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ModelPolicy).order_by(ModelPolicy.name))
    return result.scalars().all()

@router.post("/policies")
async def create_policy(payload: PolicyPayload, db: AsyncSession = Depends(get_db)):
    try:
        policy = ModelPolicy(
            name=payload.name,
            primary_provider=payload.primary_provider,
            secondary_provider=payload.secondary_provider,
            fallback_order=payload.fallback_order,
            max_input_tokens=payload.max_input_tokens,
            max_output_tokens=payload.max_output_tokens,
            timeout_seconds=payload.timeout_seconds,
            retry_count=payload.retry_count,
            is_active=False
        )
        db.add(policy)
        await db.commit()
        await db.refresh(policy)
        return policy
    except Exception as e:
        logger.exception("Failed to create policy", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to create policy: {str(e)}")

@router.put("/policies/{policy_id}/activate")
async def activate_policy(policy_id: int, db: AsyncSession = Depends(get_db)):
    # Verify policy exists
    res = await db.execute(select(ModelPolicy).where(ModelPolicy.id == policy_id))
    policy = res.scalar_one_or_none()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found.")

    try:
        # Mark all policies inactive
        await db.execute(update(ModelPolicy).values(is_active=False))
        # Mark target policy active
        policy.is_active = True
        await db.commit()
        return {"success": True, "activated_policy_id": policy.id}
    except Exception as e:
        logger.exception("Failed to activate policy", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to activate policy: {str(e)}")

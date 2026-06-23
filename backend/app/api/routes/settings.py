from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, Any, List
from pydantic import BaseModel

from app.core.database import get_db
from app.core.models import Secret
from app.core.security import encrypt_secret
from app.core.config import settings
from app.logging.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/settings", tags=["settings"])

class EnvKeyPayload(BaseModel):
    key: str
    value: str

@router.get("/env")
async def get_env_settings(db: AsyncSession = Depends(get_db)):
    """Returns lists of configured keys and system variables."""
    # Fetch all stored secrets
    res = await db.execute(select(Secret.name))
    secrets_list = res.scalars().all()
    
    # Mask values
    environment_variables = {
        "GEMINI_API_KEY": "****" if "gemini_api_key" in secrets_list or settings.gemini_api_key else "",
        "OPENAI_API_KEY": "****" if "openai_api_key" in secrets_list or settings.openai_api_key else "",
        "HUGGINGFACE_API_KEY": "****" if "huggingface_api_key" in secrets_list or settings.huggingface_api_key else "",
        "GROQ_API_KEY": "****" if "groq_api_key" in secrets_list or settings.groq_api_key else "",
        "OLLAMA_BASE_URL": settings.ollama_base_url,
        "DEFAULT_PRIMARY_PROVIDER": settings.default_primary_provider,
        "DEFAULT_SECONDARY_PROVIDER": settings.default_secondary_provider,
        "LOG_LEVEL": settings.log_level
    }
    return environment_variables

@router.post("/env")
async def save_env_setting(payload: EnvKeyPayload, db: AsyncSession = Depends(get_db)):
    """Encrypts and stores a sensitive key in the secrets database table."""
    key_name = payload.key.upper()
    if not payload.value:
        raise HTTPException(status_code=400, detail="Value cannot be empty.")

    try:
        enc_val = encrypt_secret(payload.value)
        # Check if already exists
        res = await db.execute(select(Secret).where(Secret.name == key_name.lower()))
        secret = res.scalar_one_or_none()
        
        if secret:
            secret.encrypted_value = enc_val
        else:
            secret = Secret(
                name=key_name.lower(),
                encrypted_value=enc_val
            )
            db.add(secret)
            
        await db.commit()
        logger.info("Saved environment variable secret reference", key=key_name)
        return {"success": True, "message": f"Successfully updated environment setting for '{key_name}'."}
    except Exception as e:
        logger.exception("Failed to save environment secret", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to save setting: {str(e)}")

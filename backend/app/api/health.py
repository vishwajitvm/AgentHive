from fastapi import APIRouter
from app.core.config import settings

router = APIRouter(tags=["health"])

@router.get("/health")
async def health():
    return {
        "service": settings.project_name,
        "status": "ok",
        "env": settings.app_env,
        "version": "0.1.0"
    }

@router.get("/ready")
async def ready():
    # TODO: add database, Redis, MinIO, Ollama health checks.
    return {
        "status": "ready-check-placeholder",
        "database": "pending",
        "redis": "pending",
        "ollama": "pending"
    }

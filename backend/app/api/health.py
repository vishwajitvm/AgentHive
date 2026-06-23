from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import redis.asyncio as aioredis
import httpx

from app.core.config import settings
from app.core.database import get_db
from app.logging.logger import get_logger

logger = get_logger(__name__)
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
async def ready(db: AsyncSession = Depends(get_db)):
    db_status = "unhealthy"
    redis_status = "unhealthy"
    ollama_status = "unhealthy"
    minio_status = "unhealthy"

    # 1. Database check
    try:
        await db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        logger.error("Health check - Database query failed", error=str(e))

    # 2. Redis check
    try:
        r = aioredis.from_url(settings.redis_url)
        await r.ping()
        redis_status = "healthy"
        await r.close()
    except Exception as e:
        logger.error("Health check - Redis ping failed", error=str(e))

    # 3. Ollama check
    try:
        async with httpx.AsyncClient(timeout=3) as client:
            resp = await client.get(f"{settings.ollama_base_url}/")
            if resp.status_code in [200, 404, 405]: # Ollama base page or status is ok
                ollama_status = "healthy"
    except Exception as e:
        logger.error("Health check - Ollama connection failed", error=str(e))

    # 4. MinIO check
    try:
        # MinIO console or API ping
        async with httpx.AsyncClient(timeout=3) as client:
            resp = await client.get(f"http://{settings.minio_endpoint}/minio/health/live")
            if resp.status_code == 200:
                minio_status = "healthy"
            else:
                # Direct check if console address responds
                resp_console = await client.get(f"http://minio:9001/")
                if resp_console.status_code == 200:
                    minio_status = "healthy"
    except Exception as e:
        logger.error("Health check - MinIO check failed", error=str(e))

    is_ready = all(s == "healthy" for s in [db_status, redis_status, ollama_status, minio_status])

    return {
        "status": "ready" if is_ready else "degraded",
        "database": db_status,
        "redis": redis_status,
        "ollama": ollama_status,
        "minio": minio_status
    }

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.logging.logger import configure_logging, get_logger
from app.core.database import init_db
from app.agents.registry import initialize_agents
from app.core.exceptions import AgentHiveException, agenthive_exception_handler

# Import Routers
from app.api.health import router as health_router
from app.api.routes.agents import router as agents_router
from app.api.routes.models import router as models_router
from app.api.routes.workflows import router as workflows_router
from app.api.routes.logs import router as logs_router
from app.api.routes.settings import router as settings_router

import time
import uuid

configure_logging()
logger = get_logger(__name__)

app = FastAPI(title="AgentHive API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
app.add_exception_handler(AgentHiveException, agenthive_exception_handler)

@app.on_event("startup")
async def startup_event():
    logger.info("Initializing AgentHive database...")
    await init_db()
    
    logger.info("Pre-populating default agents...")
    from app.core.database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        await initialize_agents(db)
        
    logger.info("AgentHive API service has successfully started.")

@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
    start = time.perf_counter()
    try:
        response = await call_next(request)
        latency_ms = round((time.perf_counter() - start) * 1000, 2)
        logger.info(
            "api_request_completed",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            latency_ms=latency_ms,
        )
        response.headers["x-request-id"] = request_id
        return response
    except Exception as exc:
        latency_ms = round((time.perf_counter() - start) * 1000, 2)
        logger.exception(
            "api_request_failed",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            latency_ms=latency_ms,
            error=str(exc),
        )
        raise

# Register Routers
app.include_router(health_router)
app.include_router(agents_router, prefix="/api")
app.include_router(models_router, prefix="/api")
app.include_router(workflows_router, prefix="/api")
app.include_router(logs_router, prefix="/api")
app.include_router(settings_router, prefix="/api")

from fastapi import Request, status
from fastapi.responses import JSONResponse
from app.logging.logger import get_logger

logger = get_logger(__name__)

class AgentHiveException(Exception):
    """Base exception for all AgentHive errors."""
    def __init__(self, message: str, details: dict = None, status_code: int = 500):
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.status_code = status_code

class LLMRouteError(AgentHiveException):
    """Raised when the LLM Router fails to resolve a call after all fallbacks."""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, details, status_code=status.HTTP_502_BAD_GATEWAY)

class AgentRunError(AgentHiveException):
    """Raised when an agent run fails, loops, or times out."""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, details, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

class WorkflowValidationError(AgentHiveException):
    """Raised when a workflow DAG contains errors or cycles."""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, details, status_code=status.HTTP_400_BAD_REQUEST)

class ToolExecutionError(AgentHiveException):
    """Raised when a tool fails to execute or access unauthorized boundaries."""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, details, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)

async def agenthive_exception_handler(request: Request, exc: AgentHiveException) -> JSONResponse:
    """Global handler for structured AgentHive exceptions."""
    logger.error(
        "agenthive_error_occurred",
        path=request.url.path,
        message=exc.message,
        details=exc.details,
        status_code=exc.status_code,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.__class__.__name__,
            "message": exc.message,
            "details": exc.details,
            "success": False
        }
    )

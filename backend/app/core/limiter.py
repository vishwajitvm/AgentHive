from slowapi import Limiter
from slowapi.util import get_remote_address
from app.core.config import settings

# Initialize rate limiter
# It uses Redis for distributed rate limiting if configured
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=settings.redis_url,
    default_limits=["100/minute"]
)

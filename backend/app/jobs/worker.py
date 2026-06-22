from celery import Celery
from app.core.config import settings

celery_app = Celery("agenthive", broker=settings.redis_url, backend=settings.redis_url)

@celery_app.task(name="agenthive.ping")
def ping():
    return "pong"

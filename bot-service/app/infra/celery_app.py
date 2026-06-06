from celery import Celery

from app.core.config import settings


celery_app = Celery(
    "bot_service",
    broker=settings.rabbitmq_url,
    backend=settings.redis_url,
    include=[
        "app.tasks.llm_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    result_expires=3600,
)

# Явный импорт нужен, чтобы задача llm_request была зарегистрирована
# и Celery не падал с KeyError при вызове по имени.
import app.tasks.llm_tasks  # noqa: E402,F401

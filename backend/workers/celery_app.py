# backend/workers/celery_app.py
from celery import Celery
from core.config import settings

celery_app = Celery(
    "ai_assignment",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["workers.tasks"],
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
    task_routes={
        "workers.tasks.process_assignment": {"queue": "assignments"},
        "workers.tasks.process_notebook": {"queue": "notebooks"},
    },
)

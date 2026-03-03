"""Celery application configuration."""

import os

from celery import Celery

celery_app = Celery("ai_real_estate")

celery_app.conf.update(
    broker_url=os.getenv("CELERY_BROKER_URL", "redis://redis:6379/1"),
    result_backend=os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/2"),
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)

celery_app.autodiscover_tasks(["app.tasks"])

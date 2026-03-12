from celery import Celery
from worker.config import get_settings

settings = get_settings()

celery = Celery(
    "voicegen",
    broker=settings.broker_url,
    backend=settings.result_backend,
    include=["worker.tasks"],
)

celery.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    # Use the same default queue as GeminiBApiServer
    task_default_queue="celery",
)

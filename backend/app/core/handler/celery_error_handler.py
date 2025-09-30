# app/core/celery_error_handler.py

from celery import Celery

from app.core.logging import get_logger

logger = get_logger(__name__)


def setup_celery_exception_handlers(app: Celery):
    pass


def pipeline_error_handler(stage_num: int, max_retries: int = 3, retry_delay: int = 60):
    pass

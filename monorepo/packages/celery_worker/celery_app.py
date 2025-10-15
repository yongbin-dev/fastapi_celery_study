"""
ML Server Celery Application
ML 관련 Celery 태스크 설정
"""

import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from celery import Celery
from shared.config import settings

# Celery 앱 생성
celery_app = Celery(
    "ml_server",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["ml_server.app.tasks"],  # ML 태스크 모듈
)

# Celery 설정
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Seoul",
    enable_utc=True,
    result_expires=3600,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
)

# Convenience alias
app = celery_app

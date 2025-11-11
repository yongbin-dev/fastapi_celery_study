"""
ML Server Celery Application
ML 관련 Celery 태스크 설정
"""

import os
import time

from celery import Celery
from shared import get_logger
from shared.config import settings

# 프로젝트 루트를 sys.path에 추가
# project_root = Path(__file__).parent.parent
# sys.path.insert(0, str(project_root))

logger = get_logger(__name__)

# Celery 앱 생성
celery_app = Celery(
    "celery_worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "tasks.pipeline_tasks",  # 파이프라인 태스크 모듈
        "tasks.batch_tasks",  # 배치 태스크 모듈
    ],
)

# Celery 설정
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Seoul",
    enable_utc=True,
    result_expires=3600,
    worker_prefetch_multiplier=settings.CELERY_WORKER_PREFETCH_MULTIPLIER,
    worker_max_tasks_per_child=settings.CELERY_WORKER_MAX_TASKS_PER_CHILD,
    task_acks_late=True,
)

logger.info(
    f"🔧 Celery prefetch_multiplier: {settings.CELERY_WORKER_PREFETCH_MULTIPLIER}"
)
logger.info(
    f"🔧 Celery max_tasks_per_child: {settings.CELERY_WORKER_MAX_TASKS_PER_CHILD}"
)


# 타임존을 서울로 설정
os.environ["TZ"] = "Asia/Seoul"
try:
    time.tzset()  # Unix/Linux에서 타임존 설정 적용
    logger.info("🕐 Celery 타임존 설정: Asia/Seoul")
except AttributeError:
    # Windows에서는 tzset이 없음
    logger.info("🕐 Celery 타임존 설정: Asia/Seoul (Windows 환경)")


# Celery signals 등록
try:
    from core import celery_signals  # noqa: F401

    logger.info("✅ Celery signals 모듈 import 성공!")
except ImportError as e:
    logger.error(f"❌ Celery signals import 실패: {e}")

# Convenience alias
app = celery_app

"""
ML Server Celery Application
ML 관련 Celery 태스크 설정
"""

import sys
from pathlib import Path

from celery import Celery
from shared import get_logger
from shared.config import settings

# 프로젝트 루트를 sys.path에 추가
# project_root = Path(__file__).parent.parent
# sys.path.insert(0, str(project_root))

logger = get_logger(__name__)

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


# 타임존을 서울로 설정
# os.environ["TZ"] = "Asia/Seoul"
# try:
#     time.tzset()  # Unix/Linux에서 타임존 설정 적용
#     logger.info("🕐 Celery 타임존 설정: Asia/Seoul")
# except AttributeError:
#     # Windows에서는 tzset이 없음
#     logger.info("🕐 Celery 타임존 설정: Asia/Seoul (Windows 환경)")


# Celery signals 등록
try:
    from .core import celery_signals

    __all__ = ["celery_app", "celery_signals"]
    logger.info("✅ Celery signals 모듈 import 성공!")
except ImportError as e:
    logger.error(f"❌ Celery signals import 실패: {e}")

# Convenience alias
app = celery_app

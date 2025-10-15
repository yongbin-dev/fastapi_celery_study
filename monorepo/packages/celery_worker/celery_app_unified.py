# celery_app_unified.py
# 통합 Celery 애플리케이션 (API Server + ML Server 태스크)

import os
import sys
import time
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from celery import Celery
from shared.config.settings import settings
from shared.core.logging import get_logger

# 공통 로깅 시스템 사용
logger = get_logger(__name__)

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
    from core.celery import celery_signals

    __all__ = ["celery_app", "celery_signals"]
    logger.info("✅ Celery signals 모듈 import 성공!")
except ImportError as e:
    logger.error(f"❌ Celery signals import 실패: {e}")


def setup_celery_logging():
    """Celery가 공통 로깅 시스템을 사용하도록 설정"""
    import logging

    celery_loggers = [
        "celery",
        "celery.worker",
        "celery.task",
        "celery.beat",
        "celery.app",
        "celery.redirected",
    ]

    for logger_name in celery_loggers:
        celery_logger = logging.getLogger(logger_name)
        celery_logger.propagate = True
        celery_logger.setLevel(logging.INFO)

    logger.info("✅ Celery 로깅이 공통 로깅 시스템과 통합됨")


# 로그 설정 실행
setup_celery_logging()

# Celery 인스턴스 생성
celery_app = Celery(
    "fastapi_celery_monorepo",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "tasks.pipeline_tasks",  # Pipeline tasks
        # ML Server tasks can be added here
    ],
)

# Celery 설정
celery_app.conf.update(
    # 태스크 직렬화
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Seoul",
    enable_utc=True,
    # 결과 백엔드 설정
    result_expires=3600,  # 1시간 후 결과 만료
    # 워커 설정
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    # 로깅 설정
    worker_log_format="%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s",
    worker_task_log_format="%(asctime)s | %(levelname)-8s | %(name)s | [%(task_name)s(%(task_id)s)] | %(message)s",
    worker_hijack_root_logger=False,
    worker_log_color=False,
    worker_redirect_stdouts=True,
    worker_redirect_stdouts_level="INFO",
)

# Convenience alias
app = celery_app

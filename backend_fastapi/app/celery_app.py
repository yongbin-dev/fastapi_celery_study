# app/core/celery_app.py

import os
import time
from celery import Celery
from app.config import settings
from app.core.logging import get_logger

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
# 이 파일을 임포트하는 시점에 시그널 핸들러가 등록되도록 최상단으로 이동
try:
    from app.core.celery import celery_signals

    logger.info("✅ Celery signals 모듈 import 성공!")
except ImportError as e:
    logger.error(f"❌ Celery signals import 실패: {e}")


def setup_celery_logging():
    """Celery가 공통 로깅 시스템을 사용하도록 설정"""
    import logging

    # Celery 관련 로거들이 공통 로깅 시스템을 사용하도록 설정
    # 이미 app.core.logging에서 celery 로거가 설정되어 있으므로
    # 추가 핸들러를 붙이지 않고 레벨만 조정

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
        # 핸들러는 루트 로거에서 상속받아 사용
        celery_logger.propagate = True
        celery_logger.setLevel(logging.INFO)

    logger.info("✅ Celery 로깅이 공통 로깅 시스템과 통합됨")


# 로그 설정 실행
setup_celery_logging()


# Celery 인스턴스 생성
celery_app = Celery(
    "celery_study",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=settings.CELERY_TASK_MODULES,  # 설정에서 태스크 모듈들을 동적으로 가져옴
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
    # 워커 설정 - 멀티프로세싱 사용 (기본: prefork)
    # worker_pool="solo",  # 단일 프로세스만 사용하려면 주석 해제
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    # 재시도 설정
    task_reject_on_worker_lost=True,
    # 로깅 설정 - 공통 로깅 시스템과 통합
    worker_log_format="%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s",
    worker_task_log_format="%(asctime)s | %(levelname)-8s | %(name)s | [%(task_name)s(%(task_id)s)] | %(message)s",
    worker_hijack_root_logger=False,  # 루트 로거를 hijack하지 않고 공통 시스템 사용
    # 워커 프로세스 정보 로깅 - 공통 시스템과 일치하도록 설정
    worker_log_color=False,  # 컬러는 공통 시스템에서 처리
    worker_redirect_stdouts=True,  # stdout/stderr을 로그로 리다이렉트
    worker_redirect_stdouts_level="INFO",
)

# # 태스크 자동 발견 - 설정된 모듈들과 추가 패키지들에서 자동 발견
# celery_app.autodiscover_tasks(settings.CELERY_TASK_MODULES + ['app'])


# Queue stats를 위한 태스크 등록
from app.core.celery.celery_signals import collect_queue_stats

celery_app.task(name="app.core.celery.celery_signals.collect_queue_stats")(
    collect_queue_stats
)

# Celery Beat 스케줄 설정
celery_app.conf.beat_schedule = {
    "collect-queue-stats": {
        "task": "app.core.celery.celery_signals.collect_queue_stats",
        "schedule": 60.0,  # 1분마다
    },
}

# Convenience alias for backward compatibility
app = celery_app

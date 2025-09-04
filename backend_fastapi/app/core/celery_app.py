# app/core/celery_app.py

import logging
import os
from celery import Celery
from .config import settings

# Celery 로그 설정
def setup_celery_logging():
    """Celery 로그를 날짜별 파일로 저장하도록 설정"""
    from datetime import datetime
    from logging.handlers import TimedRotatingFileHandler
    
    logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs")
    os.makedirs(logs_dir, exist_ok=True)
    
    # 현재 날짜
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    # 포맷터 설정
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Celery 로거 설정
    celery_logger = logging.getLogger('celery')
    celery_logger.setLevel(logging.INFO)
    
    # 일별 로테이션 파일 핸들러
    celery_handler = TimedRotatingFileHandler(
        os.path.join(logs_dir, f'celery_{current_date}.log'),
        when='midnight',
        interval=1,
        backupCount=30,  # 30일치 로그 보관
        encoding='utf-8'
    )
    celery_handler.setLevel(logging.INFO)
    celery_handler.setFormatter(formatter)
    celery_handler.suffix = "%Y-%m-%d"
    
    # 기존 핸들러 제거 후 새 핸들러 추가
    celery_logger.handlers.clear()
    celery_logger.addHandler(celery_handler)
    
    # 워커 로거 설정
    worker_logger = logging.getLogger('celery.worker')
    worker_handler = TimedRotatingFileHandler(
        os.path.join(logs_dir, f'celery_worker_{current_date}.log'),
        when='midnight',
        interval=1,
        backupCount=30,
        encoding='utf-8'
    )
    worker_handler.setLevel(logging.INFO)
    worker_handler.setFormatter(formatter)
    worker_handler.suffix = "%Y-%m-%d"
    worker_logger.handlers.clear()
    worker_logger.addHandler(worker_handler)
    
    # 태스크 로거 설정
    task_logger = logging.getLogger('celery.task')
    task_handler = TimedRotatingFileHandler(
        os.path.join(logs_dir, f'celery_tasks_{current_date}.log'),
        when='midnight',
        interval=1,
        backupCount=30,
        encoding='utf-8'
    )
    task_handler.setLevel(logging.INFO)
    task_handler.setFormatter(formatter)
    task_handler.suffix = "%Y-%m-%d"
    task_logger.handlers.clear()
    task_logger.addHandler(task_handler)
    
    print(f"✅ Celery 날짜별 로그 파일 설정 완료: {logs_dir}")
    print(f"   - celery_{current_date}.log")
    print(f"   - celery_worker_{current_date}.log")
    print(f"   - celery_tasks_{current_date}.log")

# 로그 설정 실행
setup_celery_logging()


# Celery 인스턴스 생성
celery_app = Celery(
    "study",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks"] , # 태스크 모듈들

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
    
    # 워커 설정 - macOS 호환성을 위해 멀티프로세싱 대신 solo pool 사용
    worker_pool="solo",  # macOS fork() 문제 해결
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    
    # 재시도 설정
    task_reject_on_worker_lost=True,
    
    # 로깅 설정 - 파일로 로그 저장
    worker_log_format="[%(asctime)s: %(levelname)s/%(processName)s] %(message)s",
    worker_task_log_format="[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s",
    worker_hijack_root_logger=False,  # 루트 로거를 hijack하지 않음
)

# 태스크 자동 발견 (선택사항)
celery_app.autodiscover_tasks()

# Celery signals 등록 - 반드시 celery_app 생성 후에!
try:
    from . import celery_signals
    print("✅ Celery signals 모듈 import 성공!")
except Exception as e:
    print(f"❌ Celery signals import 실패: {e}")

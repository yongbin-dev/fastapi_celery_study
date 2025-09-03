# app/core/celery_app.py

from celery import Celery
from .config import settings


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
)

# 태스크 자동 발견 (선택사항)
celery_app.autodiscover_tasks()

# Celery signals 등록 - 반드시 celery_app 생성 후에!
try:
    from . import celery_signals
    print("✅ Celery signals 모듈 import 성공!")
except Exception as e:
    print(f"❌ Celery signals import 실패: {e}")

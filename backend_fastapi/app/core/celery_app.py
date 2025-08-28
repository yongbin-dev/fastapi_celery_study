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
    timezone="UTC",
    enable_utc=True,
    
    # 결과 백엔드 설정
    result_expires=3600,  # 1시간 후 결과 만료
    
    # 워커 설정
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    
    # 재시도 설정
    task_reject_on_worker_lost=True,
)

# 태스크 자동 발견 (선택사항)
celery_app.autodiscover_tasks()
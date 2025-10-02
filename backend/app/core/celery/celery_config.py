"""
Celery 설정
도메인별 큐 라우팅 및 워커 설정
"""

from kombu import Queue

# ==================== 큐 정의 ====================
task_queues = (
    Queue("default", routing_key="default"),
    Queue("ocr", routing_key="ocr.*"),  # OCR 전용 큐
    Queue("llm", routing_key="llm.*"),  # LLM 전용 큐
    Queue("vision", routing_key="vision.*"),  # Vision 전용 큐
    Queue("orchestration", routing_key="orchestration.*"),  # 오케스트레이션 큐
)

# ==================== 태스크 라우팅 ====================
task_routes = {
    # OCR 도메인 태스크 → ocr 큐
    "ocr.*": {"queue": "ocr", "routing_key": "ocr.task"},

    # LLM 도메인 태스크 → llm 큐
    "llm.*": {"queue": "llm", "routing_key": "llm.task"},

    # Vision 도메인 태스크 → vision 큐
    "vision.*": {"queue": "vision", "routing_key": "vision.task"},

    # 오케스트레이션 태스크 → orchestration 큐 (base 컨테이너)
    "chain.*": {"queue": "orchestration", "routing_key": "orchestration.task"},
    "orchestration.*": {"queue": "orchestration", "routing_key": "orchestration.task"},

    # 기타 태스크 → default 큐
    "*": {"queue": "default", "routing_key": "default"},
}

# ==================== Celery 설정 ====================
celery_config = {
    "task_queues": task_queues,
    "task_routes": task_routes,
    "task_default_queue": "default",
    "task_default_routing_key": "default",
    "task_acks_late": True,  # 태스크 완료 후 ACK
    "worker_prefetch_multiplier": 1,  # 한 번에 하나씩 처리
    "task_track_started": True,  # 태스크 시작 추적
    "result_expires": 3600,  # 결과 1시간 보관
}

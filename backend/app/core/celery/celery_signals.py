# celery_signals.py - 간소화된 버전 (데코레이터 사용으로 대부분 기능 제거)

from celery.signals import (
    worker_ready,
    worker_shutdown,
    heartbeat_sent,
)

from app.core.logging import get_logger

# 로거 설정
logger = get_logger(__name__)


def get_worker_name(sender=None):
    """안전하게 워커 이름 가져오기"""
    if sender and hasattr(sender, "hostname"):
        return sender.hostname
    elif sender and hasattr(sender, "consumer") and hasattr(sender.consumer, "hostname"):
        return sender.consumer.hostname
    elif sender and hasattr(sender, "request") and hasattr(sender.request, "hostname"):
        return sender.request.hostname
    else:
        import socket
        return f"celery@{socket.gethostname()}"


# 워커 관련 신호 처리 (필수 신호만 유지)

@worker_ready.connect
def worker_ready_handler(sender=None, **kwargs):
    """워커 준비 완료 처리"""
    worker_name = get_worker_name(sender)
    logger.info(f"🟢 SIGNAL: worker_ready 수신 - worker: {worker_name}")


@worker_shutdown.connect
def worker_shutdown_handler(sender=None, **kwargs):
    """워커 종료 처리"""
    worker_name = get_worker_name(sender)
    logger.info(f"🔴 SIGNAL: worker_shutdown 수신 - worker: {worker_name}")


@heartbeat_sent.connect
def heartbeat_handler(sender=None, **kwargs):
    """하트비트 처리"""
    # 하트비트는 너무 자주 발생하므로 로깅하지 않음
    pass


# 노트: TaskLog 및 ChainExecution 관련 처리는 모두 @task_logger 데코레이터에서 처리합니다.
# 이제 signals는 워커 상태 모니터링 용도로만 사용됩니다.
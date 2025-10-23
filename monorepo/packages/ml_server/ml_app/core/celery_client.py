"""
Celery 클라이언트
ml_server에서 celery_worker의 태스크를 호출하기 위한 클라이언트
"""

from typing import Optional

from celery import Celery
from shared.config import settings
from shared.core.logging import get_logger

logger = get_logger(__name__)


class CeleryClient:
    """Celery 태스크 클라이언트"""

    def __init__(
        self, broker_url: Optional[str] = None, backend_url: Optional[str] = None
    ):
        """
        Args:
            broker_url: Celery 브로커 URL (기본값: settings.REDIS_URL)
            backend_url: Celery 백엔드 URL (기본값: settings.REDIS_URL)
        """
        self.broker_url = broker_url or settings.REDIS_URL
        self.backend_url = backend_url or settings.REDIS_URL

        # Celery 앱 생성 (worker가 아닌 client 모드)
        self.celery_app = Celery(
            "ml_server_client",
            broker=self.broker_url,
            backend=self.backend_url,
        )

        # 설정
        self.celery_app.conf.update(
            task_serializer="json",
            accept_content=["json"],
            result_serializer="json",
            timezone="Asia/Seoul",
            enable_utc=True,
        )

        logger.info(f"✅ Celery 클라이언트 생성: broker={self.broker_url}")

    def send_task(self, task_name: str, **kwargs):
        """
        Celery 태스크 전송

        Args:
            task_name: 태스크 이름 (예: "tasks.ocr_extract")
            **kwargs: 태스크 인자

        Returns:
            AsyncResult 객체
        """
        logger.info(f"📤 Celery 태스크 전송: {task_name}")
        return self.celery_app.send_task(task_name, kwargs=kwargs)


# 싱글톤 인스턴스
_celery_client: Optional[CeleryClient] = None


def get_celery_client() -> CeleryClient:
    """Celery 클라이언트 싱글톤 인스턴스 반환"""
    global _celery_client
    if _celery_client is None:
        _celery_client = CeleryClient()
    return _celery_client

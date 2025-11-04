# packages/celery_worker/tasks/grpc_clients/ocr_client.py
"""OCR gRPC 클라이언트"""

from typing import Optional

import grpc
from shared.config import settings
from shared.core.logging import get_logger
from shared.grpc.generated import ocr_pb2, ocr_pb2_grpc

logger = get_logger(__name__)


class OCRGrpcClient:
    """OCR gRPC 클라이언트"""

    def __init__(self, server_address: Optional[str] = None):
        self.server_address = server_address or getattr(
            settings, 'ML_SERVER_GRPC_ADDRESS', 'localhost:50051'
        )
        self._channel: Optional[grpc.aio.Channel] = None
        self._stub: Optional[ocr_pb2_grpc.OCRServiceStub] = None

    async def __aenter__(self):
        """컨텍스트 매니저 진입"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """컨텍스트 매니저 종료"""
        await self.close()

    async def connect(self):
        """채널 연결"""
        if self._channel is None:
            self._channel = grpc.aio.insecure_channel(
                self.server_address,
                options=[
                    ('grpc.max_send_message_length', 100 * 1024 * 1024),
                    ('grpc.max_receive_message_length', 100 * 1024 * 1024),
                    ('grpc.keepalive_time_ms', 10000),
                ]
            )
            self._stub = ocr_pb2_grpc.OCRServiceStub(self._channel)
            logger.info(f"gRPC 채널 연결: {self.server_address}")

    async def close(self):
        """채널 종료"""
        if self._channel:
            await self._channel.close()
            self._channel = None
            self._stub = None
            logger.info("gRPC 채널 종료")

    async def extract_text(
        self,
        public_image_path: str,
        private_image_path: str,
        language: str = "korean",
        confidence_threshold: float = 0.5,
        use_angle_cls: bool = True,
        timeout: float = 300.0
    ) -> ocr_pb2.OCRResponse:
        """OCR 텍스트 추출

        Args:
            public_image_path: 공개 이미지 경로
            private_image_path: 비공개 이미지 경로
            language: 언어
            confidence_threshold: 신뢰도 임계값
            use_angle_cls: 각도 분류 사용 여부
            timeout: 타임아웃 (초)

        Returns:
            OCR 응답

        Raises:
            grpc.RpcError: gRPC 통신 오류
        """
        if not self._stub:
            await self.connect()

        if self._stub is None:
            raise Exception("_stub is None")

        # 요청 생성
        request = ocr_pb2.OCRRequest(
            public_image_path=public_image_path,
            private_image_path=private_image_path,
            language=language,
            confidence_threshold=confidence_threshold,
            use_angle_cls=use_angle_cls
        )

        # gRPC 호출
        try:
            response = await self._stub.ExtractText(
                request,
                timeout=timeout
            )

            logger.info(
                f"gRPC OCR 완료: {len(response.text_boxes)} 텍스트 박스, "
                f"신뢰도: {response.overall_confidence:.2f}"
            )

            return response

        except grpc.RpcError as e:
            logger.error(f"gRPC 오류: {e.code()}, {e.details()}")
            raise

    async def check_health(self) -> ocr_pb2.HealthCheckResponse:
        """헬스 체크

        Returns:
            헬스 체크 응답
        """
        if not self._stub :
            await self.connect()

        if self._stub is None:
            raise Exception("_stub is None")

        request = ocr_pb2.HealthCheckRequest(service_name="OCRService")
        return await self._stub.CheckHealth(request)


# 싱글톤 인스턴스
_grpc_client: Optional[OCRGrpcClient] = None


def get_ocr_grpc_client() -> OCRGrpcClient:
    """OCR gRPC 클라이언트 가져오기 (싱글톤)"""
    global _grpc_client
    if _grpc_client is None:
        _grpc_client = OCRGrpcClient()
    return _grpc_client

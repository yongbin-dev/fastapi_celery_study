import json
from typing import Callable

from fastapi import Request, Response
from starlette.background import BackgroundTask
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from shared.core.logging import get_logger

logger = get_logger(__name__)


class ResponseLogMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            response = await call_next(request)

            # 응답 본문을 읽기 위한 준비
            response_body = b""
            async for chunk in response.body_iterator:
                response_body += chunk

            # 로그 메시지 생성 및 전송을 백그라운드 작업으로 처리
            task = BackgroundTask(self.log_response, response, response_body)

            return Response(
                content=response_body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
                background=task,
            )
        except Exception as e:
            logger.error(f"ResponseLogMiddleware 에러: {e}")
            raise e from None

    async def log_response(self, response: Response, response_body: bytes):
        """응답 정보를 로깅하는 함수"""
        log_message = f"Response | Status: {response.status_code}"

        # 응답 본문 로깅
        body_str = ""
        if response_body:
            # content-type이 json이면 예쁘게 출력, 아니면 텍스트로 처리
            if "application/json" in response.headers.get("content-type", ""):
                try:
                    body_json = json.loads(response_body.decode("utf-8"))
                    body_str = json.dumps(body_json, ensure_ascii=False, indent=2)
                except json.JSONDecodeError:
                    body_str = response_body.decode("utf-8", errors="ignore")
            else:
                body_str = response_body.decode("utf-8", errors="ignore")

            # 로그가 너무 길어지는 것을 방지하기 위해 500자로 제한
            log_message += f"\n--- Response Body ---\n{body_str[:300]}"
            if len(body_str) > 500:
                log_message += "\n... (truncated)"

        logger.info(log_message)

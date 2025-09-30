import json
import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import get_logger

logger = get_logger(__name__)


class ResponseLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()

        # call_next 호출하여 response 얻기
        response = await call_next(request)

        duration = time.time() - start_time

        # Response body 읽기
        response_body = b""
        if hasattr(response, "body"):
            # 일반 Response의 경우
            response_body = response.body
        elif hasattr(response, "body_iterator"):
            # StreamingResponse의 경우
            chunks = []
            async for chunk in response.body_iterator:
                chunks.append(chunk)
            response_body = b"".join(chunks)

        # Response body를 문자열로 변환하여 로깅
        response_log = None
        if response_body:
            try:
                response_text = response_body.decode("utf-8")
                # JSON인 경우 파싱해서 로깅
                content_type = response.headers.get("content-type", "")
                if "application/json" in content_type:
                    response_data = json.loads(response_text)
                    response_log = json.dumps(response_data, ensure_ascii=False)[:500]
                else:
                    response_log = response_text[:500]
            except Exception:
                response_log = f"[binary data: {len(response_body)} bytes]"

        # 로그 메시지 생성
        log_msg = (
            f"{request.method} {request.url.path} | "
            f"Status: {response.status_code} | "
            f"Duration: {duration * 1000:.2f}ms"
        )

        if response_log:
            log_msg += f" | Response: {response_log}"

        logger.info(log_msg)

        # Response 반환 (body 재구성)
        if response_body:
            return Response(
                content=response_body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
            )

        return response

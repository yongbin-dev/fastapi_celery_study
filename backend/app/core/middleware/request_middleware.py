import json
import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import get_logger

logger = get_logger(__name__)


class RequestLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # 요청 정보
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "")

        # Request body 읽기 (POST, PUT 등)
        request_body = None
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if body:
                    request_body = json.loads(body.decode("utf-8"))

                    # body를 다시 읽을 수 있도록 설정
                    async def receive():
                        return {"type": "http.request", "body": body}

                    request._receive = receive
            except Exception:
                request_body = body.decode("utf-8")[:200] if body else None

        response = await call_next(request)

        duration = time.time() - start_time

        # 기본 로그
        log_msg = (
            f"{request.method} {request.url.path} | "
            f"Status: {response.status_code} | "
            f"Duration: {duration * 1000:.2f}ms | "
            f"IP: {client_ip} | "
            f"UA: {user_agent[:50]}"
        )

        # Request body가 있으면 추가
        if request_body:
            body_str = (
                json.dumps(request_body, ensure_ascii=False)[:200]
                if isinstance(request_body, dict)
                else str(request_body)[:200]
            )
            log_msg += f" | Request: {body_str}"

        logger.info(log_msg)

        return response

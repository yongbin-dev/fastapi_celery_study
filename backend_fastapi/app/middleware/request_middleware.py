import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from ..core.logging import get_logger

logger = get_logger(__name__)


class RequestLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # 요청 정보
        client_ip = request.client.host
        user_agent = request.headers.get("user-agent", "")

        response = await call_next(request)

        duration = time.time() - start_time

        logger.info(
            f"{request.method} {request.url.path} | "
            f"Status: {response.status_code} | "
            f"Duration: {duration * 1000:.2f}ms | "
            f"IP: {client_ip} | "
            f"UA: {user_agent[:50]}"
        )

        return response



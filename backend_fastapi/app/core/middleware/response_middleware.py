import json
import time

from fastapi import Request
from fastapi.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import get_logger

logger = get_logger(__name__)


class ResponseLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # Request body 읽기 (필요한 경우)
        # body = await request.body()

        response = await call_next(request)

        duration = time.time() - start_time

        # # Response body 읽기
        # response_body = b""
        # async for chunk in response.body_iterator:
        #     response_body += chunk

        # Response body를 문자열로 변환
        # try:
        #     response_text = response_body.decode("utf-8")
        #     # JSON인 경우 예쁘게 출력
        #     if response.headers.get("content-type") == "application/json":
        #         response_data = json.loads(response_text)
        #         response_log = json.dumps(response_data, ensure_ascii=False)[
        #             :200
        #         ]  # 200자 제한
        #     else:
        #         response_log = response_text[:200]  # 200자 제한
        # except:
        #     response_log = str(response_body)[:200]

        # logger.info(
        #     f"{request.method} {request.url.path} | "
        #     f"Status: {response.status_code} | "
        #     f"Duration: {duration * 1000:.2f}ms | "
        #     f"Response: {response_log}"
        # )

        # 새로운 Response 객체 생성해서 반환
        return Response(
            content=response,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type,
        )

from typing import Callable

from fastapi import Request, Response
from starlette.background import BackgroundTask
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from ..core.logging import get_logger

logger = get_logger(__name__)


class RequestLogMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 요청 본문을 읽기 위해 복사
        request_body = await request.body()

        # 백그라운드에서 로깅 작업을 수행하도록 태스크 생성
        log_task = BackgroundTask(self.log_request, request, request_body)

        # 응답 생성
        response = await call_next(request)
        response.background = log_task
        return response

    async def log_request(self, request: Request, request_body: bytes):
        """요청 정보를 로깅하는 함수"""
        log_message = f"Request | {request.method} {request.url}"
        logger.info(log_message)

        # 헤더 정보 로깅 (필요시 특정 헤더만 선택)
        # headers = dict(request.headers)
        # log_message += f"\n--- Headers ---\n{json.dumps(headers, indent=2)}"

        # # 요청 본문 로깅
        # body_str = ""
        # if request_body:
        #     # content-type에 따라 다르게 처리
        #     content_type = request.headers.get("content-type", "")
        #     if "application/json" in content_type:
        #         try:
        #             body_json = json.loads(request_body.decode("utf-8"))
        #             body_str = json.dumps(body_json, ensure_ascii=False, indent=2)
        #         except json.JSONDecodeError:
        #             body_str = request_body.decode("utf-8", errors="ignore")
        #     elif "multipart/form-data" in content_type:
        #         # 파일 업로드와 같은 multipart 요청은 본문 로깅에서 제외
        #         body_str = "(multipart/form-data content not logged)"
        #     else:
        #         body_str = request_body.decode("utf-8", errors="ignore")

        #     # 로그가 너무 길어지는 것을 방지하기 위해 500자로 제한
        #     log_message += f"\n--- Request Body ---\n{body_str[:500]}"
        #     if len(body_str) > 500:
        #         log_message += "\n... (truncated)"

        # logger.info(log_message)

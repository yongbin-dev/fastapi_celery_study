import json
import logging
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse
from ..core.config import settings
from ..utils.response_builder import ResponseBuilder

logger = logging.getLogger(__name__)


class CommonResponseMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.exclude_paths = settings.EXCLUDE_PATHS

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 제외 경로 체크
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)

        # API 경로만 처리
        if not request.url.path.startswith("/api/"):
            return await call_next(request)

        response = await call_next(request)

        # 에러 응답은 이미 처리됨 (에러 핸들러에서)
        if response.status_code >= 400:
            return response

        # 디버깅용 로그
        logger.info(f"Response type: {type(response)}")
        logger.info(f"Response status: {response.status_code}")

        try:
            # 응답 본문 읽기
            response_body = None

            # JSONResponse나 일반 Response 처리
            if hasattr(response, 'body'):
                if isinstance(response.body, bytes):
                    response_body = response.body.decode('utf-8')
                else:
                    # body_iterator가 있는 경우
                    body_parts = []
                    async for chunk in response.body_iterator:
                        body_parts.append(chunk)
                    response_body = b''.join(body_parts).decode('utf-8')

            if not response_body:
                logger.warning("응답 본문을 읽을 수 없습니다")
                return response

            logger.info(f"Original response body: {response_body}")

            # JSON 파싱
            try:
                original_data = json.loads(response_body)
            except json.JSONDecodeError:
                logger.warning("응답이 JSON 형식이 아닙니다")
                return response

            # 이미 공통 형식이면 그대로 반환
            if isinstance(original_data, dict) and "success" in original_data:
                logger.info("이미 공통 형식의 응답입니다")
                return JSONResponse(
                    content=original_data,
                    status_code=response.status_code,
                    headers=dict(response.headers)
                )

            # 공통 형식으로 변환
            formatted_response = ResponseBuilder.success(
                data=original_data,
                message="성공"
            )

            logger.info(f"Formatted response: {formatted_response}")

            return JSONResponse(
                content=formatted_response,
                status_code=response.status_code,
                headers=dict(response.headers)
            )

        except Exception as e:
            logger.error(f"응답 변환 중 오류 발생: {e}")
            import traceback
            logger.error(traceback.format_exc())

        return response
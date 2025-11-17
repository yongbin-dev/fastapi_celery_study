"""LLM 서버 통신 Client

OpenAI API를 통해 vLLM 서버와 통신하는 책임만 담당하는 클래스
"""

from typing import Any, Dict, Iterator, List, Optional

from openai import OpenAI
from openai.types.chat import ChatCompletion, ChatCompletionChunk
from shared.core.logging import get_logger

logger = get_logger(__name__)


class LLMClient:
    """vLLM 서버 통신 전담 클래스 (OpenAI API 호환)"""

    def __init__(
        self,
        server_url: str = "http://localhost:38000/v1",
        api_key: str = "EMPTY",
        timeout: float = 60.0,
    ):
        """LLMClient 초기화

        Args:
            server_url: vLLM 서버 URL (기본값: http://localhost:38000/v1)
            api_key: API 키 (vLLM은 "EMPTY" 사용)
            timeout: 요청 타임아웃 (초 단위, 기본값: 60.0)
        """
        self.server_url = server_url
        self.api_key = api_key
        self.timeout = timeout
        self.client = OpenAI(
            api_key=api_key,
            base_url=server_url,
            timeout=timeout,
        )
        logger.info(f"LLMClient 초기화 완료: {server_url}")

    async def get_available_models(self) -> List[str]:
        """사용 가능한 모델 목록 조회

        Returns:
            List[str]: 모델 ID 리스트

        Raises:
            Exception: 모델 조회 실패
        """
        try:
            models = self.client.models.list()
            model_ids = [model.id for model in models.data]
            logger.info(f"사용 가능한 모델: {model_ids}")
            return model_ids
        except Exception as e:
            logger.error(f"모델 목록 조회 실패: {str(e)}")
            raise

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs: Any,
    ) -> ChatCompletion | Iterator[ChatCompletionChunk]:
        """채팅 완성 요청

        Args:
            messages: 메시지 리스트 [{"role": "user", "content": "..."}, ...]
            model: 사용할 모델 ID (기본값: 첫 번째 사용 가능한 모델)
            temperature: 샘플링 온도 (0.0 ~ 2.0, 기본값: 0.7)
            max_tokens: 최대 생성 토큰 수 (기본값: None)
            stream: 스트리밍 응답 여부 (기본값: False)
            **kwargs: 추가 OpenAI API 파라미터

        Returns:
            ChatCompletion | Iterator[ChatCompletionChunk]: 완성 결과 또는 스트리밍 청크

        Raises:
            ValueError: 사용 가능한 모델이 없거나 메시지가 비어있음
            Exception: API 호출 실패
        """
        if not messages:
            raise ValueError("메시지가 비어있습니다")

        # 모델이 지정되지 않으면 첫 번째 모델 사용
        if model is None:
            available_models = await self.get_available_models()
            if not available_models:
                raise ValueError("사용 가능한 모델이 없습니다")
            model = available_models[0]
            logger.info(f"기본 모델 사용: {model}")

        try:
            logger.info(f"채팅 완성 요청 (모델: {model}, 스트리밍: {stream})")

            response = self.client.chat.completions.create(
                messages=messages,  # type: ignore
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream,
                **kwargs,
            )  # type: ignore

            if stream:
                logger.info("스트리밍 응답 시작")
            else:
                logger.info("채팅 완성 성공")

            return response

        except Exception as e:
            logger.error(f"채팅 완성 실패: {str(e)}")
            raise

    def simple_chat(
        self,
        user_message: str,
        system_message: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """간단한 채팅 요청 (단일 메시지)

        Args:
            user_message: 사용자 메시지
            system_message: 시스템 메시지 (선택사항)
            model: 사용할 모델 ID (기본값: 첫 번째 사용 가능한 모델)
            **kwargs: 추가 OpenAI API 파라미터

        Returns:
            str: 어시스턴트 응답 텍스트

        Raises:
            Exception: API 호출 실패
        """
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": user_message})

        response = self.chat_completion(messages=messages, model=model, **kwargs)

        if not isinstance(response, ChatCompletion):
            raise ValueError("스트리밍 응답이 아닌 일반 응답을 기대했습니다")

        return response.choices[0].message.content or ""

    def stream_chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        **kwargs: Any,
    ) -> Iterator[str]:
        """스트리밍 채팅 요청

        Args:
            messages: 메시지 리스트
            model: 사용할 모델 ID (기본값: 첫 번째 사용 가능한 모델)
            **kwargs: 추가 OpenAI API 파라미터

        Yields:
            str: 스트리밍 텍스트 청크

        Raises:
            Exception: API 호출 실패
        """
        stream_response = self.chat_completion(
            messages=messages, model=model, stream=True, **kwargs
        )

        # 스트리밍 응답인지 확인
        if isinstance(stream_response, ChatCompletion):
            raise ValueError("스트리밍 응답을 기대했지만 일반 응답을 받았습니다")

        # 스트리밍 청크 처리
        for chunk in stream_response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

# app/domains/llm/controllers/llm_controller.py

from app.domains.llm.schemas import ChatCompletionRequest
from app.domains.llm.services import LLMService, get_llm_service
from fastapi import APIRouter, Depends
from shared.core.logging import get_logger
from shared.utils.response_builder import ResponseBuilder

logger = get_logger(__name__)

router = APIRouter(prefix="/llm", tags=["LLM"])


@router.get("/")
async def llm_health_check():
    """LLM 서비스 헬스 체크"""

    return ResponseBuilder.success(
        data={"status": "healthy"},
        message="LLM 서비스 정상 작동 중",
    )


@router.get("/models")
async def get_available_models(llm_service: LLMService = Depends(get_llm_service)):
    """사용 가능한 LLM 모델 목록 조회"""

    available_models = await llm_service.get_available_models()

    return ResponseBuilder.success(
        data={"servers": "", "available_models": available_models},
        message="",
    )


@router.post("/chat")
async def run_chat_completion(
    request: ChatCompletionRequest,
    llm_service: LLMService = Depends(get_llm_service),
):
    """LLM 채팅 완성 수행

    Args:
        request: 채팅 완성 요청 데이터 (메시지, 모델, 온도 등)
        llm_service: LLM 서비스 의존성

    Returns:
        채팅 완성 결과
    """
    # Pydantic 모델을 딕셔너리로 변환하여 서비스에 전달
    messages = [msg.model_dump() for msg in request.messages]

    result = await llm_service.chat_completion(
        messages=messages,
        model=request.model,
        temperature=request.temperature,
        max_tokens=request.max_tokens,
        stream=request.stream,
    )

    return ResponseBuilder.success(
        data={"result": result},
        message="채팅 완성 성공",
    )

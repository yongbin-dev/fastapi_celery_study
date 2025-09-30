# app/domains/llm/controllers/llm_controller.py
from fastapi import APIRouter, HTTPException
from app.core.logging import get_logger
from ..schemas import (
    LLMPredictRequest,
    LLMPredictResponse,
    LLMChatRequest,
    LLMChatResponse,
)
from ..tasks.llm_tasks import generate_text_task, chat_task
from app.schemas.common import ApiResponse
from app.utils.response_builder import ResponseBuilder

logger = get_logger(__name__)

router = APIRouter(prefix="/llm", tags=["LLM"])


# 실제 확인된 설정
OLLAMA_SERVERS = {
    "server1": {"url": "http://192.168.0.122:12434", "name": "qwen3-server"},
    "server2": {"url": "http://192.168.0.122:13434", "name": "qwen2-server"},
}

# 두 서버 모두 동일한 모델 보유
AVAILABLE_MODELS = ["qwen2.5vl:7b-q8_0", "qwen3:32b", "mistral-small3.2:24b"]


@router.post("/generate", response_model=ApiResponse[LLMPredictResponse])
async def generate_text(request: LLMPredictRequest):
    """
    LLM 텍스트 생성 API

    - **prompt**: 입력 프롬프트
    - **model**: 사용할 모델 이름
    - **max_tokens**: 최대 토큰 수
    - **temperature**: 생성 온도
    """
    try:
        task = generate_text_task.delay(request.prompt, request.model)

        response = LLMPredictResponse(task_id=task.id, status="PENDING")

        return ResponseBuilder.success(
            data=response, message="LLM 텍스트 생성 태스크가 시작되었습니다"
        )

    except Exception as e:
        logger.error(f"LLM 텍스트 생성 API 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat", response_model=ApiResponse[LLMChatResponse])
async def chat(request: LLMChatRequest):
    """
    LLM 채팅 API

    - **message**: 사용자 메시지
    - **conversation_id**: 대화 ID (선택)
    - **model**: 사용할 모델 이름
    - **max_length**: 최대 응답 길이
    """
    try:
        # 동기 실행 (즉시 응답)
        from ..services.llm_model import LLMModel

        model = LLMModel()
        model.load_model()

        result = model.predict(
            {"message": request.message, "max_length": request.max_length}
        )

        if result.get("status") == "failed":
            raise HTTPException(status_code=500, detail=result.get("error"))

        response = LLMChatResponse(
            response=result.get("response", ""),
            status="success",
            conversation_id=request.conversation_id,
        )

        return ResponseBuilder.success(data=response, message="LLM 채팅 응답 생성 완료")

    except Exception as e:
        logger.error(f"LLM 채팅 API 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models")
async def get_available_models():
    """사용 가능한 LLM 모델 목록 조회"""

    return ResponseBuilder.success(
        data={"servers": OLLAMA_SERVERS, "available_models": AVAILABLE_MODELS},
        message=f"",
    )

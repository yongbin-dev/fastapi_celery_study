# app/domains/llm/controllers/llm_controller.py
from fastapi import APIRouter
from shared.core.logging import get_logger
from shared.utils.response_builder import ResponseBuilder

logger = get_logger(__name__)

router = APIRouter(prefix="/llm", tags=["LLM"])


# 실제 확인된 설정
OLLAMA_SERVERS = {
    "server1": {"url": "http://192.168.0.122:12434", "name": "qwen3-server"},
    "server2": {"url": "http://192.168.0.122:13434", "name": "qwen2-server"},
}

# 두 서버 모두 동일한 모델 보유
AVAILABLE_MODELS = ["qwen2.5vl:7b-q8_0", "qwen3:32b", "mistral-small3.2:24b"]


@router.get("/")
async def ocr_healthy():
    """사용 가능한 LLM 모델 목록 조회"""

    return ResponseBuilder.success(
        data={"success"},
        message="",
    )


@router.get("/models")
async def get_available_models():
    """사용 가능한 LLM 모델 목록 조회"""

    return ResponseBuilder.success(
        data={"servers": OLLAMA_SERVERS, "available_models": AVAILABLE_MODELS},
        message="",
    )

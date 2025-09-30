# app/domains/ocr/controllers/ocr_controller.py
from fastapi import APIRouter, HTTPException
from app.core.logging import get_logger
from ..schemas import OCRExtractRequest, OCRExtractResponse
from ..tasks.ocr_tasks import extract_text_task
from app.schemas.common import ApiResponse
from app.utils.response_builder import ResponseBuilder

logger = get_logger(__name__)

router = APIRouter(prefix="/ocr", tags=["OCR"])


@router.post("/extract", response_model=ApiResponse[OCRExtractResponse])
async def extract_text(request: OCRExtractRequest):
    """
    OCR 텍스트 추출 API

    - **image_path**: 이미지 파일 경로
    - **language**: 추출할 언어 (기본값: korean)
    - **use_angle_cls**: 각도 분류 사용 여부 (기본값: True)
    - **confidence_threshold**: 신뢰도 임계값 (기본값: 0.5)
    """
    try:
        task = extract_text_task.delay(
            request.image_path, request.language, request.confidence_threshold
        )

        response = OCRExtractResponse(task_id=task.id, status="PENDING")

        return ResponseBuilder.success(
            data=response, message="OCR 텍스트 추출 태스크가 시작되었습니다"
        )

    except Exception as e:
        logger.error(f"OCR 텍스트 추출 API 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/languages")
async def get_supported_languages():
    """지원하는 언어 목록 조회"""
    languages = [
        {"code": "korean", "name": "한국어"},
        {"code": "english", "name": "영어"},
        {"code": "chinese", "name": "중국어"},
        {"code": "japanese", "name": "일본어"},
    ]

    return ResponseBuilder.success(
        data={"languages": languages}, message="지원 언어 목록"
    )

    # @router.post("/predict")
    # async def predict(request: PredictRequest):
    if request.server not in OLLAMA_SERVERS:
        return {
            "message": f"지원하지 않는 서버: {request.server}",
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "data": {"available_servers": list(OLLAMA_SERVERS.keys())},
        }

    if request.model not in AVAILABLE_MODELS:
        return {
            "message": f"지원하지 않는 모델: {request.model}",
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "data": {"available_models": AVAILABLE_MODELS},
        }

    server_info = OLLAMA_SERVERS[request.server]
    ollama_url = server_info["url"]

    logging.info(f"Server: {server_info['name']} ({ollama_url})")
    logging.info(f"Model: {request.model}")

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{ollama_url}/api/generate",
            json={"model": request.model, "prompt": request.prompt, "stream": False},
        )

        logging.info(f"Response Status Code: {response}")

        if response.status_code == 200:
            result = response.json()
            return ResponseBuilder.success(data=result)


# @router.get("/models")
# async def get_supported_models():
#     """지원하는 언어 목록 조회"""
#     languages = [
#         {"code": "korean", "name": "한국어"},
#         {"code": "english", "name": "영어"},
#         {"code": "chinese", "name": "중국어"},
#         {"code": "japanese", "name": "일본어"},
#     ]

#     return ResponseBuilder.success(data={"languages": languages}, message="지원 언어 목록")

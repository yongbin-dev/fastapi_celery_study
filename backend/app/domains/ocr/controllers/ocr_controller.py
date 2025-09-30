# app/domains/ocr/controllers/ocr_controller.py
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.core.logging import get_logger
from app.utils.response_builder import ResponseBuilder

from ..services import OCRService, get_ocr_service

logger = get_logger(__name__)

router = APIRouter(prefix="/ocr", tags=["OCR"])


# @router.post("/extract", response_model=ApiResponse[OCRExtractResponse])
# async def extract_text(
#     image_file: UploadFile = File(...),
#     language: str = Form("korean"),
#     confidence_threshold: float = Form(0.5),
#     use_angle_cls: bool = Form(True),
# ):
#     """
#     OCR 텍스트 추출 API (비동기)

#     - **image_file**: 이미지 파일 (multipart/form-data)
#     - **language**: 추출할 언어 (기본값: korean)
#     - **use_angle_cls**: 각도 분류 사용 여부 (기본값: True)
#     - **confidence_threshold**: 신뢰도 임계값 (기본값: 0.5)
#     """
#     try:
#         # 이미지 파일 읽기
#         image_data = await image_file.read()

#         # Celery Task로 비동기 처리
#         task = extract_text_task.delay(
#             image_data=image_data,
#             language=language,
#             confidence_threshold=confidence_threshold,
#             use_angle_cls=use_angle_cls,
#         )

#         response = OCRExtractResponse(task_id=task.id, status="PENDING")

#         return ResponseBuilder.success(
#             data=response, message="OCR 텍스트 추출 태스크가 시작되었습니다"
#         )

#     except Exception as e:
#         logger.error(f"OCR 텍스트 추출 API 오류: {str(e)}")
#         raise HTTPException(status_code=500, detail=str(e))


@router.post("/extract/sync")
async def extract_text_sync(
    image_file: UploadFile = File(...),
    language: str = Form("korean"),
    confidence_threshold: float = Form(0.5),
    use_angle_cls: bool = Form(True),
    ocr_service: OCRService = Depends(get_ocr_service),
):
    """
    OCR 텍스트 추출 API (동기)

    - **image_file**: 이미지 파일 (multipart/form-data)
    - **language**: 추출할 언어 (기본값: korean)
    - **use_angle_cls**: 각도 분류 사용 여부 (기본값: True)
    - **confidence_threshold**: 신뢰도 임계값 (기본값: 0.5)
    """

    # 이미지 파일 읽기
    image_data = await image_file.read()

    # Service를 통한 동기 처리
    result = ocr_service.extract_text_from_image(
        image_data=image_data,
        language=language,
        confidence_threshold=confidence_threshold,
        use_angle_cls=use_angle_cls,
    )

    if result.status == "failed":
        raise HTTPException(status_code=400, detail=result.error)

    return ResponseBuilder.success(
        data=result.model_dump(), message="OCR 텍스트 추출 완료"
    )


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


@router.get("/health")
async def health_check():
    """헬스 체크"""
    return ResponseBuilder.success(
        data={"status": "healthy"}, message="OCR 서비스 정상"
    )

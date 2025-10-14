# app/domains/ocr/controllers/ocr_controller.py
from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logging import get_logger
from app.domains.common.services.common_service import CommonService, get_common_service
from app.utils.response_builder import ResponseBuilder

from ..services import OCRService, get_ocr_service

logger = get_logger(__name__)

router = APIRouter(prefix="/ocr", tags=["OCR"])


@router.post("/extract/sync")
async def extract_text_sync(
    image_file: UploadFile = File(...),
    language: str = Form("korean"),
    confidence_threshold: float = Form(0.5),
    use_angle_cls: bool = Form(True),
    service: OCRService = Depends(get_ocr_service),
    common_service: CommonService = Depends(get_common_service),
    db: AsyncSession = Depends(get_db),
):
    """
    OCR 텍스트 추출 API (동기)

    - **image_file**: 이미지 파일 (multipart/form-data)
    - **language**: 추출할 언어 (기본값: korean)
    - **use_angle_cls**: 각도 분류 사용 여부 (기본값: True)
    - **confidence_threshold**: 신뢰도 임계값 (기본값: 0.5)
    """
    # image_data = await image_file.read()
    # filename = image_file.filename or "unknown.png"
    # image_response = await common_service.save_image(
    #     image_data, filename, image_file.content_type
    # )

    # result = service.extract_text_from_image(
    #     image_data=image_data,
    #     language=language,
    #     confidence_threshold=confidence_threshold,
    #     use_angle_cls=use_angle_cls,
    # )

    # ocr_results = await common_service.save_ocr_execution_to_db(
    #     db=db, image_response=image_response, ocr_result=result
    # )

    return ResponseBuilder.success(data="", message="OCR 텍스트 추출 완료")


@router.get("/results")
async def get_all_ocr_executions(
    service: OCRService = Depends(get_ocr_service),
    db: AsyncSession = Depends(get_db),
):
    result = await service.get_all_ocr_executions(db)
    return ResponseBuilder.success(data=result)


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

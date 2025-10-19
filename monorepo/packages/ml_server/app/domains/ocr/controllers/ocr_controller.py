# app/domains/ocr/controllers/ocr_controller.py
from fastapi import APIRouter, Depends, Form
from shared.core.logging import get_logger
from shared.utils.response_builder import ResponseBuilder
from sqlalchemy.ext.asyncio import AsyncSession
from shared.core.database import get_db
from shared.service.common_service import CommonService, get_common_service
from app.models.ocr_model import get_ocr_model

logger = get_logger(__name__)

router = APIRouter(prefix="/ocr", tags=["OCR"])


@router.get("/extract")
async def run_ocr_image_extract(
    language: str = Form("korean"),
    confidence_threshold: float = Form(0.5),
    use_angle_cls: bool = Form(True),
    common_service : CommonService = Depends(get_common_service),
    db: AsyncSession = Depends(get_db),
    
):
    """image ocr"""
  
    model = get_ocr_model(use_angle_cls=use_angle_cls, lang=language)
    # logger.info(f"OCR 실행 시작: 이미지 크기 {len(image_data)} bytes")
    
    image_data = await common_service.load_image("");
    result = model.predict(image_data, confidence_threshold)
    
    # OCRExecution 생성
    # ocr_execution_data = OCRExecutionCreate(
    #     chain_id=chain_id,
    #     image_path=image_response.private_img,
    #     public_path=image_response.public_img,
    #     status=ocr_result.status,
    #     error=ocr_result.error,
    # )
    # db_ocr_execution = await ocr_execution_crud.create(
    #     db=db, obj_in=ocr_execution_data
    # )

    # # OCRTextBox 생성
    # for box in ocr_result.text_boxes:
    #     text_box_data = OCRTextBoxCreate(
    #         ocr_execution_id=db_ocr_execution.id,  # type: ignore
    #         text=box.text,
    #         confidence=box.confidence,
    #         bbox=box.bbox,
    #     )

    #     await ocr_text_box_crud.create(db=db, obj_in=text_box_data)

    # logger.info(f"OCR 실행 정보 DB 저장 완료: ID={db_ocr_execution.id}")
    # OCRResultDTO.model_validate(db_ocr_execution)
    

    return ResponseBuilder.success(
        data="", message=""
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

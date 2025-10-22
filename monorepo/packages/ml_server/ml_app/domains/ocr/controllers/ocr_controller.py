# app/domains/ocr/controllers/ocr_controller.py
from fastapi import APIRouter, Depends, Form
from ml_app.models.ocr_model import get_ocr_model
from shared.core.database import get_db
from shared.core.logging import get_logger
from shared.service.common_service import CommonService, get_common_service
from shared.utils.response_builder import ResponseBuilder
from sqlalchemy.ext.asyncio import AsyncSession

logger = get_logger(__name__)

router = APIRouter(prefix="/ocr", tags=["OCR"])


@router.post("/extract")
async def run_ocr_image_extract(
    image_path : str = Form(""),
    language: str = Form("korean"),
    confidence_threshold: float = Form(0.5),
    use_angle_cls: bool = Form(True),
    common_service : CommonService = Depends(get_common_service),
    db: AsyncSession = Depends(get_db),
):
    """image ocr"""
    model = get_ocr_model(use_angle_cls=use_angle_cls, lang=language)
    # logger.info(f"OCR 실행 시작: 이미지 크기 {len(image_data)} bytes")
    image_data = await common_service.load_image(image_path)
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
        data=result, message=""
    )

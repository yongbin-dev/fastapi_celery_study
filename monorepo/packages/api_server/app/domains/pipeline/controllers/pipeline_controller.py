"""파이프라인 API 컨트롤러

CR 추출 파이프라인 REST API 엔드포인트
"""

import uuid
from typing import List

from app.domains.ocr.services.ocr_service import OCRService, get_ocr_service
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from shared.core.database import get_db
from shared.core.logging import get_logger
from shared.service.common_service import CommonService, get_common_service
from shared.utils.response_builder import ResponseBuilder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from ..schemas.pipeline_schemas import (
    PipelineHistoryResponse,
    PipelineStartResponse,
    PipelineStatusResponse,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/pipeline", tags=["Pipeline"])


@router.post("/run-pipeline", response_model=PipelineStartResponse)
async def create_pipeline(
    image_file: UploadFile = File(...),
    language: str = Form("korean"),
    confidence_threshold: float = Form(0.5),
    use_angle_cls: bool = Form(True),
    service: OCRService = Depends(get_ocr_service),
    common_service: CommonService = Depends(get_common_service),
    db: AsyncSession = Depends(get_db),
):
    """CR 추출 파이프라인 시작

    Args:
        file: 처리할 이미지 또는 PDF 파일
        ocr_engine: OCR 엔진 (easyocr, paddleocr)
        llm_model: LLM 모델 (gpt-4, gpt-3.5-turbo)
        min_confidence: 최소 OCR 신뢰도 (0.0-1.0)

    Returns:
        파이프라인 시작 응답

    Raises:
        HTTPException: 처리 중 오류 발생 시
    """
    try:
        # 1. 이미지를 Supabase Storage에 저장
        image_data = await image_file.read()

        filename = image_file.filename or "unknown.png"
        # encoded_name = quote(filename)  # URL-safe 인코딩
        image_response = await common_service.save_image(
            image_data, filename, image_file.content_type
        )

        chain_id = str(uuid.uuid4())
        # 2. ML 서버의 CELERY_CHAIN 호출
        await service.call_ml_server_ocr(
            chain_id=chain_id,
            image_path=image_response.private_img,
            language=language,
            confidence_threshold=confidence_threshold,
            use_angle_cls=use_angle_cls,
        )

        # # OCRExecution 생성
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
        # ocr_execution = await common_service.save_ocr_execution_to_db(
        #     db=db, image_response=image_response, ocr_result=ocr_result
        # )

        #           PipelineStartResponse(
        #             context_id=context_id,
        #             status="started",
        #             message="CR extraction pipeline started successfully",
        #         )

        return ResponseBuilder.success(
            data=image_response, message="OCR 텍스트 추출 완료"
        )

        #

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/status/{chain_id}", response_model=PipelineStatusResponse)
async def get_pipeline_status(chain_id: str, db: Session = Depends(get_db)):
    pass


@router.get("/history", response_model=List[PipelineHistoryResponse])
async def get_pipeline_history(
    limit: int = 100, offset: int = 0, db: Session = Depends(get_db)
) -> List[PipelineHistoryResponse]:
    """파이프라인 실행 이력 조회

    Args:
        limit: 최대 조회 개수
        offset: 시작 위치
        db: DB 세션

    Returns:
        파이프라인 실행 이력 리스트
    """

    # chain_execs = (
    #     db.query(ChainExecution)
    #     .order_by(ChainExecution.started_at)
    #     .limit(limit)
    #     .offset(offset)
    #     .all()
    # )

    return []

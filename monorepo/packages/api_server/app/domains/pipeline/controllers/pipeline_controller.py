"""파이프라인 API 컨트롤러

CR 추출 파이프라인 REST API 엔드포인트
"""

import uuid

from app.domains.ocr.services.ocr_service import OCRService, get_ocr_service
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from redis import Redis
from shared.core.database import get_db
from shared.core.logging import get_logger
from shared.repository.crud.async_crud import chain_execution_crud
from shared.schemas.chain_execution import ChainExecutionResponse
from shared.service.common_service import CommonService, get_common_service
from shared.service.redis_service import RedisService, get_redis_service
from shared.utils.response_builder import ResponseBuilder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from ..schemas.pipeline_schemas import (
    PipelineStartResponse,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/pipeline", tags=["Pipeline"])


@router.post("/extract/pdf")
async def extract_text_sync_by_pdf(
    pdf_file: UploadFile = File(...),
    service: OCRService = Depends(get_ocr_service),
    common_service: CommonService = Depends(get_common_service),
    db: AsyncSession = Depends(get_db),
):
    """
    OCR 텍스트 추출 API (동기)

    - **pdf_file**: PDF 파일 (multipart/form-data)
    """
    try:
        filename = pdf_file.filename
        pdf_file_bytes = await pdf_file.read()

        if filename is None :
            raise Exception()

        image_response_list = await common_service.save_pdf(
            original_filename=filename ,
            pdf_file_bytes=pdf_file_bytes
        )

        await service.call_ml_server_pdf(
            image_response_list=image_response_list
        )

        return ResponseBuilder.success(
            data=image_response_list,
            message="PDF 페이지 수 확인 완료"
        )

    except Exception as e:
        logger.error(f"PDF 처리 중 오류 발생: {str(e)}")
        return ResponseBuilder.error(message=f"PDF 처리 실패: {str(e)}")


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
        encoded_file_name = str(uuid.uuid4()) + "_" + filename

        image_response = await common_service.save_image(
            image_data, encoded_file_name, image_file.content_type
        )

        chain_id = str(uuid.uuid4())
        # 2. ML 서버의 CELERY_CHAIN 호출
        await service.call_ml_server_ocr(
            chain_id=chain_id,
            private_image_path=image_response.private_img,
            public_image_path=image_response.public_img,
            language=language,
            confidence_threshold=confidence_threshold,
            use_angle_cls=use_angle_cls,
        )

        return ResponseBuilder.success(
            data=image_response, message="OCR 텍스트 추출 완료"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/status/{chain_id}")
async def get_pipeline_status(
        chain_id: str,
        db: Session = Depends(get_db),
        redis_service : RedisService = Depends(get_redis_service)
    ):
    redis_client : Redis = redis_service.get_redis_client()
    result = redis_client.get("pipeline:context:"+chain_id)
    logger.info(result)
    return ResponseBuilder.success(
        data=result,
        message=""
    )

# response_model=List[PipelineHistoryResponse]
@router.get("/history", )
async def get_pipeline_history(
    limit: int = 100, offset: int = 0, db: AsyncSession = Depends(get_db)
) :
    """파이프라인 실행 이력 조회

    Args:
        limit: 최대 조회 개수
        offset: 시작 위치
        db: DB 세션

    Returns:
        파이프라인 실행 이력 리스트
    """
    result = await chain_execution_crud.get_multi_with_task_logs(db)
    list = []

    if result is None:
        list = []
    else:
        list = [ChainExecutionResponse.model_validate(ocr) for ocr in result]
    return ResponseBuilder.success(
        data=list
    )



@router.post("/batch", response_model=PipelineStartResponse)
async def start_batch_pipeline(
    batch_name: str = Form(...),
    files: list[UploadFile] = File(...),
    common_service: CommonService = Depends(get_common_service),
):
    """배치 파이프라인 시작

    여러 이미지를 배치로 처리합니다.

    Args:
        batch_name: 배치 이름
        files: 업로드할 이미지 파일 목록
        common_service: 공통 서비스

    Returns:
        배치 ID 및 시작 정보
    """

    pass


@router.get("/batch/{batch_id}")
async def get_batch_status(
    batch_id: str,
    db: Session = Depends(get_db),
):
    """배치 처리 상태 조회
    Args:
        batch_id: 배치 ID
        db: DB 세션
    Returns:
        배치 처리 상태 정보
    """
    from shared.repository.crud.sync_crud.batch_execution import batch_execution_crud

    try:
        batch_execution = batch_execution_crud.get_by_batch_id(db, batch_id=batch_id)

        if not batch_execution:
            raise HTTPException(status_code=404, detail="배치를 찾을 수 없습니다")

        # 진행률 계산
        progress_percentage = batch_execution.get_progress_percentage()

        # 예상 남은 시간 계산 (간단한 추정)
        estimated_time_remaining = None
        if batch_execution.started_at and batch_execution.completed_images > 0:
            from datetime import datetime

            elapsed = (datetime.now() - batch_execution.started_at).total_seconds()
            avg_time_per_image = elapsed / batch_execution.completed_images
            remaining_images = (
                batch_execution.total_images - batch_execution.completed_images
            )
            estimated_time_remaining = avg_time_per_image * remaining_images

        from shared.schemas.batch_execution import BatchStatusResponse

        return ResponseBuilder.success(
            data=BatchStatusResponse(
                batch_id=batch_execution.batch_id,
                status=batch_execution.status,
                total_images=batch_execution.total_images,
                completed_images=batch_execution.completed_images,
                failed_images=batch_execution.failed_images,
                progress_percentage=progress_percentage,
                started_at=batch_execution.started_at,
                finished_at=batch_execution.finished_at,
                estimated_time_remaining=estimated_time_remaining,
            )
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"배치 상태 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/batch")
async def get_batch_list(
    limit: int = 10,
    db: Session = Depends(get_db),
):
    """배치 목록 조회

    Args:
        limit: 최대 조회 개수
        db: DB 세션

    Returns:
        배치 목록
    """
    from shared.repository.crud.sync_crud.batch_execution import batch_execution_crud
    from shared.schemas.batch_execution import BatchExecutionResponse

    try:
        batches = batch_execution_crud.get_recent_batches(db, limit=limit)

        batch_list = []
        for batch in batches:
            response = BatchExecutionResponse.model_validate(batch)
            response.progress_percentage = batch.get_progress_percentage()
            batch_list.append(response)

        return ResponseBuilder.success(data=batch_list)

    except Exception as e:
        logger.error(f"배치 목록 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

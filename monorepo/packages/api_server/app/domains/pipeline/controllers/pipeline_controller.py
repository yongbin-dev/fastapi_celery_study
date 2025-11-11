"""파이프라인 API 컨트롤러

CR 추출 파이프라인 REST API 엔드포인트
"""

from app.domains.ocr.services.ocr_service import OCRService, get_ocr_service
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from shared.core.database import get_db
from shared.core.logging import get_logger
from shared.repository.crud.async_crud import chain_execution_crud
from shared.schemas.chain_execution import ChainExecutionResponse
from shared.service.common_service import CommonService, get_common_service
from shared.utils.response_builder import ResponseBuilder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

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

        if filename is None:
            raise Exception()

        image_response_list = await common_service.save_pdf(
            original_filename=filename, pdf_file_bytes=pdf_file_bytes
        )

        await service.call_ml_server_pdf(image_response_list=image_response_list)

        return ResponseBuilder.success(
            data=image_response_list, message="PDF 페이지 수 확인 완료"
        )

    except Exception as e:
        logger.error(f"PDF 처리 중 오류 발생: {str(e)}")
        return ResponseBuilder.error(message=f"PDF 처리 실패: {str(e)}")


# response_model=List[PipelineHistoryResponse]
@router.get(
    "/history",
)
async def get_pipeline_history(
    limit: int = 100, offset: int = 0, db: AsyncSession = Depends(get_db)
):
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
    return ResponseBuilder.success(data=list)


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


@router.post("/cancel/{chain_id}")
async def cancel_pipeline(
    chain_id: str,
    db: Session = Depends(get_db),
):
    """파이프라인 작업 취소

    Args:
        chain_id: Chain ID
        db: DB 세션

    Returns:
        취소 결과
    """
    from shared.pipeline.cache import get_pipeline_cache_service
    from shared.repository.crud.sync_crud.chain_execution import chain_execution_crud
    from shared.schemas.enums import ProcessStatus

    cache_service = get_pipeline_cache_service()

    try:
        # 1. DB에서 chain_execution 조회
        chain_execution = chain_execution_crud.get_by_chain_id(db, chain_id=chain_id)

        if not chain_execution:
            raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다")

        # 이미 완료된 작업인지 확인
        if chain_execution.status in [
            ProcessStatus.SUCCESS.value,
            ProcessStatus.FAILURE.value,
            ProcessStatus.REVOKED.value,
        ]:
            return ResponseBuilder.error(
                message=f"이미 완료된 작업입니다 (상태: {chain_execution.status})"
            )

        # 2. Celery 작업 취소
        if chain_execution.celery_task_id:
            from celery import Celery
            from shared.config import settings

            # Celery 앱 인스턴스 생성
            celery_app = Celery(broker=settings.REDIS_URL, backend=settings.REDIS_URL)

            celery_app.control.revoke(
                chain_execution.celery_task_id, terminate=True, signal="SIGKILL"
            )
            logger.info(f"✅ Celery task 취소 요청: {chain_execution.celery_task_id}")

        # 3. Redis Context 상태를 REVOKED로 업데이트
        try:
            batch_id = chain_execution.batch_id or ""
            if cache_service.exists(batch_id, chain_id):
                context = cache_service.load_context(batch_id, chain_id)
                context.update_status(ProcessStatus.REVOKED)
                cache_service.save_context(context)
                logger.info("✅ Redis context 상태 업데이트: REVOKED")
        except Exception as e:
            logger.warning(f"Redis context 업데이트 실패 (무시): {str(e)}")

        # 4. DB 상태 업데이트
        chain_execution_crud.update_status(
            db=db, chain_execution=chain_execution, status=ProcessStatus.REVOKED
        )

        return ResponseBuilder.success(message=f"작업 {chain_id}가 취소되었습니다")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"작업 취소 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

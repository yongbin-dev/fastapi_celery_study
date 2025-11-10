# app/domains/ocr/controllers/ocr_controller.py

from fastapi import APIRouter, Depends
from shared.core.database import get_db
from shared.core.logging import get_logger
from shared.utils.response_builder import ResponseBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from ..services import OCRService, get_ocr_service

logger = get_logger(__name__)

router = APIRouter(prefix="/ocr", tags=["OCR"])


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


@router.get("/batch/{task_id}/status")
async def get_batch_status(
    task_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    배치 OCR 처리 상태 조회

    Celery 태스크 ID로 배치 처리 상태를 조회합니다.

    Args:
        task_id: Celery 태스크 ID

    Returns:
        배치 처리 상태 및 결과
    """
    try:
        # Celery 결과 조회
        import sys
        from pathlib import Path

        from celery.result import AsyncResult

        # celery_worker 패키지 경로 추가
        celery_worker_path = (
            Path(__file__).parent.parent.parent.parent.parent.parent / "celery_worker"
        )
        sys.path.insert(0, str(celery_worker_path))

        from celery_app import celery_app

        async_result = AsyncResult(task_id, app=celery_app)

        # 태스크 상태 확인
        task_state = async_result.state
        task_info = {
            "task_id": task_id,
            "state": task_state,
        }

        if async_result.ready():
            if async_result.successful():
                # 태스크 성공 - batch_id 획득
                batch_id = async_result.result
                task_info["batch_id"] = batch_id

                # DB에서 배치 실행 상태 조회
                from shared.repository.crud.async_crud.batch_execution import (
                    async_batch_execution_crud,
                )

                batch_execution = await async_batch_execution_crud.get_by_batch_id(
                    db, batch_id=batch_id
                )

                if batch_execution:
                    task_info["batch_status"] = batch_execution.status
                    task_info["total_images"] = batch_execution.total_images
                    task_info["completed_images"] = batch_execution.completed_images
                    task_info["failed_images"] = batch_execution.failed_images
                    task_info["completed_chunks"] = batch_execution.completed_chunks
                    task_info["batch_name"] = batch_execution.batch_name

                logger.info(f"✅ 배치 상태 조회 성공: task_id={task_id}")
            else:
                # 태스크 실패
                task_info["error"] = str(async_result.result)
                logger.error(f"❌ 배치 태스크 실패: task_id={task_id}")
        else:
            # 진행 중
            task_info["message"] = "태스크 진행 중"
            logger.info(f"⏳ 배치 태스크 진행 중: task_id={task_id}")

        return ResponseBuilder.success(
            data=task_info,
            message="배치 상태 조회 완료",
        )

    except Exception as e:
        logger.error(f"❌ 배치 상태 조회 실패: {str(e)}")
        return ResponseBuilder.error(message=f"배치 상태 조회 실패: {str(e)}")

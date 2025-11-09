# app/domains/ocr/controllers/ocr_controller.py
import uuid
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, Form, UploadFile
from shared.core.database import get_db
from shared.core.logging import get_logger
from shared.service.common_service import CommonService, get_common_service
from shared.utils.response_builder import ResponseBuilder
from sqlalchemy.ext.asyncio import AsyncSession

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
    try:
        # 1. 이미지를 Supabase Storage에 저장
        image_data = await image_file.read()

        filename = image_file.filename or "unknown.png"
        encoded_name = quote(filename)  # URL-safe 인코딩
        encoded_file_name = str(uuid.uuid4()) + "_" + encoded_name

        image_response = await common_service.save_image(
            image_data, encoded_file_name, image_file.content_type
        )

        chain_id = str(uuid.uuid4())
        # 2. ML 서버의 OCR API 호출
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
        logger.error(f"OCR 처리 중 오류 발생: {str(e)}")
        return ResponseBuilder.error(message=f"OCR 처리 실패: {str(e)}")


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


@router.post("/extract-pdf/async")
async def extract_pdf_async(
    pdf_file: UploadFile = File(...),
    chunk_size: int = Form(10),
):
    """
    PDF OCR 비동기 처리 (Celery 배치 파이프라인)

    PDF 파일을 업로드받아 이미지로 변환 후 배치 파이프라인으로 OCR을 수행합니다.
    태스크를 Celery 큐에 전송하고 즉시 task_id를 반환합니다.

    Args:
        pdf_file: PDF 파일
        chunk_size: 청크당 이미지 수 (기본값: 10)

    Returns:
        task_id: Celery 태스크 ID (결과 조회용)
    """
    try:
        # Celery worker의 batch_tasks import
        import sys
        from pathlib import Path

        # celery_worker 패키지 경로 추가
        celery_worker_path = (
            Path(__file__).parent.parent.parent.parent.parent.parent / "celery_worker"
        )
        sys.path.insert(0, str(celery_worker_path))

        from tasks.batch_tasks import start_batch_pipeline_from_pdf

        # PDF 파일 읽기
        filename = pdf_file.filename or "unknown.pdf"
        pdf_file_bytes = await pdf_file.read()

        logger.info(f"📄 PDF OCR 비동기 요청: filename={filename}")

        # Celery 태스크 시작
        task_id = start_batch_pipeline_from_pdf(
            pdf_file_bytes=pdf_file_bytes,
            original_filename=filename,
            options={},
            chunk_size=chunk_size,
        )

        logger.info(f"✅ PDF OCR 태스크 전송 완료: task_id={task_id}")

        return ResponseBuilder.success(
            data={
                "task_id": task_id,
                "filename": filename,
                "message": "PDF OCR 처리가 시작되었습니다",
            },
            message="태스크 전송 완료",
        )

    except Exception as e:
        logger.error(f"❌ PDF OCR 비동기 처리 실패: {str(e)}")
        return ResponseBuilder.error(message=f"PDF OCR 처리 실패: {str(e)}")


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

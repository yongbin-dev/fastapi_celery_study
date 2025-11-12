"""PDF 배치 처리 태스크

PDF 파일을 이미지로 변환 후 배치 OCR 처리
"""

import uuid
from typing import Any, Dict, Optional

from celery_app import celery_app
from shared.core.logging import get_logger
from shared.pipeline.exceptions import RetryableError
from shared.service.common_service import get_common_service

from .image_tasks import start_image_batch_pipeline

logger = get_logger(__name__)


@celery_app.task(
    bind=True,
    name="batch.convert_pdf_and_process",
    max_retries=3,
    autoretry_for=(ConnectionError, TimeoutError, RetryableError),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
)
def convert_pdf_and_process_task(
    self,
    batch_id: str,
    pdf_file_bytes: bytes,
    original_filename: str,
    options: Dict[str, Any],
    chunk_size: int,
) -> str:
    """PDF를 이미지로 변환 후 배치 OCR 처리 태스크

    Args:
        self: Celery task instance
        batch_id: 배치 ID
        pdf_file_bytes: PDF 파일 바이트 데이터
        original_filename: 원본 파일명
        options: 파이프라인 옵션
        chunk_size: 청크당 이미지 수

    Returns:
        batch_id: 배치 고유 ID
    """
    import asyncio

    logger.info(f"📄 PDF → 배치 OCR 시작: filename={original_filename}")

    try:
        # 1. PDF를 이미지로 변환
        async def convert_pdf():
            common_service = get_common_service()
            return await common_service.save_pdf(
                original_filename=original_filename,
                pdf_file_bytes=pdf_file_bytes,
            )

        image_responses = asyncio.run(convert_pdf())

        logger.info(f"✅ PDF 변환 완료: {len(image_responses)}개 이미지 생성")

        # 2. 배치 파이프라인 시작
        batch_name = f"pdf_{original_filename}_{uuid.uuid4().hex[:8]}"
        start_image_batch_pipeline(
            batch_id=batch_id,
            batch_name=batch_name,
            image_responses=image_responses,
            options=options,
            chunk_size=chunk_size,
            initiated_by="pdf_converter",
        )

        logger.info(
            f"🚀 PDF 배치 파이프라인 시작: batch_id={batch_id}, "
            f"images={len(image_responses)}"
        )

        return batch_id

    except Exception as e:
        logger.error(
            f"❌ PDF → 배치 OCR 실패: filename={original_filename}, error={str(e)}",
            exc_info=True,
        )
        raise


def start_pdf_batch_pipeline(
    batch_id: str,
    pdf_file_bytes: bytes,
    original_filename: str,
    options: Optional[Dict[str, Any]] = None,
    chunk_size: int = 10,
) -> str:
    """PDF 배치 파이프라인 시작 (비동기)

    PDF를 이미지로 변환한 후 배치 파이프라인을 시작합니다.
    Celery 태스크로 비동기 실행됩니다.

    Args:
        batch_id: 배치 ID
        pdf_file_bytes: PDF 파일 바이트 데이터
        original_filename: 원본 파일명
        options: 파이프라인 옵션 (기본: None)
        chunk_size: 청크당 이미지 수 (기본: 10)

    Returns:
        task_id: Celery 태스크 ID (결과 조회용)
    """
    if options is None:
        options = {}

    logger.info(f"📄 PDF 배치 파이프라인 시작 요청: filename={original_filename}")

    # Celery 태스크로 비동기 실행
    result = convert_pdf_and_process_task.apply_async(
        kwargs={
            "batch_id": batch_id,
            "pdf_file_bytes": pdf_file_bytes,
            "original_filename": original_filename,
            "options": options,
            "chunk_size": chunk_size,
        }
    )

    logger.info(
        f"📤 PDF 배치 태스크 전송 완료: task_id={result.id}, "
        f"filename={original_filename}"
    )

    return result.id

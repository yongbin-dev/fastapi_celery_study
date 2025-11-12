# packages/celery_worker/tasks/batch/pdf_tasks.py
import asyncio
from typing import Any, Dict

from celery_app import celery_app
from shared.core.logging import get_logger
from shared.service.common_service import get_common_service

logger = get_logger(__name__)


@celery_app.task(name="batch.convert_pdf_and_process")
def convert_pdf_and_process_task(
    batch_id: str,
    batch_name: str,
    pdf_url: str,
    original_filename: str,
    options: Dict[str, Any],
    chunk_size: int,
    initiated_by: str,
):
    """
    PDF를 이미지로 변환하고, 이미지 배치 파이프라인을 시작하는 Celery 태스크
    """
    logger.info(f"PDF 변환 및 처리 작업 시작: batch_id={batch_id}")

    async def _async_run():
        common_service = get_common_service()
        # start_pdf_batch_pipeline의 비동기 로직을 이곳으로 이동
        from celery import group

        from tasks.batch.helpers import (
            convert_to_image_response_dicts,
            create_batch_execution,
            split_into_chunks,
            start_batch_execution,
        )
        from tasks.batch.image_tasks import process_image_chunk_task

        image_responses = await common_service.download_and_split_pdf(
            pdf_url, original_filename
        )
        total_images = len(image_responses)

        create_batch_execution(
            batch_id=batch_id,
            batch_name=batch_name,
            total_images=total_images,
            chunk_size=chunk_size,
            initiated_by=initiated_by,
            options=options,
        )

        image_dicts = convert_to_image_response_dicts(image_responses)
        chunks = split_into_chunks(image_dicts, chunk_size)
        chunk_tasks = group(
            process_image_chunk_task.s(
                batch_id=batch_id,
                chunk_index=idx,
                image_dicts=chunk,
                options=options,
            )
            for idx, chunk in enumerate(chunks)
        )

        start_batch_execution(batch_id)
        chunk_tasks.apply_async()

    try:
        asyncio.run(_async_run())
    except Exception as e:
        logger.error(f"❌ PDF 처리 중 오류 발생: batch_id={batch_id}, error={e}")
        raise


def start_pdf_batch_pipeline(
    batch_id: str,
    batch_name: str,
    pdf_url: str,
    original_filename: str,
    options: Dict[str, Any],
    chunk_size: int = 10,
    initiated_by: str = "api_server",
) -> str:
    """
    PDF 처리 Celery 태스크를 시작시키는 동기 함수
    """
    logger.info(f"PDF 처리 태스크 큐에 추가: batch_id={batch_id}")
    task = convert_pdf_and_process_task.apply_async(
        args=[
            batch_id,
            batch_name,
            pdf_url,
            original_filename,
            options,
            chunk_size,
            initiated_by,
        ]
    )
    return task.id

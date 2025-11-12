"""이미지 배치 처리 태스크

여러 이미지를 청크 단위로 배치 OCR 처리
"""

from typing import Any, Dict, List

from celery import group
from celery_app import celery_app
from shared.core.logging import get_logger
from shared.pipeline.exceptions import RetryableError
from shared.schemas.common import ImageResponse

from .helpers import (
    convert_to_image_response_dicts,
    create_batch_execution,
    split_into_chunks,
    start_batch_execution,
    update_batch_statistics,
)

logger = get_logger(__name__)


@celery_app.task(
    bind=True,
    name="batch.process_image_chunk",
    max_retries=3,
    autoretry_for=(ConnectionError, TimeoutError, RetryableError),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
)
def process_image_chunk_task(
    self,
    batch_id: str,
    chunk_index: int,
    image_dicts: List[Dict[str, Any]],
    options: Dict[str, Any],
):
    """이미지 청크 단위 배치 OCR 처리 태스크

    청크 내 모든 이미지를 한 번의 Batch OCR API 호출로 처리합니다.

    Args:
        self: Celery task instance
        batch_id: 배치 ID
        chunk_index: 청크 인덱스
        image_dicts: ImageResponse dict 목록
        options: 파이프라인 옵션
    """
    from tasks.pipeline import execute_batch_ocr_pipeline

    logger.info(
        f"[청크 {chunk_index}] 배치 OCR 시작: batch_id={batch_id}, "
        f"images={len(image_dicts)}"
    )

    completed_count = 0
    failed_count = 0

    try:
        # dict를 ImageResponse 객체로 복원
        image_responses = [ImageResponse(**img_dict) for img_dict in image_dicts]

        # 배치 OCR 파이프라인 실행
        result = execute_batch_ocr_pipeline(
            image_responses=image_responses,
            batch_id=batch_id,
            options=options,
        )

        completed_count = result.get("completed_count", 0)
        failed_count = result.get("failed_count", 0)

        logger.info(
            f"[청크 {chunk_index}] 배치 OCR 완료: "
            f"성공={completed_count}, 실패={failed_count}"
        )

    except Exception as e:
        # 전체 청크 실패
        failed_count = len(image_dicts)
        completed_count = 0

        logger.error(
            f"[청크 {chunk_index}] 배치 OCR 실패: "
            f"batch_id={batch_id}, error={str(e)}",
            exc_info=True,
        )

    # 배치 통계 업데이트
    update_batch_statistics(
        batch_id=batch_id,
        completed_count=completed_count,
        failed_count=failed_count,
    )

    logger.info(
        f"[청크 {chunk_index}] 처리 완료: "
        f"completed={completed_count}, failed={failed_count}"
    )


def start_image_batch_pipeline(
    batch_id: str,
    batch_name: str,
    image_responses: List[ImageResponse],
    options: Dict[str, Any],
    chunk_size: int = 10,
    initiated_by: str = "api_server",
) -> str:
    """이미지 배치 파이프라인 시작

    여러 이미지를 청크로 나누어 병렬 처리합니다.

    Args:
        batch_id: 배치 ID
        batch_name: 배치 이름
        image_responses: 처리할 ImageResponse 객체 목록
        options: 파이프라인 옵션
        chunk_size: 청크당 이미지 수 (기본: 10)
        initiated_by: 시작한 사용자/시스템

    Returns:
        batch_id: 배치 고유 ID
    """
    logger.info(
        f"배치 파이프라인 시작 준비: batch_id={batch_id}, "
        f"total_images={len(image_responses)}, chunk_size={chunk_size}"
    )

    # 1. BatchExecution 레코드 생성
    create_batch_execution(
        batch_id=batch_id,
        batch_name=batch_name,
        total_images=len(image_responses),
        chunk_size=chunk_size,
        initiated_by=initiated_by,
        options=options,
    )

    # 2. ImageResponse를 dict로 변환 (Celery 직렬화용)
    image_dicts = convert_to_image_response_dicts(image_responses)

    # 3. 청크로 분할
    chunks = split_into_chunks(image_dicts, chunk_size)

    logger.info(
        f"배치 파이프라인 청크 분할 완료: "
        f"total_images={len(image_responses)}, chunks={len(chunks)}"
    )

    # 4. 각 청크를 병렬 처리할 태스크 그룹 생성
    chunk_tasks = group(
        process_image_chunk_task.s(
            batch_id=batch_id,
            chunk_index=idx,
            image_dicts=chunk,
            options=options,
        )
        for idx, chunk in enumerate(chunks)
    )

    # 5. 배치 실행 시작 상태로 변경
    start_batch_execution(batch_id)

    # 6. 비동기 실행
    chunk_tasks.apply_async()

    logger.info(
        f"✅ 배치 파이프라인 시작됨: batch_id={batch_id}, " f"chunks={len(chunks)}"
    )

    return batch_id

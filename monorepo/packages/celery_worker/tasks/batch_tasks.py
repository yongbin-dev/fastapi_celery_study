"""배치 파이프라인 Celery 태스크

여러 이미지를 배치로 처리하는 Celery 태스크 모음
"""

import uuid
from typing import Any, Dict, List

from celery import group
from celery_app import celery_app
from shared.core.database import get_db_manager
from shared.core.logging import get_logger
from shared.pipeline.exceptions import RetryableError
from shared.schemas.common import ImageResponse

logger = get_logger(__name__)


@celery_app.task(
    bind=True,
    name="pipeline.process_chunk",
    max_retries=3,
    autoretry_for=(ConnectionError, TimeoutError, RetryableError),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
)
def process_chunk_task(
    self,
    batch_id: str,
    chunk_index: int,
    image_response_dicts: List[Dict[str, str]],
    options: Dict[str, Any],
) -> Dict[str, Any]:
    """청크 단위 파이프라인 처리
    Args:
        self: Celery task instance
        batch_id: 배치 ID
        chunk_index: 청크 인덱스
        image_response_dicts: ImageResponse dict 목록
        options: 파이프라인 옵션
    Returns:
        청크 처리 결과 (성공/실패 이미지 수)
    """
    from shared.repository.crud.sync_crud.batch_execution import batch_execution_crud

    # pipeline_tasks에서 start_pipeline import
    from .pipeline_tasks import start_pipeline

    logger.info(
        f"청크 처리 시작: batch_id={batch_id}, chunk={chunk_index}, "
        f"images={len(image_response_dicts)}"
    )

    completed_count = 0
    failed_count = 0
    results = []

    # 각 이미지에 대해 개별 파이프라인 실행
    for idx, image_dict in enumerate(image_response_dicts):
        try:
            # dict를 ImageResponse 객체로 복원
            image_response = ImageResponse(**image_dict)

            # 개별 파이프라인 실행
            context_id = start_pipeline(image_response, batch_id, options)
            file_path = image_response.private_img
            completed_count += 1
            results.append({
                "file_path": file_path,
                "context_id": context_id,
                "status": "success",
            })

            logger.info(
                f"이미지 처리 완료: batch={batch_id}, chunk={chunk_index}, "
                f"idx={idx}, file={file_path}"
            )

        except Exception as e:
            file_path = image_dict.get("private_img", "unknown")
            failed_count += 1
            results.append({
                "file_path": file_path,
                "status": "failed",
                "error": str(e),
            })

            logger.error(
                f"이미지 처리 실패: batch={batch_id}, chunk={chunk_index}, "
                f"idx={idx}, file={file_path}, error={str(e)}"
            )

    # 배치 통계 업데이트
    with get_db_manager().get_sync_session() as session:
        if session:
            batch_execution = batch_execution_crud.get_by_batch_id(
                session, batch_id=batch_id
            )

            if batch_execution:
                # 완료/실패 이미지 수 업데이트
                if completed_count > 0:
                    batch_execution_crud.increment_completed_images(
                        session, batch_execution=batch_execution, count=completed_count
                    )

                if failed_count > 0:
                    batch_execution_crud.increment_failed_images(
                        session, batch_execution=batch_execution, count=failed_count
                    )

                # 청크 완료 표시
                batch_execution_crud.increment_completed_chunks(
                    session, batch_execution=batch_execution
                )

    logger.info(
        f"청크 처리 완료: batch_id={batch_id}, chunk={chunk_index}, "
        f"completed={completed_count}, failed={failed_count}"
    )

    return {
        "batch_id": batch_id,
        "chunk_index": chunk_index,
        "completed": completed_count,
        "failed": failed_count,
        "results": results,
    }


def start_batch_pipeline(
    batch_name: str,
    image_response_list: List[ImageResponse],
    options: Dict[str, Any],
    chunk_size: int = 10,
    initiated_by: str = "api_server",
) -> str:
    """배치 파이프라인 시작
    Args:
        batch_name: 배치 이름
        image_response_list: 처리할 ImageResponse 객체 목록
        options: 파이프라인 옵션
        chunk_size: 청크당 이미지 수
        initiated_by: 시작한 사용자/시스템
    Returns:
        batch_id: 배치 고유 ID
    """
    from shared.repository.crud.sync_crud.batch_execution import batch_execution_crud

    # 1. Batch ID 생성
    batch_id = str(uuid.uuid4())

    # 2. DB에 BatchExecution 생성
    with get_db_manager().get_sync_session() as session:
        if not session:
            raise RuntimeError("DB 세션 생성 실패")

        batch_execution_crud.create_batch_execution(
            db=session,
            batch_id=batch_id,
            batch_name=batch_name,
            total_images=len(image_response_list),
            chunk_size=chunk_size,
            initiated_by=initiated_by,
            options=options,
        )

    # 3. ImageResponse 객체를 dict로 변환 (Celery 직렬화를 위해)
    image_response_dicts = [
        {
            "public_img": img.public_img,
            "private_img": img.private_img,
        }
        for img in image_response_list
    ]

    # 4. 파일 경로를 청크로 분할
    chunks = []
    for i in range(0, len(image_response_dicts), chunk_size):
        chunk_files = image_response_dicts[i : i + chunk_size]
        chunks.append(chunk_files)

    logger.info(
        f"배치 파이프라인 시작: batch_id={batch_id}, "
        f"total_images={len(image_response_list)}, chunks={len(chunks)}"
    )

    # 5. 각 청크를 독립적인 태스크로 실행
    # group을 사용하여 병렬 처리
    chunk_tasks = group(
        process_chunk_task.s(
            batch_id=batch_id,
            chunk_index=idx,
            image_response_dicts=chunk_files,
            options=options,
        )
        for idx, chunk_files in enumerate(chunks)
    )

    # 6. 배치 시작 상태로 변경
    with get_db_manager().get_sync_session() as session:
        if session:
            batch_execution = batch_execution_crud.get_by_batch_id(
                session, batch_id=batch_id
            )
            if batch_execution:
                batch_execution.start_execution()
                session.commit()

    # 7. 비동기 실행
    chunk_tasks.apply_async()

    logger.info(f"배치 태스크 시작됨: batch_id={batch_id}")

    return batch_id

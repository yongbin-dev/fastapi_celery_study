"""배치 처리 헬퍼 함수들

배치 파이프라인에서 사용하는 공통 유틸리티 함수들
"""

from typing import Any, Dict, List

from shared.core.database import get_db, get_db_manager
from shared.core.logging import get_logger
from shared.schemas.common import ImageResponse
from shared.schemas.enums import ProcessStatus

logger = get_logger(__name__)


def convert_to_image_response_dicts(
    image_responses: List[ImageResponse],
) -> List[Dict[str, str]]:
    """ImageResponse 객체를 dict로 변환 (Celery 직렬화용)

    Args:
        image_responses: ImageResponse 객체 리스트

    Returns:
        dict 형태의 이미지 정보 리스트
    """
    return [
        {
            "public_img": img.public_img,
            "private_img": img.private_img,
        }
        for img in image_responses
    ]


def split_into_chunks(items: List[Any], chunk_size: int) -> List[List[Any]]:
    """리스트를 청크로 분할

    Args:
        items: 분할할 리스트
        chunk_size: 청크 크기

    Returns:
        청크 리스트
    """
    chunks = []
    for i in range(0, len(items), chunk_size):
        chunk = items[i : i + chunk_size]
        chunks.append(chunk)
    return chunks


def update_batch_statistics(
    batch_id: str,
    completed_count: int,
    failed_count: int,
):
    """배치 실행 통계 업데이트

    Args:
        batch_id: 배치 ID
        completed_count: 완료된 이미지 수
        failed_count: 실패한 이미지 수
    """
    from shared.repository.crud.sync_crud.batch_execution import batch_execution_crud

    with get_db_manager().get_sync_session() as session:
        if not session:
            logger.warning("DB 세션 생성 실패 - 통계 업데이트 건너뜀")
            return

        batch_execution = batch_execution_crud.get_by_batch_id(
            session, batch_id=batch_id
        )

        if not batch_execution:
            logger.warning(f"BatchExecution을 찾을 수 없음: batch_id={batch_id}")
            return

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


def create_batch_execution(
    batch_id: str,
    batch_name: str,
    total_images: int,
    chunk_size: int,
    initiated_by: str,
    options: Dict[str, Any],
):
    """배치 실행 레코드 생성

    Args:
        batch_id: 배치 ID
        batch_name: 배치 이름
        total_images: 총 이미지 수
        chunk_size: 청크 크기
        initiated_by: 시작한 사용자/시스템
        options: 파이프라인 옵션
    """
    from shared.repository.crud.sync_crud.batch_execution import batch_execution_crud

    with get_db_manager().get_sync_session() as session:
        if not session:
            raise RuntimeError("DB 세션 생성 실패")

        batch_execution_crud.create_batch_execution(
            db=session,
            batch_id=batch_id,
            batch_name=batch_name,
            total_images=total_images,
            chunk_size=chunk_size,
            initiated_by=initiated_by,
            options=options,
        )


def start_batch_execution(batch_id: str):
    """배치 실행 시작 상태로 변경

    Args:
        batch_id: 배치 ID
    """
    from shared.repository.crud.sync_crud.batch_execution import batch_execution_crud

    with get_db_manager().get_sync_session() as session:
        if not session:
            logger.warning("DB 세션 생성 실패 - 상태 업데이트 건너뜀")
            return

        batch_execution = batch_execution_crud.get_by_batch_id(
            session, batch_id=batch_id
        )
        if batch_execution:
            batch_execution.start_execution()
            session.commit()


# ==================== 비동기 버전 헬퍼 함수들 ====================


async def async_create_batch_execution(
    batch_id: str,
    batch_name: str,
    total_images: int,
    chunk_size: int,
    initiated_by: str,
    options: Dict[str, Any],
):
    """배치 실행 레코드 생성 (비동기)

    Args:
        batch_id: 배치 ID
        batch_name: 배치 이름
        total_images: 총 이미지 수
        chunk_size: 청크 크기
        initiated_by: 시작한 사용자/시스템
        options: 파이프라인 옵션
    """
    from shared.repository.crud.async_crud.batch_execution import (
        async_batch_execution_crud,
    )

    async for session in get_db():
        await async_batch_execution_crud.create_batch_execution(
            db=session,
            batch_id=batch_id,
            batch_name=batch_name,
            total_images=total_images,
            chunk_size=chunk_size,
            initiated_by=initiated_by,
            options=options,
        )
        break


async def async_start_batch_execution(batch_id: str):
    """배치 실행 시작 상태로 변경 (비동기)

    Args:
        batch_id: 배치 ID
    """
    from shared.repository.crud.async_crud.batch_execution import (
        async_batch_execution_crud,
    )

    async for session in get_db():
        batch_execution = await async_batch_execution_crud.get_by_batch_id(
            db=session, batch_id=batch_id
        )
        if batch_execution:
            batch_execution.start_execution()
            await async_batch_execution_crud.update_status(
                db=session,
                batch_execution=batch_execution,
                status=ProcessStatus.STARTED,
            )
        else:
            logger.warning(f"BatchExecution을 찾을 수 없음: batch_id={batch_id}")
        break

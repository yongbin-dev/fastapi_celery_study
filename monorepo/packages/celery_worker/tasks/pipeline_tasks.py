"""파이프라인 Celery 태스크

각 스테이지를 Celery 태스크로 래핑하여 비동기 실행 및 재시도 지원
"""

import json
import uuid
from typing import Any, Dict, List

from celery import chain
from celery_app import celery_app
from shared.core.database import get_db_manager

# Redis 서비스 인스턴스
# 로깅 설정
from shared.core.logging import get_logger
from shared.pipeline.context import PipelineContext
from shared.pipeline.exceptions import RetryableError
from shared.service.redis_service import get_redis_service

from .stages.llm_stage import LLMStage
from .stages.ocr_stage import OCRStage

logger = get_logger(__name__)

redis_service = get_redis_service().get_redis_client()


# Context 저장/로드 헬퍼
def save_context_to_redis(context: PipelineContext, ttl: int = 86400) -> None:
    """Context를 Redis에 저장 (24시간 TTL)

    Args:
        context: 파이프라인 컨텍스트
        ttl: Time To Live (초)
    """
    key = f"pipeline:context:{context.context_id}"
    redis_service.set(key, context.model_dump_json(), ex=ttl)


def load_context_from_redis(context_id: str) -> PipelineContext:
    """Redis에서 Context 로드

    Args:
        context_id: 컨텍스트 ID

    Returns:
        파이프라인 컨텍스트

    Raises:
        ValueError: Context가 Redis에 없을 때
    """
    key = f"pipeline:context:{context_id}"
    data = redis_service.get(key)
    if not data:
        raise ValueError(f"Context {context_id} not found in Redis")

    # JSON 문자열을 딕셔너리로 파싱
    if isinstance(data, str):
        data_dict = json.loads(data)
    else:
        data_dict = data

    return PipelineContext(**data_dict)  # type: ignore

# 각 단계별 Celery 태스크
@celery_app.task(
    bind=True,
    name="pipeline.ocr_stage",
    max_retries=3,
    autoretry_for=(ConnectionError, TimeoutError, RetryableError),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
)
def ocr_stage_task(self, context_id: str) -> str:
    """OCR 단계 실행

    Args:
        self: Celery task instance
        context_id: 컨텍스트 ID

    Returns:
        컨텍스트 ID (다음 단계로 전달)
    """
    # Redis에서 context 로드
    context = load_context_from_redis(context_id)

    # OCR 실행 (동기로 실행 - run_sync 필요 없음, async 함수를 직접 호출)
    import asyncio

    stage = OCRStage()
    context = asyncio.run(stage.run(context))

    # Redis에 저장
    save_context_to_redis(context)

    return context_id  # 다음 단계로 전달


@celery_app.task(
    bind=True,
    name="pipeline.llm_stage",
    max_retries=3,
    autoretry_for=(ConnectionError, TimeoutError, RetryableError),
    retry_backoff=True,
    retry_backoff_max=600,
)
def llm_stage_task(self, context_id: str) -> str:
    """LLM 분석 단계 실행

    Args:
        self: Celery task instance
        context_id: 컨텍스트 ID

    Returns:
        컨텍스트 ID
    """
    context = load_context_from_redis(context_id)

    import asyncio

    stage = LLMStage()
    context = asyncio.run(stage.run(context))

    save_context_to_redis(context)
    return context_id


@celery_app.task(bind=True, name="tasks.start_pipeline")
def start_pipeline_task(
    self, file_path: str,  options: Dict[str, Any]
) -> str:
    """파이프라인 시작 (Celery Task)"""
    return start_pipeline(file_path, options)


# 파이프라인 시작 함수
def start_pipeline(
    file_path: str,  options: Dict[str, Any]
) -> str:
    """CR 추출 파이프라인 시작

    Args:
        file_path: 입력 파일 경로
        options: 파이프라인 옵션

    Returns:
        context_id: 파이프라인 실행 추적 ID (=chain_id)
    """
    # 1. Chain ID 생성 (context_id와 동일)
    chain_id = str(uuid.uuid4())

    # 2. DB에 ChainExecution 생성
    from shared.repository.crud.sync_crud.chain_execution import chain_execution_crud


    with get_db_manager().get_sync_session() as session:
        if not session:
            raise RuntimeError("DB 세션 생성 실패")

        chain_execution_crud.create_chain_execution(
            db=session,
            chain_id=chain_id,
            chain_name="workflow",
            total_tasks=2,  # OCR, LLM
            initiated_by="api_server",
            input_data={"file_path": file_path, "options": options},
        )


    # 3. Context 생성 및 Redis 저장
    context = PipelineContext(
        context_id=chain_id,
        input_file_path=file_path,
        public_file_path="",
        options=options,
    )

    save_context_to_redis(context)

    # 4. Celery chain으로 단계 연결
    workflow = chain(
        ocr_stage_task.s(context.context_id),
        llm_stage_task.s(),
    )

    # 5. 비동기 실행
    workflow.apply_async()

    return context.context_id


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
    file_paths: List[str],
    public_file_paths: List[str],
    options: Dict[str, Any],
) -> Dict[str, Any]:
    """청크 단위 파이프라인 처리
    Args:
        self: Celery task instance
        batch_id: 배치 ID
        chunk_index: 청크 인덱스
        file_paths: 이미지 파일 경로 목록
        public_file_paths: 공개 파일 경로 목록
        options: 파이프라인 옵션
    Returns:
        청크 처리 결과 (성공/실패 이미지 수)
    """
    from shared.repository.crud.sync_crud.batch_execution import batch_execution_crud

    logger.info(
        f"청크 처리 시작: batch_id={batch_id}, chunk={chunk_index}, "
        f"images={len(file_paths)}"
    )

    completed_count = 0
    failed_count = 0
    results = []

    # 각 이미지에 대해 개별 파이프라인 실행
    for idx, file_path in enumerate(file_paths):
        try:
            # 개별 파이프라인 실행
            context_id = start_pipeline(file_path, options)

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
    file_paths: List[str],
    options: Dict[str, Any],
    chunk_size: int = 10,
    initiated_by: str = "api_server",
) -> str:
    """배치 파이프라인 시작
    Args:
        batch_name: 배치 이름
        file_paths: 처리할 이미지 파일 경로 목록
        public_file_paths: 공개 파일 경로 목록
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
            total_images=len(file_paths),
            chunk_size=chunk_size,
            initiated_by=initiated_by,
            input_data={
                "file_paths": file_paths,
            },
            options=options,
        )

    # 3. 파일 경로를 청크로 분할
    chunks = []
    for i in range(0, len(file_paths), chunk_size):
        chunk_files = file_paths[i : i + chunk_size]
        chunks.append(chunk_files)

    logger.info(
        f"배치 파이프라인 시작: batch_id={batch_id}, "
        f"total_images={len(file_paths)}, chunks={len(chunks)}"
    )

    # 4. 각 청크를 독립적인 태스크로 실행
    # group을 사용하여 병렬 처리
    from celery import group

    chunk_tasks = group(
        process_chunk_task.s(
            batch_id=batch_id,
            chunk_index=idx,
            file_paths=chunk_files,
            options=options,
        )
        for idx, chunk_files in enumerate(chunks)
    )

    # 5. 배치 시작 상태로 변경
    with get_db_manager().get_sync_session() as session:
        if session:
            batch_execution = batch_execution_crud.get_by_batch_id(
                session, batch_id=batch_id
            )
            if batch_execution:
                batch_execution.start_execution()
                session.commit()

    # 6. 비동기 실행
    chunk_tasks.apply_async()

    logger.info(f"배치 태스크 시작됨: batch_id={batch_id}")

    return batch_id

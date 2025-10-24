"""파이프라인 Celery 태스크

각 스테이지를 Celery 태스크로 래핑하여 비동기 실행 및 재시도 지원
"""

import json
import uuid
from typing import Any, Dict

from celery import chain
from celery_app import celery_app
from shared.pipeline.context import PipelineContext
from shared.pipeline.exceptions import RetryableError
from shared.service.redis_service import get_redis_service

from .stages.llm_stage import LLMStage
from .stages.ocr_stage import OCRStage

# Redis 서비스 인스턴스
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


def save_final_result_to_db(context: PipelineContext) -> None:
    """최종 결과를 DB에 저장

    Args:
        context: 파이프라인 컨텍스트
    """
    # TODO: DB에 최종 결과 저장 로직 구현
    # from shared.repository.crud.async_crud import PipelineRunCRUD
    # await PipelineRunCRUD.create(...)
    _ = context


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
def start_pipeline_task(self, file_path: str, options: Dict[str, Any]) -> str:
    """파이프라인 시작 (Celery Task)"""
    return start_pipeline(file_path, options)


# 파이프라인 시작 함수
def start_pipeline(file_path: str, options: Dict[str, Any]) -> str:
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
    from shared.core.database import get_db_manager
    from shared.repository.crud.sync_crud.chain_execution import chain_execution_crud

    try:

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
    finally:
        pass
        # db.close()

    # 3. Context 생성 및 Redis 저장
    context = PipelineContext(
        context_id=chain_id, input_file_path=file_path, options=options
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

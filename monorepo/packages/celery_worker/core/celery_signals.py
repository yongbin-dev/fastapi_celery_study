"""Celery Signals 핸들러

Task 실행 생명주기를 자동으로 DB에 기록
"""

import asyncio
from datetime import datetime

from celery import signals
from shared.core.database import get_db_manager
from shared.core.logging import get_logger
from shared.pipeline.context import PipelineContext
from shared.repository.crud.sync_crud.chain_execution import (
    chain_execution_crud,
)
from shared.repository.crud.sync_crud.task_log import task_log_crud
from shared.schemas.chain_execution import ChainExecutionResponse
from shared.schemas.enums import ProcessStatus

logger = get_logger(__name__)

# Task 이름 → Stage 매핑
TASK_STAGE_MAP = {
    "pipeline.ocr_stage": "OCRStage",
    "pipeline.llm_stage": "LLMStage",
}


@signals.task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, args=None, **kwargs):
    """Task 시작 전 - TaskLog 생성

    Args:
        sender: Task instance
        task_id: Celery task UUID
        task: Task instance
        args: Task arguments
        **kwargs: Additional kwargs
    """
    # Pipeline task인지 확인
    if task_id is None or task is None or task.name not in TASK_STAGE_MAP:
        return

    # context_id 추출 (첫 번째 인자)
    if not args or len(args) == 0:
        return

    context = args[0]

    # PipelineContext 객체 또는 딕셔너리 처리
    if isinstance(context, PipelineContext):
        chain_id = context.chain_execution_id
        batch_id = context.batch_id
    elif isinstance(context, dict):
        chain_id = context.get("chain_execution_id") or context.get("chain_id")
        batch_id = context.get("batch_id")
    else:
        logger.warning(
            f"Task {task.name}의 첫 번째 인자가 PipelineContext 또는 딕셔너리가 아닙니다. "
            f"type: {type(context)}"
        )
        return

    if not chain_id:
        logger.warning(f"Task {task.name}의 context에 chain_execution_id가 없습니다.")
        return

    logger.info(f"prerun context : {batch_id} , {chain_id} , {task_id}")
    with get_db_manager().get_sync_session() as session:
        if not session:
            raise RuntimeError("DB 세션 생성 실패")
        # ChainExecution 조회 (chain_id는 DB의 정수 ID)
        chain_exec = chain_execution_crud.get(session, id=chain_id)

        if chain_exec is not None:
            chain_exec_resp = ChainExecutionResponse.model_validate(chain_exec)
            # TaskLog가 이미 있는지 확인 (재시도 시 중복 생성 방지)
            task_log = task_log_crud.get_by_celery_task_id(
                session, celery_task_id=task_id
            )

            if task_log:
                # 이미 존재하면 상태 및 재시도 횟수 업데이트
                task_log.status = ProcessStatus.STARTED.value
                task_log.retries = task.request.retries
                task_log.started_at = datetime.now()
                session.add(task_log)
                session.commit()
                session.refresh(task_log)
            else:
                # 없으면 새로 생성
                task_log_crud.create_task_log(
                    db=session,
                    celery_task_id=task_id,
                    task_name=task.name,
                    status=ProcessStatus.STARTED.value,
                    chain_execution_id=chain_exec_resp.id,
                )

            if chain_exec_resp.status == ProcessStatus.PENDING.value:
                chain_exec.start_execution()


@signals.task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, **kwargs):
    """Task 완료 후 - TaskLog 업데이트

    Args:
        sender: Task instance
        task_id: Celery task UUID
        task: Task instance
        **kwargs: Additional kwargs
    """
    # Pipeline task인지 확인

    if task is None or task_id is None or task.name not in TASK_STAGE_MAP:
        return

    with get_db_manager().get_sync_session() as session:
        if not session:
            raise RuntimeError("DB 세션 생성 실패")

        # TaskLog 조회 및 업데이트
        task_log = task_log_crud.get_by_celery_task_id(session, celery_task_id=task_id)

        if task_log:
            task_log_crud.update_status(
                db=session, task_log=task_log, status=ProcessStatus.SUCCESS.value
            )


@signals.task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, **kwargs):
    """Task 실패 시 - 에러 기록

    Args:
        sender: Task instance
        task_id: Celery task UUID
        exception: Exception instance
        **kwargs: Additional kwargs
    """
    # Pipeline task인지 확인
    if sender is None or task_id is None or sender.name not in TASK_STAGE_MAP:
        return

    # DB 업데이트
    with get_db_manager().get_sync_session() as session:
        if not session:
            raise RuntimeError("DB 세션 생성 실패")
        # TaskLog 조회 및 업데이트
        task_log = task_log_crud.get_by_celery_task_id(session, celery_task_id=task_id)

        if task_log:
            task_log_crud.update_status(
                db=session,
                task_log=task_log,
                status=ProcessStatus.FAILURE.value,
                error=str(exception)[:500],  # 500자 제한
            )

            # ChainExecution 실패 카운트 증가
            if task_log.chain_execution:
                # Chain 전체를 실패로 마킹
                task_log.chain_execution.complete_execution(
                    success=False,
                    error_message=f"Task {sender.name} failed: {str(exception)}",
                )


@signals.task_retry.connect
def task_retry_handler(sender=None, task_id=None, **kwargs):
    """Task 재시도 시 - 재시도 카운트 증가

    Args:
        sender: Task instance
        task_id: Celery task UUID
        **kwargs: Additional kwargs
    """
    # Pipeline task인지 확인
    if sender is None or task_id is None or sender.name not in TASK_STAGE_MAP:
        return

    with get_db_manager().get_sync_session() as session:
        if not session:
            raise RuntimeError("DB 세션 생성 실패")

        task_log = task_log_crud.get_by_celery_task_id(session, celery_task_id=task_id)

        if task_log:
            task_log_crud.update_status(
                db=session,
                task_log=task_log,
                status=ProcessStatus.RETRY.value,
            )


@signals.worker_shutdown.connect
def worker_shutdown_handler(sender=None, **kwargs):
    """워커 종료 시 - DB 연결 풀 정리

    Args:
        sender: Worker instance
        **kwargs: Additional kwargs
    """
    logger.info("🛑 Celery 워커 종료 - DB 연결 풀 정리 시작")

    try:
        db_manager = get_db_manager()

        # 동기 엔진 정리 (즉시 실행 가능)
        logger.info("동기 엔진 dispose 시작...")
        db_manager.sync_engine.dispose()
        logger.info("✅ 동기 엔진 dispose 완료")

        # 비동기 엔진 정리
        logger.info("비동기 엔진 dispose 시작...")
        try:
            # 현재 이벤트 루프 가져오기 또는 새로 생성
            try:
                loop = asyncio.get_running_loop()
                # 이미 실행 중인 루프가 있으면 태스크 생성
                logger.warning("실행 중인 이벤트 루프 감지 - 태스크로 dispose 예약")
                asyncio.create_task(db_manager.async_engine.dispose())
                asyncio.create_task(db_manager.health_check_engine.dispose())
            except RuntimeError:
                # 실행 중인 루프가 없으면 새 루프로 실행
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(db_manager.async_engine.dispose())
                    loop.run_until_complete(db_manager.health_check_engine.dispose())
                finally:
                    loop.close()

            logger.info("✅ 비동기 엔진 dispose 완료")
        except Exception as e:
            logger.error(f"❌ 비동기 엔진 정리 중 오류 발생: {e}")
            # 비동기 정리 실패해도 계속 진행

        logger.info("✅ DB 연결 풀 정리 완료")

    except Exception as e:
        logger.error(f"❌ DB 연결 풀 정리 실패: {e}")
        # 종료 시그널이므로 예외를 발생시키지 않음

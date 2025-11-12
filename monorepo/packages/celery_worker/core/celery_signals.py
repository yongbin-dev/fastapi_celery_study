"""Celery Signals 핸들러

Task 실행 생명주기를 자동으로 DB에 기록
"""

from datetime import datetime

from celery import signals
from shared.core.database import get_db_manager
from shared.core.logging import get_logger
from shared.repository.crud.sync_crud.chain_execution import (
    chain_execution_crud,
)
from shared.repository.crud.sync_crud.task_log import task_log_crud
from shared.schemas.chain_execution import ChainExecutionResponse
from shared.schemas.enums import ProcessStatus

logger = get_logger(__name__)

# Task 이름 → Stage 매핑
TASK_STAGE_MAP = {
    # "pipeline.ocr_stage": "OCRStage",
    # "pipeline.llm_stage": "LLMStage",
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

    # context가 딕셔너리인지 확인
    if not isinstance(context, dict):
        logger.warning(
            f"Task {task.name}의 첫 번째 인자가 딕셔너리가 아닙니다. "
            f"type: {type(context)}, value: {context}"
        )
        return

    chain_id = context.get("chain_id")
    batch_id = context.get("batch_id")

    if not chain_id:
        logger.warning(
            f"Task {task.name}의 context에 chain_id가 없습니다. context: {context}"
        )
        return

    logger.info(f"prerun context : {batch_id} , {chain_id} , {task_id}")
    with get_db_manager().get_sync_session() as session:
        if not session:
            raise RuntimeError("DB 세션 생성 실패")
        # ChainExecution 조회 (context_id가 chain_id)
        chain_exec = chain_execution_crud.get_by_chain_id(session, chain_id=chain_id)

        if chain_exec is not None:
            chain_exec_resp = ChainExecutionResponse.model_validate(chain_exec)
            # TaskLog가 이미 있는지 확인 (재시도 시 중복 생성 방지)
            task_log = task_log_crud.get_by_task_id(session, task_id=task_id)

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
                    task_id=task_id,
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
        task_log = task_log_crud.get_by_task_id(session, task_id=task_id)

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
        task_log = task_log_crud.get_by_task_id(session, task_id=task_id)

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

        task_log = task_log_crud.get_by_task_id(session, task_id=task_id)

        if task_log:
            task_log_crud.update_status(
                db=session,
                task_log=task_log,
                status=ProcessStatus.RETRY.value,
            )

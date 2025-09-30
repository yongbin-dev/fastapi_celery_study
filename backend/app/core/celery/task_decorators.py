# app/utils/task_decorators.py

import json
import time
from functools import wraps
from typing import Any, Callable, Dict, Optional, TypeVar

try:
    from typing import ParamSpec
except ImportError:
    from typing_extensions import ParamSpec

from orchestration.schemas.enums import ProcessStatus
from orchestration.schemas.pipeline import StageResult

from app.core.database import get_db_manager
from app.core.logging import get_logger
from app.repository.crud import (
    chain_execution as chain_execution_crud,
)
from app.repository.crud import (
    task_log as task_log_crud,
)

logger = get_logger(__name__)


P = ParamSpec("P")
T = TypeVar("T")


def _handle_chain_execution(
    session, chain_id: str, is_pipeline: bool, task_name: str
) -> Optional[int]:
    """ChainExecution 처리 헬퍼"""
    try:
        chain_exec = chain_execution_crud.get_by_chain_id(session, chain_id=chain_id)

        if not chain_exec and is_pipeline:
            # Pipeline task인 경우 ChainExecution 자동 생성
            chain_exec = chain_execution_crud.create_chain_execution(
                session,
                chain_id=chain_id,
                chain_name="pipeline_workflow",
                total_tasks=4,
                initiated_by="system",
            )
            logger.info(f"새 ChainExecution 생성: {chain_id}")

        if chain_exec:
            # 상태를 RUNNING으로 업데이트
            if str(chain_exec.status) != "RUNNING":
                chain_execution_crud.update_status(
                    session, chain_execution=chain_exec, status=ProcessStatus.RUNNING
                )
                logger.info(f"ChainExecution 상태 업데이트: {chain_id} -> RUNNING")

            return chain_exec.id  # type: ignore

        return None

    except Exception as e:
        logger.error(f"ChainExecution 처리 오류: {e}", exc_info=True)
        return None


def _update_chain_progress(session, chain_execution_id: int, success: bool):
    """ChainExecution 진행률 업데이트 헬퍼"""
    try:
        chain_exec = chain_execution_crud.get(session, id=chain_execution_id)
        if chain_exec:
            if success:
                chain_execution_crud.increment_completed_tasks(
                    session, chain_execution=chain_exec
                )
                logger.info(f"ChainExecution 완료 작업 증가: {chain_exec.chain_id}")
            else:
                chain_execution_crud.increment_failed_tasks(
                    session, chain_execution=chain_exec
                )
                logger.info(f"ChainExecution 실패 작업 증가: {chain_exec.chain_id}")
    except Exception as e:
        logger.error(f"ChainExecution 진행률 업데이트 오류: {e}", exc_info=True)


def task_logger(auto_chain: bool = False, is_pipeline: bool = False):
    """
    TaskLog 자동 처리 데코레이터

    Args:
        auto_chain: chain_id가 있을 때 자동으로 ChainExecution과 연결
        is_pipeline: Pipeline task 여부 (chain_id 필수)
    """

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
            task_id = self.request.id
            task_name = self.name

            # chain_id 추출
            chain_id = None
            if args and len(args) > 0:
                # 첫 번째 인자가 딕셔너리이고 chain_id 키가 있는 경우 (stage2~4)
                if isinstance(args[0], dict) and "chain_id" in args[0]:
                    chain_id = str(args[0]["chain_id"])
                # 첫 번째 인자가 문자열인 경우 (stage1)
                elif isinstance(args[0], str):
                    chain_id = str(args[0])

            if not chain_id and "chain_id" in kwargs:
                chain_id = kwargs.get("chain_id")

            # Pipeline task는 chain_id 필수
            if is_pipeline and not chain_id:
                error_msg = (
                    f"Pipeline task에는 chain_id가 필수입니다. task: {task_name}"
                )
                logger.error(error_msg)
                raise ValueError(error_msg)

            # TaskLog 처리
            with get_db_manager().get_sync_session() as session:
                if not session:
                    logger.error("DB 세션 생성 실패")
                    raise RuntimeError("DB 세션 생성 실패")

                try:
                    # ChainExecution 처리
                    chain_execution_id = None
                    if chain_id and auto_chain:
                        chain_execution_id = _handle_chain_execution(
                            session, chain_id, is_pipeline, task_name
                        )

                    # TaskLog 생성
                    task_log = task_log_crud.create_task_log(
                        session,
                        task_id=task_id,
                        task_name=task_name,
                        status="STARTED",
                        args=json.dumps(args, ensure_ascii=False) if args else None,
                        kwargs=(
                            json.dumps(kwargs, ensure_ascii=False) if kwargs else None
                        ),
                        chain_execution_id=chain_execution_id,
                    )

                    logger.info(f"TaskLog 생성: {task_id} (chain: {chain_id})")

                    # 실제 함수 실행
                    start_time = time.time()
                    try:
                        result = func(self, *args, **kwargs)  # type: ignore

                        # 성공 처리
                        execution_time = time.time() - start_time
                        task_log_crud.update_status(
                            session,
                            task_log=task_log,
                            status="SUCCESS",
                            result=(
                                json.dumps(result, ensure_ascii=False)
                                if result
                                else None
                            ),
                        )

                        # ChainExecution 진행률 업데이트
                        if chain_execution_id and is_pipeline:
                            _update_chain_progress(
                                session, chain_execution_id, success=True
                            )

                        logger.info(f"Task 성공: {task_id} ({execution_time:.2f}s)")
                        return result

                    except Exception as e:
                        # 실패 처리
                        execution_time = time.time() - start_time
                        task_log_crud.update_status(
                            session,
                            task_log=task_log,
                            status="FAILURE",
                            error=str(e),
                        )

                        # ChainExecution 실패 카운트 업데이트
                        if chain_execution_id and is_pipeline:
                            _update_chain_progress(
                                session, chain_execution_id, success=False
                            )

                        logger.error(
                            f"Task 실패: {task_id} ({execution_time:.2f}s) - {e}"
                        )
                        raise

                except Exception as e:
                    logger.error(f"TaskLog 처리 오류: {e}", exc_info=True)
                    # TaskLog 처리 실패해도 원본 함수는 실행
                    return func(self, *args, **kwargs)  # type: ignore

        return wrapper

    return decorator


def create_stage_result(
    chain_id: str,
    stage: int,
    result_status: ProcessStatus,
    data: Dict[str, Any],
    execution_time: float,
) -> Dict[str, Any]:
    """단계 결과 객체 생성 헬퍼 함수"""
    return StageResult(
        chain_id=chain_id,
        stage=stage,
        result=result_status,
        data=data,
        execution_time=execution_time,
        success=True,
        error_message="",
    ).model_dump()

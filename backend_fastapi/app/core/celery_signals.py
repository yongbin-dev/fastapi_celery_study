# app/core/celery_signals.py

import asyncio
import logging
import threading
from contextlib import asynccontextmanager
from typing import Any, Generator, Optional

from celery import signals, Task
from celery.result import EagerResult
from sqlalchemy.orm import sessionmaker, selectinload
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from app.models.pipeline_execution import PipelineExecution
from app.models.pipeline_stage import PipelineStage

logger = logging.getLogger(__name__)

# --- 스레드-안전 DB 초기화 로직 ---

# 각 스레드가 자신만의 엔진과 세션메이커를 갖도록 스레드-로컬 저장소 사용
thread_local = threading.local()

def get_thread_safe_session_maker() -> sessionmaker:
    """현재 스레드에 대한 세션 메이커를 반환하거나 새로 생성합니다."""
    if not hasattr(thread_local, "session_maker"):
        logger.info(f"[DB INIT] Creating new engine and session maker for thread {threading.get_ident()}.")
        from app.core.config import settings
        try:
            engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True, echo=False)
            thread_local.session_maker = sessionmaker(
                bind=engine, class_=AsyncSession, expire_on_commit=False
            )
        except Exception as e:
            logger.error(f"[DB INIT] ❌ Failed to create engine/session for thread {threading.get_ident()}: {e}", exc_info=True)
            raise
    return thread_local.session_maker


@asynccontextmanager
async def get_async_db_session() -> Generator[AsyncSession, None, None]:
    """스레드에 안전한 비동기 데이터베이스 세션을 제공하는 컨텍스트 관리자."""
    session_maker = get_thread_safe_session_maker()
    db: Optional[AsyncSession] = None
    try:
        db = session_maker()
        yield db
    except Exception as e:
        logger.error(f"[DB SESSION] Error during database session in thread {threading.get_ident()}: {e}", exc_info=True)
        if db:
            await db.rollback()
        raise
    finally:
        if db:
            await db.close()


def run_async_in_sync(coro):
    """동기 컨텍스트에서 비동기 코루틴을 실행하고 결과를 반환합니다."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


# --- 비동기 헬퍼 함수 ---

async def _handle_prerun(task: Task):
    """prerun 핸들러의 모든 비동기 로직을 포함하는 단일 진입점"""
    # 첫 태스크인 경우, 초기 레코드 생성
    if task.request.id == task.request.root_id:
        await _create_initial_pipeline_records(task)
    
    # 현재 스테이지 상태를 STARTED로 업데이트
    await _update_stage_status(task, "STARTED")


async def _create_initial_pipeline_records(task: Task):
    """체인의 첫 태스크일 때 PipelineExecution과 모든 Stage 레코드를 생성"""
    root_id = task.request.root_id
    logger.info(f"[_create_initial_pipeline_records] Triggered for task {task.request.id} with root_id {root_id}.")

    if not task.request.chain:
        logger.info(f"[_create_initial_pipeline_records] Task {task.request.id} has no chain. Skipping.")
        return

    logger.info(f"[_create_initial_pipeline_records] Chain detected. Proceeding to create records for root_id {root_id}.")
    async with get_async_db_session() as db:
        try:
            existing = await db.execute(select(PipelineExecution).filter_by(execution_id=root_id))
            if existing.scalars().first():
                logger.warning(f"[_create_initial_pipeline_records] PipelineExecution for {root_id} already exists. Skipping creation.")
                return

            logger.info(f"[_create_initial_pipeline_records] Creating new PipelineExecution for {root_id}.")
            execution = PipelineExecution(execution_id=root_id, status="STARTED", overall_progress=0)
            db.add(execution)
            await db.flush()

            all_stage_names = [task.name] + [t['task'] for t in task.request.chain]
            logger.info(f"[_create_initial_pipeline_records] Creating {len(all_stage_names)} PENDING stages.")
            for i, stage_name in enumerate(all_stage_names, 1):
                stage = PipelineStage(
                    pipeline_execution_id=execution.id,
                    stage_number=i,
                    stage_name=stage_name,
                    status="PENDING",
                    progress=0
                )
                db.add(stage)
            
            await db.commit()
            logger.info(f"[_create_initial_pipeline_records] ✅ Successfully committed PipelineExecution and Stages for {root_id}.")

        except Exception as e:
            logger.error(f"[_create_initial_pipeline_records] ❌ Error creating records for {root_id}: {e}", exc_info=True)
            await db.rollback()


async def _update_stage_status(task: Task, status: str, error_info: Optional[str] = None):
    """특정 스테이지의 상태를 업데이트"""
    root_id = task.request.root_id
    task_name = task.name
    logger.info(f"[_update_stage_status] Triggered for task {task.request.id} ({task_name}) with status {status}.")

    if not root_id:
        logger.warning(f"[_update_stage_status] Task {task.request.id} is not part of a chain (no root_id). Skipping update.")
        return

    async with get_async_db_session() as db:
        try:
            query = select(PipelineExecution).options(selectinload(PipelineExecution.stages)).filter(PipelineExecution.execution_id == root_id)
            result = await db.execute(query)
            execution = result.scalars().first()

            if not execution:
                logger.error(f"[_update_stage_status] ❌ PipelineExecution NOT FOUND for root_id {root_id}. Cannot update status.")
                return

            logger.info(f"[_update_stage_status] Found PipelineExecution {root_id}. Searching for stage {task_name}.")
            target_stage = next((s for s in execution.stages if s.stage_name == task_name), None)

            if not target_stage:
                logger.error(f"[_update_stage_status] ❌ PipelineStage NOT FOUND for task {task_name} in execution {root_id}. Cannot update status.")
                return

            logger.info(f"[_update_stage_status] Found stage {target_stage.stage_number}. Updating status to {status}.")
            target_stage.status = status
            if status == "STARTED":
                target_stage.started_at = datetime.utcnow()
                execution.status = "PROGRESS"
                execution.current_step = target_stage.stage_number
            elif status in ["SUCCESS", "FAILURE"]:
                target_stage.completed_at = datetime.utcnow()
                if status == "SUCCESS":
                    target_stage.progress = 100
                else: # FAILURE
                    execution.status = "FAILURE"
                    execution.error_traceback = error_info
                    target_stage.error_message = error_info

            completed_stages = sum(1 for s in execution.stages if s.status == "SUCCESS")
            total_stages = len(execution.stages)
            if total_stages > 0:
                execution.overall_progress = int((completed_stages / total_stages) * 100)
                if completed_stages == total_stages:
                    execution.status = "SUCCESS"
            
            await db.commit()
            logger.info(f"[_update_stage_status] ✅ Successfully committed status {status} for stage {target_stage.stage_number} in {root_id}.")

        except Exception as e:
            logger.error(f"[_update_stage_status] ❌ Error updating stage status for {task_name} in {root_id}: {e}", exc_info=True)
            await db.rollback()


# --- 시그널 핸들러 ---

@signals.task_prerun.connect(weak=False)
def task_prerun_handler(task: Task, **kwargs: Any):
    logger.debug(f"[task_prerun] Received for task: {task.name}[{task.request.id}]")
    if not hasattr(task, 'request') or isinstance(task.request, EagerResult):
        return
    
    run_async_in_sync(_handle_prerun(task))


@signals.task_success.connect(weak=False)
def task_success_handler(sender: Task, **kwargs: Any):
    logger.info(f"[task_success] Received for task: {sender.name}[{sender.request.id}]")
    if not hasattr(sender, 'request') or isinstance(sender.request, EagerResult):
        return
    run_async_in_sync(_update_stage_status(sender, "SUCCESS"))


@signals.task_failure.connect(weak=False)
def task_failure_handler(sender: Task, einfo: Any, **kwargs: Any):
    logger.error(f"[task_failure] Received for task: {sender.name}[{sender.request.id}]")
    if not hasattr(sender, 'request') or isinstance(sender.request, EagerResult):
        return
    run_async_in_sync(_update_stage_status(sender, "FAILURE", error_info=str(einfo)))


async def _create_initial_pipeline_records(task: "Task"):
    """체인의 첫 태스크일 때 PipelineExecution과 모든 Stage 레코드를 생성"""
    root_id = task.request.root_id
    logger.info(f"[_create_initial_pipeline_records] Triggered for task {task.request.id} with root_id {root_id}.")

    if not task.request.chain:
        logger.info(f"[_create_initial_pipeline_records] Task {task.request.id} has no chain. Skipping.")
        return

    logger.info(f"[_create_initial_pipeline_records] Chain detected. Proceeding to create records for root_id {root_id}.")
    async with get_async_db_session() as db:
        try:
            existing = await db.execute(select(PipelineExecution).filter_by(execution_id=root_id))
            if existing.scalars().first():
                logger.warning(f"[_create_initial_pipeline_records] PipelineExecution for {root_id} already exists. Skipping creation.")
                return

            logger.info(f"[_create_initial_pipeline_records] Creating new PipelineExecution for {root_id}.")
            execution = PipelineExecution(execution_id=root_id, status="STARTED", overall_progress=0)
            db.add(execution)
            await db.flush()

            all_stage_names = [task.name] + [t['task'] for t in task.request.chain]
            logger.info(f"[_create_initial_pipeline_records] Creating {len(all_stage_names)} PENDING stages.")
            for i, stage_name in enumerate(all_stage_names, 1):
                stage = PipelineStage(
                    pipeline_execution_id=execution.id,
                    stage_number=i,
                    stage_name=stage_name,
                    status="PENDING",
                    progress=0
                )
                db.add(stage)
            
            await db.commit()
            logger.info(f"[_create_initial_pipeline_records] ✅ Successfully committed PipelineExecution and Stages for {root_id}.")

        except Exception as e:
            logger.error(f"[_create_initial_pipeline_records] ❌ Error creating records for {root_id}: {e}", exc_info=True)
            await db.rollback()


async def _update_stage_status(task: "Task", status: str, error_info: Optional[str] = None):
    """특정 스테이지의 상태를 업데이트"""
    root_id = task.request.root_id
    task_name = task.name
    logger.info(f"[_update_stage_status] Triggered for task {task.request.id} ({task_name}) with status {status}.")

    if not root_id:
        logger.warning(f"[_update_stage_status] Task {task.request.id} is not part of a chain (no root_id). Skipping update.")
        return

    async with get_async_db_session() as db:
        try:
            query = select(PipelineExecution).options(selectinload(PipelineExecution.stages)).filter(PipelineExecution.execution_id == root_id)
            result = await db.execute(query)
            execution = result.scalars().first()

            if not execution:
                logger.error(f"[_update_stage_status] ❌ PipelineExecution NOT FOUND for root_id {root_id}. Cannot update status.")
                return

            logger.info(f"[_update_stage_status] Found PipelineExecution {root_id}. Searching for stage {task_name}.")
            target_stage = next((s for s in execution.stages if s.stage_name == task_name), None)

            if not target_stage:
                logger.error(f"[_update_stage_status] ❌ PipelineStage NOT FOUND for task {task_name} in execution {root_id}. Cannot update status.")
                return

            logger.info(f"[_update_stage_status] Found stage {target_stage.stage_number}. Updating status to {status}.")
            target_stage.status = status
            if status == "STARTED":
                target_stage.started_at = datetime.utcnow()
                execution.status = "PROGRESS"
                execution.current_step = target_stage.stage_number
            elif status in ["SUCCESS", "FAILURE"]:
                target_stage.completed_at = datetime.utcnow()
                if status == "SUCCESS":
                    target_stage.progress = 100
                else: # FAILURE
                    execution.status = "FAILURE"
                    execution.error_traceback = error_info
                    target_stage.error_message = error_info

            completed_stages = sum(1 for s in execution.stages if s.status == "SUCCESS")
            total_stages = len(execution.stages)
            if total_stages > 0:
                execution.overall_progress = int((completed_stages / total_stages) * 100)
                if completed_stages == total_stages:
                    execution.status = "SUCCESS"
            
            await db.commit()
            logger.info(f"[_update_stage_status] ✅ Successfully committed status {status} for stage {target_stage.stage_number} in {root_id}.")

        except Exception as e:
            logger.error(f"[_update_stage_status] ❌ Error updating stage status for {task_name} in {root_id}: {e}", exc_info=True)
            await db.rollback()


# --- Signal Handlers ---

@signals.task_prerun.connect(weak=False)
def task_prerun_handler(task: "Task", **kwargs: Any) -> None:
    logger.debug(f"[task_prerun] Received for task: {task.name}[{task.request.id}]")
    if not hasattr(task, 'request') or isinstance(task.request, EagerResult):
        return
        
    if task.request.id == task.request.root_id:
        logger.info(f"[task_prerun] First task in chain detected. Creating initial records for {task.request.root_id}.")
        run_async_in_sync(_create_initial_pipeline_records(task))

    logger.info(f"[task_prerun] Updating stage status to STARTED for {task.name}.")
    run_async_in_sync(_update_stage_status(task, "STARTED"))


@signals.task_success.connect(weak=False)
def task_success_handler(sender: "Task", **kwargs: Any) -> None:
    logger.info(f"[task_success] Received for task: {sender.name}[{sender.request.id}]")
    if not hasattr(sender, 'request') or isinstance(sender.request, EagerResult):
        return
    run_async_in_sync(_update_stage_status(sender, "SUCCESS"))


@signals.task_failure.connect(weak=False)
def task_failure_handler(sender: Task, einfo: Any, **kwargs: Any) -> None:
    logger.error(f"[task_failure] Received for task: {sender.name}[{sender.request.id}]")
    if not hasattr(sender, 'request') or isinstance(sender.request, EagerResult):
        return
    run_async_in_sync(_update_stage_status(sender, "FAILURE", error_info=str(einfo)))


@signals.worker_ready.connect(weak=False)
def worker_ready_handler(**kwargs: Any) -> None:
    logger.info("Celery worker is ready.")


@signals.worker_shutdown.connect(weak=False)
def worker_shutdown_handler(**kwargs: Any) -> None:
    logger.info("Celery worker is shutting down.")

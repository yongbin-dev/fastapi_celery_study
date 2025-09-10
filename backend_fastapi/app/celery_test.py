# celery_signals.py
import asyncio
import json
import traceback
from datetime import datetime
from celery import Celery
from celery.signals import (
    task_prerun,
    task_postrun,
    task_success,
    task_failure,
    task_retry,
    task_revoked,
    worker_ready,
    worker_shutdown,
    worker_process_init,
    heartbeat_sent,
    before_task_publish,
    after_task_publish
)
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from database import get_db
from models import (
    TaskLog, TaskMetadata, TaskExecutionHistory, 
    TaskResult, WorkerStatus, QueueStats, TaskDependency
)

app = Celery('tasks', broker='redis://localhost:6379')

# 비동기 실행 헬퍼
def run_async(coro):
    """동기 컨텍스트에서 비동기 함수 실행"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # 이미 실행 중인 루프가 있으면 새 태스크 생성
            task = asyncio.create_task(coro)
            return task
    except RuntimeError:
        pass
    
    # 새 루프 생성
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

# ==================== 작업 발행 시그널 ====================

@before_task_publish.connect
def on_before_task_publish(sender=None, headers=None, body=None, **kwargs):
    """작업이 큐에 발행되기 전"""
    async def create_pending_task():
        task_id = headers.get('id')
        task_name = headers.get('task')
        
        async with get_db() as session:
            # task_logs에 PENDING 상태로 생성
            task_log = TaskLog(
                task_id=task_id,
                task_name=task_name,
                status='PENDING',
                args=json.dumps(body.get('args', [])),
                kwargs=json.dumps(body.get('kwargs', {})),
                retries=0
            )
            session.add(task_log)
            
            # 메타데이터 저장
            metadata = TaskMetadata(
                task_id=task_id,
                queue_name=headers.get('queue', 'default'),
                exchange=headers.get('exchange'),
                routing_key=headers.get('routing_key'),
                priority=headers.get('priority', 0),
                eta=datetime.fromisoformat(headers['eta']) if headers.get('eta') else None,
                expires=datetime.fromisoformat(headers['expires']) if headers.get('expires') else None,
                parent_id=headers.get('parent_id'),
                root_id=headers.get('root_id')
            )
            session.add(metadata)
            await session.commit()
    
    run_async(create_pending_task())

# ==================== 작업 실행 시그널 ====================

@task_prerun.connect
def on_task_prerun(sender=None, task_id=None, task=None, args=None, kwargs=None, **kw):
    """작업 실행 시작"""
    async def update_task_start():
        async with get_db() as session:
            # task_logs 업데이트
            stmt = (
                update(TaskLog)
                .where(TaskLog.task_id == task_id)
                .values(
                    status='STARTED',
                    started_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
            )
            await session.execute(stmt)
            
            # 워커 정보 업데이트 (메타데이터)
            worker_name = sender.request.hostname if hasattr(sender, 'request') else None
            if worker_name:
                stmt = (
                    update(TaskMetadata)
                    .where(TaskMetadata.task_id == task_id)
                    .values(worker_name=worker_name)
                )
                await session.execute(stmt)
            
            # 실행 이력 추가
            result = await session.execute(
                select(TaskLog).where(TaskLog.task_id == task_id)
            )
            task_log = result.scalar_one_or_none()
            
            if task_log:
                execution = TaskExecutionHistory(
                    task_id=task_id,
                    attempt_number=task_log.retries + 1,
                    status='STARTED',
                    started_at=datetime.utcnow()
                )
                session.add(execution)
            
            await session.commit()
    
    run_async(update_task_start())

@task_success.connect
def on_task_success(sender=None, result=None, **kwargs):
    """작업 성공"""
    async def update_task_success():
        task_id = sender.request.id
        
        async with get_db() as session:
            # task_logs 업데이트
            stmt = (
                update(TaskLog)
                .where(TaskLog.task_id == task_id)
                .values(
                    status='SUCCESS',
                    result=json.dumps(result) if result else None,
                    completed_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
            )
            await session.execute(stmt)
            
            # 대용량 결과는 task_results 테이블에 저장
            result_json = json.dumps(result) if result else None
            if result_json and len(result_json) > 1000:  # 1KB 이상
                task_result = TaskResult(
                    task_id=task_id,
                    result_type='json',
                    result_data=result_json,
                    result_size=len(result_json)
                )
                # Upsert 처리
                stmt = insert(TaskResult).values(
                    task_id=task_id,
                    result_type='json',
                    result_data=result_json,
                    result_size=len(result_json)
                ).on_conflict_do_update(
                    index_elements=['task_id'],
                    set_=dict(
                        result_data=result_json,
                        result_size=len(result_json)
                    )
                )
                await session.execute(stmt)
            
            # 실행 이력 업데이트
            stmt = (
                update(TaskExecutionHistory)
                .where(
                    (TaskExecutionHistory.task_id == task_id) &
                    (TaskExecutionHistory.status == 'STARTED')
                )
                .values(
                    status='SUCCESS',
                    completed_at=datetime.utcnow()
                )
            )
            await session.execute(stmt)
            
            # 워커 통계 업데이트
            worker_name = sender.request.hostname
            if worker_name:
                stmt = (
                    update(WorkerStatus)
                    .where(WorkerStatus.worker_name == worker_name)
                    .values(
                        processed_tasks=WorkerStatus.processed_tasks + 1,
                        active_tasks=WorkerStatus.active_tasks - 1
                    )
                )
                await session.execute(stmt)
            
            await session.commit()
    
    run_async(update_task_success())

@task_failure.connect
def on_task_failure(sender=None, task_id=None, exception=None, traceback=None, **kwargs):
    """작업 실패"""
    async def update_task_failure():
        async with get_db() as session:
            # task_logs 업데이트
            error_msg = str(exception)
            tb_str = str(traceback) if traceback else None
            
            stmt = (
                update(TaskLog)
                .where(TaskLog.task_id == task_id)
                .values(
                    status='FAILURE',
                    error=error_msg,
                    completed_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
            )
            await session.execute(stmt)
            
            # 실행 이력 업데이트
            stmt = (
                update(TaskExecutionHistory)
                .where(
                    (TaskExecutionHistory.task_id == task_id) &
                    (TaskExecutionHistory.status == 'STARTED')
                )
                .values(
                    status='FAILURE',
                    error_message=error_msg,
                    traceback=tb_str,
                    completed_at=datetime.utcnow()
                )
            )
            await session.execute(stmt)
            
            # 워커 통계 업데이트
            if hasattr(sender, 'request'):
                worker_name = sender.request.hostname
                if worker_name:
                    stmt = (
                        update(WorkerStatus)
                        .where(WorkerStatus.worker_name == worker_name)
                        .values(
                            failed_tasks=WorkerStatus.failed_tasks + 1,
                            active_tasks=WorkerStatus.active_tasks - 1
                        )
                    )
                    await session.execute(stmt)
            
            await session.commit()
    
    run_async(update_task_failure())

@task_retry.connect
def on_task_retry(sender=None, request=None, reason=None, einfo=None, **kwargs):
    """작업 재시도"""
    async def update_task_retry():
        task_id = request.id
        
        async with get_db() as session:
            # 재시도 횟수 증가
            stmt = (
                update(TaskLog)
                .where(TaskLog.task_id == task_id)
                .values(
                    status='RETRY',
                    retries=TaskLog.retries + 1,
                    error=str(reason),
                    updated_at=datetime.utcnow()
                )
            )
            await session.execute(stmt)
            
            # 실행 이력에 재시도 기록
            result = await session.execute(
                select(TaskLog).where(TaskLog.task_id == task_id)
            )
            task_log = result.scalar_one_or_none()
            
            if task_log:
                execution = TaskExecutionHistory(
                    task_id=task_id,
                    attempt_number=task_log.retries,
                    status='RETRY',
                    error_message=str(reason),
                    traceback=str(einfo) if einfo else None,
                    started_at=datetime.utcnow()
                )
                session.add(execution)
            
            await session.commit()
    
    run_async(update_task_retry())

@task_revoked.connect
def on_task_revoked(sender=None, request=None, terminated=None, **kwargs):
    """작업 취소"""
    async def update_task_revoked():
        task_id = request.id
        
        async with get_db() as session:
            stmt = (
                update(TaskLog)
                .where(TaskLog.task_id == task_id)
                .values(
                    status='REVOKED',
                    error='Task was revoked' + (' (terminated)' if terminated else ''),
                    completed_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
            )
            await session.execute(stmt)
            await session.commit()
    
    run_async(update_task_revoked())

# ==================== 워커 시그널 ====================

@worker_ready.connect
def on_worker_ready(sender=None, **kwargs):
    """워커 시작"""
    async def register_worker():
        worker_name = sender.hostname
        
        async with get_db() as session:
            # Upsert 워커 상태
            stmt = insert(WorkerStatus).values(
                worker_name=worker_name,
                hostname=worker_name.split('@')[1] if '@' in worker_name else worker_name,
                pid=sender.pid if hasattr(sender, 'pid') else None,
                status='ONLINE',
                active_tasks=0,
                processed_tasks=0,
                failed_tasks=0,
                started_at=datetime.utcnow(),
                last_heartbeat=datetime.utcnow()
            ).on_conflict_do_update(
                index_elements=['worker_name'],
                set_=dict(
                    status='ONLINE',
                    started_at=datetime.utcnow(),
                    last_heartbeat=datetime.utcnow(),
                    stopped_at=None
                )
            )
            await session.execute(stmt)
            await session.commit()
    
    run_async(register_worker())

@worker_shutdown.connect
def on_worker_shutdown(sender=None, **kwargs):
    """워커 종료"""
    async def update_worker_offline():
        worker_name = sender.hostname
        
        async with get_db() as session:
            stmt = (
                update(WorkerStatus)
                .where(WorkerStatus.worker_name == worker_name)
                .values(
                    status='OFFLINE',
                    stopped_at=datetime.utcnow(),
                    active_tasks=0
                )
            )
            await session.execute(stmt)
            await session.commit()
    
    run_async(update_worker_offline())

@heartbeat_sent.connect
def on_heartbeat_sent(sender=None, **kwargs):
    """워커 하트비트"""
    async def update_heartbeat():
        # sender는 워커 인스턴스
        for worker_name in sender.state.alive_workers():
            async with get_db() as session:
                stmt = (
                    update(WorkerStatus)
                    .where(WorkerStatus.worker_name == worker_name)
                    .values(
                        last_heartbeat=datetime.utcnow(),
                        status='ONLINE'
                    )
                )
                await session.execute(stmt)
                await session.commit()
    
    run_async(update_heartbeat())

# ==================== 큐 통계 수집 (주기적 태스크) ====================

@app.task
def collect_queue_stats():
    """큐 통계 수집 (크론탭으로 실행)"""
    async def collect_stats():
        from celery import current_app
        inspect = current_app.control.inspect()
        
        # 활성 큐 정보 가져오기
        active_queues = inspect.active_queues()
        stats = inspect.stats()
        
        async with get_db() as session:
            for worker_name, queues in (active_queues or {}).items():
                for queue_info in queues:
                    queue_name = queue_info.get('name', 'default')
                    
                    # 큐별 작업 수 계산 (실제로는 Redis/RabbitMQ API 사용)
                    queue_stat = QueueStats(
                        queue_name=queue_name,
                        pending_tasks=0,  # Redis/RabbitMQ에서 가져와야 함
                        active_tasks=len(inspect.active().get(worker_name, [])),
                        completed_tasks=0,  # 집계 필요
                        failed_tasks=0,  # 집계 필요
                        avg_execution_time=0.0,  # 계산 필요
                        measured_at=datetime.utcnow()
                    )
                    session.add(queue_stat)
            
            await session.commit()
    
    run_async(collect_stats())

# Celery Beat 스케줄 설정
app.conf.beat_schedule = {
    'collect-queue-stats': {
        'task': 'celery_signals.collect_queue_stats',
        'schedule': 60.0,  # 1분마다
    },
}
# celery_signals.py
import json
import time
import psutil
from datetime import timedelta , datetime
from sqlalchemy.orm import Session
from celery.signals import (
    task_prerun,
    task_success,
    task_failure,
    task_retry,
    task_revoked,
    worker_ready,
    worker_shutdown,
    heartbeat_sent,
    before_task_publish,
    worker_process_init
)

from app.core.database import get_db_manager
from .logging import get_logger
from ..models import (
    TaskLog, QueueStats
)
from app.api.v1.crud import (
    chain_execution as chain_execution_crud,
    task_log as task_log_crud,
    task_metadata as task_metadata_crud,
    task_execution_history as task_execution_history_crud
)

# 로거 설정
logger = get_logger(__name__)


def safe_json_dumps(data):
    """안전한 JSON 직렬화"""
    return json.dumps(data, ensure_ascii=False)

def get_worker_name(sender=None):
    """안전하게 워커 이름 가져오기"""
    # 다양한 경로로 hostname 시도
    if hasattr(sender, 'hostname'):
        return sender.hostname
    elif hasattr(sender, 'consumer') and hasattr(sender.consumer, 'hostname'):
        return sender.consumer.hostname
    elif hasattr(sender, 'request') and hasattr(sender.request, 'hostname'):
        return sender.request.hostname
    else:
        # 마지막 대안: 시스템 hostname 사용
        import socket
        return f"celery@{socket.gethostname()}"

def get_chain_id_from_args(args):
    """task args에서 chain_id 추출"""
    if args and len(args) > 0:
        # args[0]이 chain_id인 경우 (UUID 문자열)
        chain_id_str = str(args[0])
        if len(chain_id_str) == 36 and chain_id_str.count('-') == 4:  # UUID 형태 확인
            return chain_id_str
    return None

def get_chain_id_from_kwargs(kwargs):
    """task kwargs에서 chain_id 추출"""
    return kwargs.get('chain_id') if kwargs else None


def extract_stage_number(task_name):
    """task_name에서 stage 번호 추출 (예: app.tasks.stage1_preprocessing -> 1)"""
    if 'stage' in task_name:
        import re
        match = re.search(r'stage(\d+)', task_name)
        if match:
            return int(match.group(1))
    return None


# 작업 관련 신호 처리

@before_task_publish.connect
def task_publish_handler(sender=None, headers=None, body=None, properties=None, **kwargs):
    """작업 발행 전 처리"""
    logger.info(f"🚀 SIGNAL: before_task_publish 수신 - sender: {sender}")
    # 동기 세션 컨텍스트 매니저를 사용하여 세션 관리
    with get_db_manager().get_sync_session() as session:
        if not session:
            logger.error("❌ DB 세션 생성 실패 - before_task_publish")
            return

        if body:
            task_name = body[0] if isinstance(body, (list, tuple)) and len(body) > 0 else None
            task_args = body[1] if isinstance(body, (list, tuple)) and len(body) > 1 else []
            task_kwargs = body[2] if isinstance(body, (list, tuple)) and len(body) > 2 else {}

            # Pipeline task인지 확인
            if task_name and 'stage' in task_name:
                chain_id = get_chain_id_from_args(task_args) or get_chain_id_from_kwargs(task_kwargs)
                if chain_id:
                    logger.info(f"Pipeline task 발행: {task_name}, chain_id: {chain_id}")

                    # ChainExecution이 존재하지 않으면 생성
                    existing_chain = chain_execution_crud.get_by_chain_id(session, chain_id=chain_id)
                    if not existing_chain:
                        chain_execution_crud.create_chain_execution(
                            session,
                            chain_id=chain_id,
                            chain_name="pipeline_workflow",
                            total_tasks=4,
                            initiated_by="system"
                        )
                        logger.info(f"새 ChainExecution 생성: {chain_id}")


@task_prerun.connect
def task_prerun_handler(task_id=None, task=None, args=None, kwargs=None, **kwds):
    """작업 실행 전 처리"""
    logger.info(f"🏃 SIGNAL: task_prerun 수신 - task_id: {task_id}")
    with get_db_manager().get_sync_session() as session:
        if not session:
            logger.error("❌ DB 세션 생성 실패 - task_prerun")
            return

        existing_task = task_log_crud.get_by_task_id(session, task_id=task_id)
        if not existing_task:
            # 새 TaskLog 생성
            task_log_crud.create_task_log(
                session,
                task_id=task_id,
                task_name=task.name if task else "unknown",
                status="STARTED",
                args=safe_json_dumps(args) if args else None,
                kwargs=safe_json_dumps(kwargs) if kwargs else None
            )
            logger.info(f"새 TaskLog 생성: {task_id}")
        else:
            # 기존 TaskLog 상태 업데이트
            task_log_crud.update_status(
                session,
                task_log=existing_task,
                status="STARTED"
            )
            logger.info(f"TaskLog 상태 업데이트: {task_id} -> STARTED")

        # TaskMetadata 생성
        task_metadata_crud.create_task_metadata(
            session,
            task_id=task_id,
            worker_name=get_worker_name() if hasattr(task, 'request') else None,
            queue_name=getattr(task.request, 'delivery_info', {}).get('routing_key', 'default') if hasattr(task, 'request') else 'default',
            priority=getattr(task.request, 'priority', 0) if hasattr(task, 'request') else 0
        )
        logger.info(f"TaskMetadata 생성: {task_id}")

        # TaskExecutionHistory에 시도 기록
        attempt_number = task_execution_history_crud.get_retry_count(session, task_id=task_id) + 1
        task_execution_history_crud.create_attempt(
            session,
            task_id=task_id,
            attempt_number=attempt_number,
            status="STARTED"
        )
        logger.info(f"TaskExecutionHistory 생성: {task_id}, attempt: {attempt_number}")



@task_success.connect
def task_success_handler(sender=None, result=None, **kwargs):
    """작업 성공 처리"""
    task_id = sender.request.id if sender and hasattr(sender, 'request') else None
    logger.info(f"✅ SIGNAL: task_success 수신 - task_id: {task_id}")

    with get_db_manager().get_sync_session() as session:
        if not session:
            logger.error("❌ DB 세션 생성 실패 - task_success")
            return

        if not task_id:
            logger.warning("task_id를 찾을 수 없음")
            return

        # TaskLog 상태 업데이트
        task_log = task_log_crud.get_by_task_id(session, task_id=task_id)
        if task_log:
            task_log_crud.update_status(
                session,
                task_log=task_log,
                status="SUCCESS",
                result=safe_json_dumps(result) if result else None
            )
            logger.info(f"TaskLog 성공 처리: {task_id}")

            # TaskExecutionHistory 완료 처리
            latest_attempt = task_execution_history_crud.get_latest_attempt(session, task_id=task_id)
            if latest_attempt:
                task_execution_history_crud.complete_attempt(
                    session,
                    execution_history=latest_attempt,
                    status="SUCCESS"
                )

            # ChainExecution 업데이트 (pipeline task인 경우)
            if task_log.task_name and 'stage' in task_log.task_name:
                # result에서 chain_id 추출
                chain_id = None
                if isinstance(result, dict) and 'chain_id' in result:
                    chain_id = result['chain_id']

                if chain_id:
                    chain_exec = chain_execution_crud.get_by_chain_id(session, chain_id=chain_id)
                    if chain_exec:
                        chain_execution_crud.increment_completed_tasks(session, chain_execution=chain_exec)

        logger.info(f"작업 성공 처리 완료: {task_id}")



@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, traceback=None, einfo=None, **kwargs):
    """작업 실패 처리"""
    logger.info(f"❌ SIGNAL: task_failure 수신 - task_id: {task_id}")
    with get_db_manager().get_sync_session() as session:
        if not session:
            logger.error("❌ DB 세션 생성 실패 - task_failure")
            return

        if not task_id:
            logger.warning("task_id를 찾을 수 없음")
            return

        error_message = str(exception) if exception else "Unknown error"
        traceback_str = str(traceback) if traceback else None

        # TaskLog 상태 업데이트
        task_log = task_log_crud.get_by_task_id(session, task_id=task_id)
        if task_log:
            task_log_crud.update_status(
                session,
                task_log=task_log,
                status="FAILURE",
                error=error_message
            )
            logger.info(f"TaskLog 실패 처리: {task_id}")

            # TaskExecutionHistory 완료 처리
            latest_attempt = task_execution_history_crud.get_latest_attempt(session, task_id=task_id)
            if latest_attempt:
                task_execution_history_crud.complete_attempt(
                    session,
                    execution_history=latest_attempt,
                    status="FAILURE",
                    error_message=error_message,
                    traceback=traceback_str
                )

            # ChainExecution 업데이트 (pipeline task인 경우)
            if task_log.task_name and 'stage' in task_log.task_name:
                # task args/kwargs에서 chain_id 추출 시도
                chain_id = None
                if task_log.kwargs:
                    try:
                        kwargs_dict = json.loads(task_log.kwargs)
                        chain_id = kwargs_dict.get('chain_id')
                    except:
                        pass

                if not chain_id and task_log.args:
                    try:
                        args_list = json.loads(task_log.args)
                        if args_list:
                            chain_id = get_chain_id_from_args(args_list)
                    except:
                        pass

                if chain_id:
                    chain_exec = chain_execution_crud.get_by_chain_id(session, chain_id=chain_id)
                    if chain_exec:
                        chain_execution_crud.increment_failed_tasks(session, chain_execution=chain_exec)
                        logger.info(f"ChainExecution 실패 카운트 증가: {chain_id}")

        logger.info(f"작업 실패 처리 완료: {task_id}")



@task_retry.connect
def task_retry_handler(sender=None, task_id=None, reason=None, einfo=None, **kwargs):
    """작업 재시도 처리"""
    logger.info(f"🔄 SIGNAL: task_retry 수신 - task_id: {task_id}")
    with get_db_manager().get_sync_session() as session:
        if not session:
            logger.error("❌ DB 세션 생성 실패 - task_retry")
            return

        if not task_id:
            logger.warning("task_id를 찾을 수 없음")
            return

        error_message = str(reason) if reason else "Retry triggered"

        # TaskLog 재시도 카운트 증가
        task_log = task_log_crud.get_by_task_id(session, task_id=task_id)
        if task_log:
            task_log_crud.increment_retries(session, task_log=task_log)
            task_log_crud.update_status(
                session,
                task_log=task_log,
                status="RETRY",
                error=error_message
            )
            logger.info(f"TaskLog 재시도 처리: {task_id}")

        # 새로운 TaskExecutionHistory 시도 기록
        attempt_number = task_execution_history_crud.get_retry_count(session, task_id=task_id) + 1
        task_execution_history_crud.create_attempt(
            session,
            task_id=task_id,
            attempt_number=attempt_number,
            status="RETRY"
        )
        logger.info(f"TaskExecutionHistory 재시도 기록: {task_id}, attempt: {attempt_number}")



@task_revoked.connect
def task_revoked_handler(sender=None, request=None, reason=None, **kwargs):
    """작업 취소 처리"""
    task_id = request.id if request else None
    logger.info(f"🚫 SIGNAL: task_revoked 수신 - task_id: {task_id}")

    with get_db_manager().get_sync_session() as session:
        if not session:
            logger.error("❌ DB 세션 생성 실패 - task_revoked")
            return


        if not task_id:
            logger.warning("task_id를 찾을 수 없음")
            return

        # TaskLog 상태 업데이트
        task_log = task_log_crud.get_by_task_id(session, task_id=task_id)
        if task_log:
            task_log_crud.update_status(
                session,
                task_log=task_log,
                status="REVOKED",
                error=str(reason) if reason else "Task revoked"
            )
            logger.info(f"TaskLog 취소 처리: {task_id}")

            # TaskExecutionHistory 완료 처리
            latest_attempt = task_execution_history_crud.get_latest_attempt(session, task_id=task_id)
            if latest_attempt:
                task_execution_history_crud.complete_attempt(
                    session,
                    execution_history=latest_attempt,
                    status="REVOKED",
                    error_message=str(reason) if reason else "Task revoked"
                )



# 워커 관련 신호 처리

@worker_process_init.connect
def worker_process_init_handler(sender=None, **kwargs):
    """워커 프로세스 초기화 처리"""
    current_process = psutil.Process()
    process_info = {
        'pid': current_process.pid,
        'ppid': current_process.ppid(),
        'name': current_process.name(),
        'create_time': current_process.create_time(),
        'cpu_percent': current_process.cpu_percent(),
        'memory_percent': current_process.memory_percent(),
        'memory_mb': round(current_process.memory_info().rss / (1024 * 1024), 2),
        'num_threads': current_process.num_threads(),
        'status': current_process.status()
    }

    logger.info(f"🆕 SIGNAL: worker_process_init 수신")
    logger.info(f"📊 프로세스 정보: PID={process_info['pid']}, "
               f"PPID={process_info['ppid']}, "
               f"메모리={process_info['memory_mb']}MB, "
               f"스레드={process_info['num_threads']}, "
               f"상태={process_info['status']}")

@worker_ready.connect
def worker_ready_handler(sender=None, **kwargs):
    """워커 준비 완료 처리"""
    worker_name = get_worker_name(sender)

    # 워커 통계 정보 수집
    from celery import current_app
    inspect = current_app.control.inspect()
    stats = inspect.stats()

    if stats and worker_name in stats:
        worker_stats = stats[worker_name]
        pool_info = worker_stats.get('pool', {})

        logger.info(f"🟢 SIGNAL: worker_ready 수신 - worker: {worker_name}")
        logger.info(f"📊 워커 풀 정보: "
                   f"구현체={pool_info.get('implementation', 'unknown')}, "
                   f"최대 동시성={pool_info.get('max-concurrency', 'unknown')}, "
                   f"프로세스 수={len(pool_info.get('processes', []))}")

        # 각 프로세스 정보 로깅
        for proc_pid in pool_info.get('processes', []):
            try:
                proc = psutil.Process(proc_pid)
                logger.info(f"🔧 워커 프로세스: PID={proc_pid}, "
                           f"메모리={round(proc.memory_info().rss / (1024 * 1024), 2)}MB, "
                           f"CPU={proc.cpu_percent()}%, "
                           f"상태={proc.status()}")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                logger.warning(f"프로세스 {proc_pid} 정보 조회 실패")
    else:
        logger.info(f"🟢 SIGNAL: worker_ready 수신 - worker: {worker_name}")

@worker_shutdown.connect
def worker_shutdown_handler(sender=None, **kwargs):
    """워커 종료 처리"""
    worker_name = get_worker_name(sender)
    logger.info(f"🔴 SIGNAL: worker_shutdown 수신 - worker: {worker_name}")

    # 종료 시 프로세스 정보 로깅
    current_process = psutil.Process()
    logger.info(f"🔴 종료되는 프로세스: PID={current_process.pid}, "
               f"실행 시간={round((time.time() - current_process.create_time()), 2)}초, "
               f"메모리={round(current_process.memory_info().rss / (1024 * 1024), 2)}MB")


@heartbeat_sent.connect
def heartbeat_handler(sender=None, **kwargs):
    """하트비트 처리"""
    # 하트비트는 너무 자주 발생하므로 로깅하지 않음
    pass

# 유틸리티 함수 및 스케줄 작업

def collect_queue_stats():
    """큐 통계 수집 작업"""
    from celery import current_app
    with get_db_manager().get_sync_session() as session:
        if not session:
            return

        session : Session

        inspect = current_app.control.inspect()

        # 활성 작업 조회
        active_tasks = inspect.active()
        reserved_tasks = inspect.reserved()
        scheduled_tasks = inspect.scheduled()

        for worker_name, tasks in (active_tasks or {}).items():
            # QueueStats 업데이트
            queue_stat = session.query(QueueStats).filter_by(
                queue_name='celery',
                worker_name=worker_name
            ).first()

            if not queue_stat:
                queue_stat = QueueStats(
                    queue_name='celery',
                    worker_name=worker_name,
                    active_tasks=len(tasks),
                    reserved_tasks=len(reserved_tasks.get(worker_name, [])),
                    scheduled_tasks=len(scheduled_tasks.get(worker_name, []))
                )
                session.add(queue_stat)
            else:
                queue_stat.active_tasks = len(tasks)
                queue_stat.reserved_tasks = len(reserved_tasks.get(worker_name, []))
                queue_stat.scheduled_tasks = len(scheduled_tasks.get(worker_name, []))
                queue_stat.last_updated = datetime.now()



def get_task_statistics(session):
    """작업 통계 조회"""
    stats = session.query(
        TaskLog.status, session.query(TaskLog).filter_by(status=TaskLog.status).count())\
        .group_by(TaskLog.status).all()

    return {status: count for status, count in stats}

def cleanup_old_records(session, days=30):
    cutoff_date = datetime.now() - timedelta(days=days)

    # 완료된 작업의 오래된 레코드 삭제
    deleted_count = session.query(TaskLog)\
        .filter(TaskLog.completed_at < cutoff_date)\
        .filter(TaskLog.status.in_(['SUCCESS', 'FAILURE', 'REVOKED']))\
        .delete()

    session.commit()
    logger.info(f"오래된 작업 레코드 {deleted_count}개 정리됨")

    return deleted_count


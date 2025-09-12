# celery_signals.py
import json
from datetime import datetime, timedelta

from celery.signals import (
    task_prerun,
    task_success,
    task_failure,
    task_retry,
    task_revoked,
    worker_ready,
    worker_shutdown,
    heartbeat_sent,
    before_task_publish
)
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import SyncSessionLocal
from app.models.base import seoul_now
from ..models import (
    TaskLog, TaskMetadata, TaskExecutionHistory,
    TaskResult, WorkerStatus, QueueStats
)
from ..models.chain_execution import ChainExecution
from .logging import get_logger

# 로거 설정
logger = get_logger(__name__)

# 데이터베이스 세션 헬퍼
def get_db_session():
    """DB 세션 생성 헬퍼"""
    try:
        return SyncSessionLocal()
    except Exception as e:
        logger.error(f"DB 세션 생성 실패: {e}")
        return None

def safe_json_dumps(data):
    """안전한 JSON 직렬화"""
    try:
        return json.dumps(data, ensure_ascii=False)
    except (TypeError, ValueError):
        return json.dumps(str(data))

def get_worker_name(sender=None):
    """안전하게 워커 이름 가져오기"""
    try:
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
    except Exception as e:
        raise Exception from e

def get_chain_id_from_args(args):
    """task args에서 chain_id 추출"""
    try:
        if args and len(args) > 0:
            # args[0]이 chain_id인 경우 (UUID 문자열)
            chain_id_str = str(args[0])
            if len(chain_id_str) == 36 and chain_id_str.count('-') == 4:  # UUID 형태 확인
                return chain_id_str
        return None
    except Exception:
        return None

def update_chain_execution(session, chain_id_str, task_name, status, error_message=None):
    """ChainExecution 테이블 업데이트"""
    try:
        if not chain_id_str:
            return
        
        # chain_id로 ChainExecution 찾기
        chain_execution = session.query(ChainExecution).filter_by(
            chain_id=chain_id_str
        ).first()
        
        if not chain_execution:
            logger.warning(f"ChainExecution을 찾을 수 없음: {chain_id_str}")
            return
        
        # 작업 진행 상황 업데이트
        if status == 'SUCCESS':
            chain_execution.increment_completed_tasks()
            logger.info(f"Chain {chain_id_str}: 완료된 작업 수 증가 ({chain_execution.completed_tasks}/{chain_execution.total_tasks})")
        elif status == 'FAILURE':
            chain_execution.increment_failed_tasks()
            if error_message:
                chain_execution.error_message = error_message
            logger.info(f"Chain {chain_id_str}: 실패한 작업 수 증가 ({chain_execution.failed_tasks})")
        
        # 전체 체인 상태 확인 및 업데이트
        if chain_execution.completed_tasks + chain_execution.failed_tasks >= chain_execution.total_tasks:
            # 모든 작업이 완료된 경우
            if chain_execution.failed_tasks > 0:
                chain_execution.complete_execution(success=False, error_message=error_message)
                logger.info(f"Chain {chain_id_str}: 전체 체인 실패로 완료")
            else:
                chain_execution.complete_execution(success=True)
                logger.info(f"Chain {chain_id_str}: 전체 체인 성공적으로 완료")
        
        session.commit()
        
    except Exception as e:
        logger.error(f"ChainExecution 업데이트 실패 (chain_id: {chain_id_str}): {e}")
        session.rollback()

# 작업 관련 신호 처리

@before_task_publish.connect
def task_publish_handler(sender=None, headers=None, body=None, properties=None, **kwargs):
    """작업 발행 전 처리"""
    logger.info(f"🚀 SIGNAL: before_task_publish 수신 - sender: {sender}")
    session = get_db_session()
    if not session:
        logger.error("❌ DB 세션 생성 실패 - before_task_publish")
        return
    
    try:
        pass
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"❌ 작업 발행 처리 실패 (SQLAlchemy): {e}")
    except Exception as e:
        session.rollback()
        logger.error(f"❌ 작업 발행 처리 실패 (기타): {e}")
    finally:
        session.close()

@task_prerun.connect
def task_prerun_handler(task_id=None, task=None, args=None, kwargs=None, **kwds):
    """작업 실행 전 처리"""
    logger.info(f"🏃 SIGNAL: task_prerun 수신 - task_id: {task_id}")
    session = get_db_session()
    if not session:
        logger.error("❌ DB 세션 생성 실패 - task_prerun")
        return
    
    try:
        pass
        
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"❌ 작업 시작 처리 실패 (SQLAlchemy): {e}")
    except Exception as e:
        session.rollback()
        logger.error(f"❌ 작업 시작 처리 실패 (기타): {e}")
    finally:
        session.close()

@task_success.connect
def task_success_handler(sender=None, result=None, **kwargs):
    """작업 성공 처리"""
    logger.info(f"✅ SIGNAL: task_success 수신")
    session = get_db_session()
    if not session:
        logger.error("❌ DB 세션 생성 실패 - task_success")
        return
    
    try:
        pass
        
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"❌ 작업 성공 처리 실패 (SQLAlchemy): {e}")
    except Exception as e:
        session.rollback()
        logger.error(f"❌ 작업 성공 처리 실패 (기타): {e}")
    finally:
        session.close()

@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, traceback=None, einfo=None, **kwargs):
    """작업 실패 처리"""
    logger.info(f"❌ SIGNAL: task_failure 수신 - task_id: {task_id}")
    session = get_db_session()
    if not session:
        logger.error("❌ DB 세션 생성 실패 - task_failure")
        return
    
    try:
        pass
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"작업 실패 처리 실패: {e}")
    finally:
        session.close()

@task_retry.connect
def task_retry_handler(sender=None, task_id=None, reason=None, einfo=None, **kwargs):
    """작업 재시도 처리"""
    session = get_db_session()
    if not session:
        return
    
    try:
        pass
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"작업 재시도 처리 실패: {e}")
    finally:
        session.close()

@task_revoked.connect
def task_revoked_handler(sender=None, request=None, reason=None, **kwargs):
    """작업 취소 처리"""
    session = get_db_session()
    if not session:
        return
    
    try:
        pass
        
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"작업 취소 처리 실패: {e}")
    finally:
        session.close()

# 워커 관련 신호 처리

@worker_ready.connect
def worker_ready_handler(sender=None, **kwargs):
    """워커 준비 완료 처리"""
    session = get_db_session()
    if not session:
        return
    
    try:
        pass
        
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"워커 준비 처리 실패: {e}")
    finally:
        session.close()

@worker_shutdown.connect
def worker_shutdown_handler(sender=None, **kwargs):
    """워커 종료 처리"""
    session = get_db_session()
    if not session:
        return
    
    try:
        pass

    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"워커 종료 처리 실패: {e}")
    finally:
        session.close()

@heartbeat_sent.connect
def heartbeat_handler(sender=None, **kwargs):
    """하트비트 처리"""
    session = get_db_session()
    if not session:
        return
    
    try:
        pass
        
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"하트비트 처리 실패: {e}")
    except Exception as e:
        session.rollback()
        logger.error(f"하트비트 처리 중 예상치 못한 오류: {e}")
    finally:
        session.close()

# 유틸리티 함수 및 스케줄 작업

def collect_queue_stats():
    """큐 통계 수집 작업"""
    from celery import current_app
    session = get_db_session()
    if not session:
        return
    
    try:
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
                queue_stat.last_updated = seoul_now()
        
        session.commit()
        logger.debug("큐 통계 수집 완료")
        
    except Exception as e:
        session.rollback()
        logger.error(f"큐 통계 수집 실패: {e}")
    finally:
        session.close()

def get_task_statistics(session):
    """작업 통계 조회"""
    try:
        stats = session.query(TaskLog.status, session.query(TaskLog).filter_by(status=TaskLog.status).count())\
            .group_by(TaskLog.status).all()
        
        return {status: count for status, count in stats}
    except Exception as e:
        logger.error(f"작업 통계 조회 실패: {e}")
        return {}

def cleanup_old_records(session, days=30):
    """오래된 레코드 정리"""
    try:
        cutoff_date = seoul_now() - timedelta(days=days)
        
        # 완료된 작업의 오래된 레코드 삭제
        deleted_count = session.query(TaskLog)\
            .filter(TaskLog.completed_at < cutoff_date)\
            .filter(TaskLog.status.in_(['SUCCESS', 'FAILURE', 'REVOKED']))\
            .delete()
        
        session.commit()
        logger.info(f"오래된 작업 레코드 {deleted_count}개 정리됨")
        
        return deleted_count
    except Exception as e:
        logger.error(f"레코드 정리 실패: {e}")
        session.rollback()
        return 0


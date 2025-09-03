# app/core/celery_signals.py

from celery import signals
from datetime import datetime
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# 데이터베이스 관련 import를 지연 로딩으로 처리
sync_engine = None
SyncSessionLocal = None
TaskInfo = None

def init_sync_db():
    """동기식 데이터베이스 초기화 (지연 로딩)"""
    global sync_engine, SyncSessionLocal, TaskInfo
    
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker, Session
        from app.models.task_info import TaskInfo
        from app.core.config import settings
        
        # AsyncPG URL을 동기식 psycopg2 URL로 변환
        sync_database_url = settings.DATABASE_URL.replace("+asyncpg", "")
        logger.info(f"동기 데이터베이스 URL: {sync_database_url}")
        
        # 동기식 엔진 생성
        sync_engine = create_engine(
            sync_database_url,
            echo=False,  # 시그널에서는 로그 최소화
            pool_size=3,
            max_overflow=5,
            pool_pre_ping=True,
            pool_recycle=3600,  # 1시간마다 연결 재생성
        )
        
        # 세션 팩토리 생성
        SyncSessionLocal = sessionmaker(
            bind=sync_engine,
            class_=Session,
            expire_on_commit=False
        )
        
        logger.info("✅ Celery 시그널용 동기 데이터베이스 초기화 완료")
        return True
        
    except Exception as e:
        logger.error(f"❌ 동기 데이터베이스 초기화 실패: {e}")
        return False

def get_sync_db():
    """안전한 동기식 데이터베이스 세션 생성"""
    global SyncSessionLocal
    
    if SyncSessionLocal is None:
        if not init_sync_db():
            return None
    
    try:
        return SyncSessionLocal()
    except Exception as e:
        logger.error(f"데이터베이스 세션 생성 실패: {e}")
        return None

@signals.task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, **kwds):
    """태스크 시작 전 실행되는 시그널 (안전한 버전)"""
    try:
        logger.info(f"태스크 시작: {task.name if task else 'Unknown'} (ID: {task_id})")

        # 데이터베이스 세션 획득
        db = get_sync_db()
        if db is None:
            logger.warning("데이터베이스 세션을 생성할 수 없어 태스크 정보 저장을 건너뜁니다")
            return

        try:
            global TaskInfo
            if TaskInfo is None:
                logger.warning("TaskInfo 모델을 로드할 수 없어 태스크 정보 저장을 건너뜁니다")
                return

            task_info = TaskInfo(
                task_id=task_id,
                status="STARTED",
                task_name=task.name if task else "Unknown",
                task_time=datetime.now(),
                args=str(args) if args else None,
                kwargs=str(kwargs) if kwargs else None
            )
            
            db.add(task_info)
            db.commit()
            logger.info(f"태스크 시작 정보 저장 완료: {task_id}")
            
        except Exception as e:
            db.rollback()
            logger.error(f"태스크 시작 정보 저장 실패: {e}")
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"시그널 핸들러에서 예외 발생: {e}")
        # 시그널 핸들러에서는 예외를 다시 raise하지 않음


@signals.task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None,
                         retval=None, state=None, **kwds):
    """태스크 완료 후 실행되는 시그널"""
    logger.info(f"태스크 완료: {task.name} (ID: {task_id}) - 상태: {state}")

    db = get_sync_db()
    try:
        # 기존 TaskInfo 찾아서 업데이트
        task_info = db.query(TaskInfo).filter(TaskInfo.task_id == task_id).first()
        if task_info:
            task_info.status = state
            task_info.result = str(retval) if retval else None
            task_info.completed_time = datetime.now()

            db.commit()
            logger.info(f"태스크 완료 정보 업데이트 완료: {task_id}")
        else:
            logger.warning(f"태스크 정보를 찾을 수 없음: {task_id}")

    except Exception as e:
        db.rollback()
        logger.error(f"태스크 완료 정보 저장 실패: {e}")
    finally:
        db.close()


@signals.task_success.connect
def task_success_handler(sender=None, result=None, **kwds):
    """태스크 성공 시 실행되는 시그널"""
    logger.info(f"태스크 성공: {sender.name}")


@signals.task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, traceback=None, einfo=None, **kwds):
    """태스크 실패 시 실행되는 시그널"""
    logger.error(f"태스크 실패: {sender.name} (ID: {task_id}) - 오류: {exception}")

    db = get_sync_db()
    try:
        # 실패 정보를 TaskInfo에 업데이트
        task_info = db.query(TaskInfo).filter(TaskInfo.task_id == task_id).first()
        if task_info:
            task_info.status = "FAILURE"
            task_info.error_message = str(exception)
            task_info.traceback = str(traceback) if traceback else None
            task_info.completed_time = datetime.now()

            db.commit()
            logger.info(f"태스크 실패 정보 업데이트 완료: {task_id}")
        else:
            logger.warning(f"실패한 태스크 정보를 찾을 수 없음: {task_id}")

    except Exception as e:
        db.rollback()
        logger.error(f"태스크 실패 정보 저장 실패: {e}")
    finally:
        db.close()


@signals.task_retry.connect
def task_retry_handler(sender=None, task_id=None, reason=None, einfo=None, **kwds):
    """태스크 재시도 시 실행되는 시그널"""
    logger.warning(f"태스크 재시도: {sender.name} (ID: {task_id}) - 이유: {reason}")

    db = get_sync_db()
    try:
        # 재시도 정보를 TaskInfo에 업데이트
        task_info = db.query(TaskInfo).filter(TaskInfo.task_id == task_id).first()
        if task_info:
            task_info.status = "RETRY"
            task_info.retry_count = (task_info.retry_count or 0) + 1
            task_info.error_message = str(reason) if reason else None

            db.commit()
            logger.info(f"태스크 재시도 정보 업데이트 완료: {task_id}")

    except Exception as e:
        db.rollback()
        logger.error(f"태스크 재시도 정보 저장 실패: {e}")
    finally:
        db.close()


@signals.worker_ready.connect
def worker_ready_handler(sender=None, **kwds):
    """워커 준비 완료 시 실행되는 시그널"""
    logger.info(f"Celery 워커 준비 완료: {sender}")


@signals.worker_shutdown.connect
def worker_shutdown_handler(sender=None, **kwds):
    """워커 종료 시 실행되는 시그널"""
    logger.info(f"Celery 워커 종료: {sender}")
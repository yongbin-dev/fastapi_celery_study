# app/core/celery_signals.py

from celery import signals
from datetime import datetime
import logging
from typing import Any, Dict, Optional, Type
from contextlib import contextmanager
import threading

logger = logging.getLogger(__name__)

# 스레드 안전성을 위한 락
_db_lock = threading.RLock()

# 데이터베이스 관련 import를 지연 로딩으로 처리
sync_engine = None
SyncSessionLocal = None
TaskInfo: Optional[Type] = None
_initialized = False


def init_sync_db():
    """동기식 데이터베이스 초기화 (지연 로딩, 스레드 안전)"""
    global sync_engine, SyncSessionLocal, TaskInfo, _initialized

    with _db_lock:
        if _initialized:
            return True

        try:
            from sqlalchemy import create_engine
            from sqlalchemy.orm import sessionmaker, Session
            from app.models.task_info import TaskInfo
            from app.core.config import settings

            # AsyncPG URL을 동기식 psycopg2 URL로 변환
            sync_database_url = settings.DATABASE_URL.replace("+asyncpg", "")
            
            # 서울 시간대 설정 추가
            if "?" in sync_database_url:
                sync_database_url += "&options=-c timezone=Asia/Seoul"
            else:
                sync_database_url += "?options=-c timezone=Asia/Seoul"
                
            logger.info(f"동기 데이터베이스 URL: {sync_database_url}")

            # 동기식 엔진 생성
            sync_engine = create_engine(
                sync_database_url,
                echo=False,  # 시그널에서는 로그 최소화
                pool_size=5,  # 약간 증가
                max_overflow=10,  # 증가
                pool_pre_ping=True,
                pool_recycle=3600,  # 1시간마다 연결 재생성
                pool_timeout=30,  # 타임아웃 설정
            )

            # 세션 팩토리 생성
            SyncSessionLocal = sessionmaker(
                bind=sync_engine,
                class_=Session,
                expire_on_commit=False
            )

            _initialized = True
            logger.info("✅ Celery 시그널용 동기 데이터베이스 초기화 완료")
            return True

        except Exception as e:
            logger.error(f"❌ 동기 데이터베이스 초기화 실패: {e}")
            return False


@contextmanager
def get_sync_db_session():
    """안전한 동기식 데이터베이스 세션 생성 (Context Manager)"""
    global SyncSessionLocal

    if SyncSessionLocal is None:
        if not init_sync_db():
            logger.error("데이터베이스 초기화 실패")
            yield None
            return

    db = None
    try:
        db = SyncSessionLocal()
        yield db
    except Exception as e:
        logger.error(f"데이터베이스 세션 생성 실패: {e}")
        if db:
            db.rollback()
        yield None
    finally:
        if db:
            try:
                db.close()
            except Exception as e:
                logger.error(f"데이터베이스 세션 종료 실패: {e}")


def extract_task_pipeline_id(task, task_id: str) -> Dict[str, Any]:
    """태스크에서 단계 정보 및 pipeline_id 추출 (chain_id를 pipeline_id로 사용)"""
    task_info = {}

    try:
        # 태스크 이름에서 단계 정보 추출 (예: step_1, step_2 등)

        # Chain ID를 Pipeline ID로 사용
        if hasattr(task, 'request'):
            # Root task ID를 pipeline_id로 사용 (체인의 루트가 파이프라인 ID)
            if hasattr(task.request, 'root_id') and task.request.root_id:
                task_info['pipeline_id'] = task.request.root_id
                logger.info(f"🔗 Pipeline ID 설정: {task.request.root_id} for task: {task_id}")
            # 루트 ID가 없으면 현재 태스크 ID를 pipeline_id로 사용
            elif not hasattr(task.request, 'parent_id') or not task.request.parent_id:
                task_info['pipeline_id'] = task_id
                logger.info(f"🔗 Pipeline ID 설정 (루트): {task_id}")
        

    except Exception as e:
        logger.warning(f"태스크 단계 정보 추출 중 오류: {e}")

    return task_info


def save_task_info_safely(task_id: str, status: str,  **extra_fields) -> bool:
    """태스크 정보를 안전하게 저장하는 헬퍼 함수 (새로운 TaskInfo 생성자 사용)"""
    global TaskInfo

    if TaskInfo is None:
        logger.warning("TaskInfo 모델을 로드할 수 없어 태스크 정보 저장을 건너뜁니다")
        return False

    try:
        with get_sync_db_session() as db:
            if db is None:
                logger.warning("데이터베이스 세션을 생성할 수 없어 태스크 정보 저장을 건너뜁니다")
                return False

            # 새로운 TaskInfo 생성자 파라미터에 맞춰 필터링
            allowed_fields = {'stages', 'traceback', 'step', 'ready', 'progress', 'pipeline_id'}
            filtered_fields = {k: v for k, v in extra_fields.items() if k in allowed_fields}
            
            if TaskInfo is not None:  # 타입 체커를 위한 추가 체크
                task_info = TaskInfo(
                    task_id=task_id,
                    status=status,
                    **filtered_fields
                )

                db.add(task_info)
                db.commit()
                return True

    except Exception as e:
        logger.error(f"태스크 정보 저장 실패: {e}")
        return False

    return False


def update_task_info_safely(task_id: str, updates: Dict[str, Any]) -> bool:
    """태스크 정보를 안전하게 업데이트하는 헬퍼 함수"""
    global TaskInfo

    if TaskInfo is None:
        logger.warning("TaskInfo 모델을 로드할 수 없어 태스크 정보 업데이트를 건너뜁니다")
        return False

    try:
        with get_sync_db_session() as db:
            if db is None:
                logger.warning("데이터베이스 세션을 생성할 수 없어 태스크 정보 업데이트를 건너뜁니다")
                return False

            task_info = db.query(TaskInfo).filter(TaskInfo.task_id == task_id).first()
            if task_info:
                for key, value in updates.items():
                    setattr(task_info, key, value)
                db.commit()
                return True
            else:
                logger.warning(f"태스크 정보를 찾을 수 없음: {task_id}")
                return False

    except Exception as e:
        logger.error(f"태스크 정보 업데이트 실패: {e}")
        return False


@signals.task_prerun.connect
def task_prerun_handler(task_id=None, task=None, args=None, kwargs=None, **kwds):
    """태스크 시작 전 실행되는 시그널 (Chain 지원 버전)"""
    try:

        # 단계 정보 추출
        step_info = extract_task_pipeline_id(task, task_id)

        # TaskInfo 생성자를 사용하여 저장 (새로운 필드만)
        extra_fields = {
            **step_info  # step, ready, progress 정보 추가
        }

        if save_task_info_safely(task_id, "STARTED",  **extra_fields):
            logger.info(f"태스크 시작 정보 저장 완료: {task_id}")
        else:
            logger.warning(f"태스크 시작 정보 저장 실패: {task_id}")

    except Exception as e:
        logger.error(f"task_prerun 시그널 핸들러에서 예외 발생: {e}")


@signals.task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None,
                         retval=None, state=None, **kwds):
    """태스크 완료 후 실행되는 시그널 (개선된 버전)"""
    try:

        updates = {
            "status": state,
            "stages": str(retval) if retval else None,
            "ready": True,
            "progress": 100 if state == "SUCCESS" else 0
        }

        if update_task_info_safely(task_id, updates):
            logger.info(f"태스크 완료 정보 업데이트 완료: {task_id}")
        else:
            logger.warning(f"태스크 완료 정보 업데이트 실패: {task_id}")

    except Exception as e:
        logger.error(f"task_postrun 시그널 핸들러에서 예외 발생: {e}")


@signals.task_success.connect
def task_success_handler(sender=None, result=None, **kwds):
    """태스크 성공 시 실행되는 시그널"""
    try:
        logger.info(f"태스크 성공: {sender.name}")
    except Exception as e:
        logger.error(f"task_success 시그널 핸들러에서 예외 발생: {e}")


@signals.task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, traceback=None, einfo=None, **kwds):
    """태스크 실패 시 실행되는 시그널 (개선된 버전)"""
    try:

        updates = {
            "status": "FAILURE",
            "traceback": str(traceback) if traceback else None,
            "ready": True,
            "progress": 0
        }

        if update_task_info_safely(task_id, updates):
            logger.info(f"태스크 실패 정보 업데이트 완료: {task_id}")
        else:
            logger.warning(f"태스크 실패 정보 업데이트 실패: {task_id}")

    except Exception as e:
        logger.error(f"task_failure 시그널 핸들러에서 예외 발생: {e}")


@signals.task_retry.connect
def task_retry_handler(sender=None, task_id=None, reason=None, einfo=None, **kwds):
    """태스크 재시도 시 실행되는 시그널 (개선된 버전)"""
    try:

        updates = {
            "status": "RETRY",
            "traceback": str(reason) if reason else None,
            "ready": False,
            "progress": 0
        }

        if update_task_info_safely(task_id, updates):
            logger.info(f"태스크 재시도 정보 업데이트 완료: {task_id}")
        else:
            logger.warning(f"태스크 재시도 정보 업데이트 실패: {task_id}")

    except Exception as e:
        logger.error(f"task_retry 시그널 핸들러에서 예외 발생: {e}")


@signals.worker_ready.connect
def worker_ready_handler(sender=None, **kwds):
    """워커 준비 완료 시 실행되는 시그널"""
    try:
        logger.info(f"Celery 워커 준비 완료: {sender}")
        # 워커 시작 시 데이터베이스 초기화 시도
        init_sync_db()
    except Exception as e:
        logger.error(f"worker_ready 시그널 핸들러에서 예외 발생: {e}")


@signals.worker_shutdown.connect
def worker_shutdown_handler(sender=None, **kwds):
    """워커 종료 시 실행되는 시그널"""
    try:
        logger.info(f"Celery 워커 종료: {sender}")
        # 워커 종료 시 연결 정리
        global sync_engine
        if sync_engine:
            sync_engine.dispose()
            logger.info("데이터베이스 연결 정리 완료")
    except Exception as e:
        logger.error(f"worker_shutdown 시그널 핸들러에서 예외 발생: {e}")


# 선택적 로깅 설정을 위한 설정 변수
ENABLE_TASK_LOGGING = True  # 환경변수로 제어 가능하도록 설정


def set_task_logging(enabled: bool):
    """태스크 로깅 활성화/비활성화"""
    global ENABLE_TASK_LOGGING
    ENABLE_TASK_LOGGING = enabled
    logger.info(f"태스크 로깅 {'활성화' if enabled else '비활성화'}")


def get_task_logging_status() -> bool:
    """태스크 로깅 상태 반환"""
    return ENABLE_TASK_LOGGING


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


def extract_chain_info(task, task_id: str) -> Dict[str, Any]:
    """태스크에서 chain 관련 정보를 추출 (TaskInfo 모델 구조에 맞춤)"""
    chain_info = {}

    try:
        if hasattr(task, 'request'):
            # Root task ID (체인의 첫 번째 태스크)
            if hasattr(task.request, 'root_id') and task.request.root_id:
                chain_info['root_task_id'] = task.request.root_id

            # Parent task ID (직접적인 부모)
            if hasattr(task.request, 'parent_id') and task.request.parent_id:
                chain_info['parent_task_id'] = task.request.parent_id

            # Chain 정보
            if hasattr(task.request, 'chain') and task.request.chain:
                chain_signatures = task.request.chain
                chain_info['chain_total'] = len(chain_signatures) + 1  # 현재 태스크 포함

    except Exception as e:
        logger.warning(f"Chain 정보 추출 중 오류: {e}")

    return chain_info


def save_task_info_safely(task_id: str, status: str, task_name: str, **extra_fields) -> bool:
    """태스크 정보를 안전하게 저장하는 헬퍼 함수 (TaskInfo 생성자 사용)"""
    global TaskInfo

    if TaskInfo is None:
        logger.warning("TaskInfo 모델을 로드할 수 없어 태스크 정보 저장을 건너뜁니다")
        return False

    try:
        with get_sync_db_session() as db:
            if db is None:
                logger.warning("데이터베이스 세션을 생성할 수 없어 태스크 정보 저장을 건너뜁니다")
                return False

            # TaskInfo 생성자를 사용하여 객체 생성
            # TaskInfo가 None이 아님을 확인했으므로 안전하게 호출 가능
            if TaskInfo is not None:  # 타입 체커를 위한 추가 체크
                task_info = TaskInfo(
                    task_id=task_id,
                    status=status,
                    task_name=task_name,
                    **extra_fields
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
        task_name = task.name if task else "Unknown"
        logger.info(f"태스크 시작: {task_name} (ID: {task_id})")

        # Chain 관련 정보 추출
        chain_info = extract_chain_info(task, task_id)

        # Chain 정보가 있으면 로그에 추가 정보 출력
        if chain_info.get('root_task_id'):
            logger.info(f"🔗 Chain 태스크: {task_name} (Root: {chain_info['root_task_id']}, "
                        f"Parent: {chain_info.get('parent_task_id', 'None')}, "
                        f"Total: {chain_info.get('chain_total', '?')})")

        # TaskInfo 생성자를 사용하여 저장
        extra_fields = {
            "task_time": datetime.now(),
            "args": str(args) if args else None,
            "kwargs": str(kwargs) if kwargs else None,
            **chain_info  # chain 관련 정보 추가
        }

        if save_task_info_safely(task_id, "STARTED", task_name, **extra_fields):
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
        task_name = task.name if task else "Unknown"
        logger.info(f"태스크 완료: {task_name} (ID: {task_id}) - 상태: {state}")

        updates = {
            "status": state,
            "result": str(retval) if retval else None,
            "completed_time": datetime.now()
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
        task_name = sender.name if sender else "Unknown"
        logger.error(f"태스크 실패: {task_name} (ID: {task_id}) - 오류: {exception}")

        updates = {
            "status": "FAILURE",
            "error_message": str(exception) if exception else None,
            "traceback": str(traceback) if traceback else None,
            "completed_time": datetime.now()
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
        task_name = sender.name if sender else "Unknown"
        logger.warning(f"태스크 재시도: {task_name} (ID: {task_id}) - 이유: {reason}")

        # 기존 retry_count를 가져와서 증가시키기 위해 조회 후 업데이트
        with get_sync_db_session() as db:
            if db is None:
                logger.warning("데이터베이스 세션을 생성할 수 없어 재시도 정보 업데이트를 건너뜁니다")
                return

            global TaskInfo
            if TaskInfo is None:
                logger.warning("TaskInfo 모델을 로드할 수 없어 재시도 정보 업데이트를 건너뜁니다")
                return

            task_info = db.query(TaskInfo).filter(TaskInfo.task_id == task_id).first()
            if task_info:
                task_info.status = "RETRY"
                task_info.retry_count = (task_info.retry_count or 0) + 1
                task_info.error_message = str(reason) if reason else None
                db.commit()
                logger.info(f"태스크 재시도 정보 업데이트 완료: {task_id}")
            else:
                logger.warning(f"재시도할 태스크 정보를 찾을 수 없음: {task_id}")

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


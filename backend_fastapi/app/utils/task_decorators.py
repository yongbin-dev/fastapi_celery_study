# app/utils/task_decorators.py

from functools import wraps
import time

from typing import Dict, Any, Callable, Optional

from app.schemas.enums import ProcessStatus
from app.schemas.pipeline import StageResult, PipelineMetadata
from app.api.v1.services.redis_service import RedisPipelineStatusManager

from app.core.logging import get_logger

logger = get_logger(__name__)


def pipeline_stage(stage_name: str, stage_num: int):
    """
    파이프라인 스테이지 데코레이터

    공통 로직을 캡슐화하여 코드 중복을 줄입니다:
    - 상태 업데이트
    - 에러 처리
    - 진행률 업데이트
    - 메트릭 로깅
    - 실행 시간 추적

    Args:
        stage_name: 스테이지 이름 (예: "데이터 전처리")
        stage_num: 스테이지 번호 (1-4)
    """

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # chain_id 추출 (args나 kwargs에서)
            chain_id = None

            # 첫 번째 argument가 dict이고 chain_id를 포함하는 경우
            if args and isinstance(args[0], dict) and "chain_id" in args[0]:
                chain_id = args[0]["chain_id"]
            # 두 번째 argument가 chain_id인 경우 (stage1의 경우)
            elif len(args) >= 2 and isinstance(args[1], str):
                chain_id = args[1]
            # kwargs에서 chain_id 찾기
            elif "chain_id" in kwargs:
                chain_id = kwargs["chain_id"]

            if not chain_id:
                raise ValueError(
                    f"chain_id를 찾을 수 없습니다. Stage {stage_num} ({stage_name})"
                )

            start_time = time.time()
            status_manager = RedisPipelineStatusManager()
            task_id = self.request.id

            # 입력 데이터 크기 계산
            input_size = 0
            if args:
                input_size = len(str(args[0])) if args[0] else 0

            logger.info(
                f"Chain {chain_id}: Stage {stage_num} ({stage_name}) 시작 - 입력 데이터 크기: {input_size} bytes"
            )

            try:
                # 작업 시작 상태 업데이트
                metadata = PipelineMetadata(
                    stage_name=stage_name, start_time=start_time, input_size=input_size
                ).dict()

                status_manager.update_status(
                    chain_id,
                    stage_num,
                    ProcessStatus.PENDING,
                    0,
                    metadata,
                    task_id=task_id,
                )

                # Celery 진행률 업데이트
                update_celery_progress(
                    self, chain_id, stage_num, stage_name, f"{stage_name} 시작", 0
                )

                # 실제 작업 로직 실행
                result = func(self, *args, **kwargs)

                # 실행 시간 계산
                execution_time = time.time() - start_time

                # 작업 완료 상태 업데이트
                completion_metadata = PipelineMetadata(
                    stage_name=stage_name,
                    start_time=start_time,
                    execution_time=execution_time,
                    input_size=input_size,
                ).dict()

                status_manager.update_status(
                    chain_id,
                    stage_num,
                    ProcessStatus.SUCCESS,
                    100,
                    completion_metadata,
                    task_id=task_id,
                )

                # 메트릭 로깅
                log_stage_metrics(
                    chain_id, stage_num, stage_name, execution_time, input_size
                )

                return result

            except Exception as e:
                handle_stage_error(self, chain_id, stage_num, stage_name, e, start_time)
                raise

        return wrapper

    return decorator


def update_celery_progress(
    self, chain_id: str, stage: int, stage_name: str, status: str, progress: int
) -> None:
    """Celery 진행 상태 업데이트 공통 로직"""
    status_manager = RedisPipelineStatusManager()

    pipeline_status = status_manager.get_pipeline_status(chain_id)
    total_stages = len(pipeline_status) if pipeline_status else 4  # 기본 4단계
    overall_progress = calculate_overall_progress(stage, progress, total_stages)

    self.update_state(
        state="PROGRESS",
        meta={
            "stage": stage,
            "stage_name": stage_name,
            "status": status,
            "progress": progress,
            "overall_progress": overall_progress,
        },
    )


def handle_stage_error(
    self,
    chain_id: str,
    stage: int,
    stage_name: str,
    error: Exception,
    start_time: float,
) -> None:
    """단계 에러 처리 공통 로직"""
    execution_time = time.time() - start_time
    error_message = f"Chain {chain_id}: Stage {stage} ({stage_name}) 실패 - {str(error)}"
    logger.error(error_message)

    # 에러 메타데이터
    error_metadata = PipelineMetadata(
        stage_name=stage_name,
        start_time=start_time,
        execution_time=execution_time,
        error=str(error),
    ).dict()

    # Redis 상태 업데이트
    status_manager = RedisPipelineStatusManager()
    status_manager.update_status(
        chain_id, stage, ProcessStatus.FAILURE, 0, error_metadata
    )

    # Celery에 에러 전파 (재시도 로직)
    raise self.retry(exc=error, countdown=60, max_retries=3)


def log_stage_metrics(
    chain_id: str,
    stage: int,
    stage_name: str,
    execution_time: float,
    input_size: int = 0,
):
    """단계별 메트릭 로깅"""
    logger.info(
        f"[METRICS] Chain: {chain_id} | Stage: {stage} | Name: {stage_name} | "
        f"Time: {execution_time:.2f}s | Input Size: {input_size}"
    )


def calculate_overall_progress(
    stage: int, stage_progress: int, total_stages: int
) -> int:
    """전체 파이프라인 진행률 계산"""
    if total_stages == 0:
        return 0
    stage_weight = 100 / total_stages
    completed_stages = (stage - 1) * stage_weight
    current_stage_progress = (stage_progress / 100) * stage_weight
    return int(completed_stages + current_stage_progress)


def validate_stage_input(data: Dict[str, Any], required_fields: list) -> bool:
    """단계 간 데이터 전달 시 검증"""
    if not data or not isinstance(data, dict):
        logger.error("입력 데이터가 dict 타입이 아닙니다")
        return False

    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        logger.error(f"필수 필드 누락: {missing_fields}")
        return False
    return True


def validate_chain_id(chain_id: Optional[str]) -> bool:
    """체인 ID 유효성 검증"""
    if not chain_id or not isinstance(chain_id, str) or not chain_id.strip():
        logger.error("유효하지 않은 chain_id")
        return False
    return True


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

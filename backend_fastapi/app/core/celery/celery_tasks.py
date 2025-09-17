# app/celery_tasks.py

import time
from typing import Dict, Any
from app.celery_app import celery_app
from app.core.exceptions import TaskValidationError
from app.core.logging import get_logger
from app.pipeline_config import STAGES
from app.schemas.enums import ProcessStatus
from app.utils.task_decorators import (
    pipeline_stage,
    validate_chain_id,
    validate_stage_input,
    create_stage_result
)

logger = get_logger(__name__)


@celery_app.task(bind=True, name=STAGES[0]["task_name"])
@pipeline_stage(stage_name=STAGES[0]["name"], stage_num=STAGES[0]["stage"])
def stage1_preprocessing(self, input_data: Dict[str, Any], chain_id: str = None) -> Dict[str, Any]:
    """
    1단계: 데이터 전처리
    """
    # 체인 ID 및 입력 데이터 검증
    if not validate_chain_id(chain_id):
        raise TaskValidationError(
            message="유효하지 않은 chain_id",
            task_id=self.request.id,
            chain_id=chain_id,
            stage_num=1
        )

    if not input_data or not isinstance(input_data, dict):
        logger.error(f"Chain {chain_id}: Stage 1 입력 데이터 검증 실패")
        raise TaskValidationError(
            message="입력 데이터가 유효하지 않습니다",
            task_id=self.request.id,
            chain_id=chain_id,
            stage_num=1,
            details={"input_data_type": type(input_data).__name__}
        )

    # 전처리 시뮬레이션
    logger.info(f"Chain {chain_id}: 데이터 전처리 시작")
    time.sleep(2)
    logger.info(f"Chain {chain_id}: 데이터 정제 완료")

    # 중간 진행률 업데이트 (데코레이터가 처리하지 않는 세부 진행률)
    from app.utils.task_decorators import update_celery_progress
    update_celery_progress(self, chain_id, 1, "데이터 전처리", '데이터 정제 중', 50)

    time.sleep(2)
    logger.info(f"Chain {chain_id}: 데이터 전처리 마무리")

    # 다음 stage로 전달할 데이터
    return create_stage_result(chain_id, 1, ProcessStatus.SUCCESS, input_data, 0.0)  # execution_time은 데코레이터가 처리


@celery_app.task(bind=True, name=STAGES[1]["task_name"])
@pipeline_stage(stage_name=STAGES[1]["name"], stage_num=STAGES[1]["stage"])
def stage2_feature_extraction(self, stage1_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    2단계: 특성 추출
    """
    # stage1에서 전달받은 chain_id 추출
    if not validate_stage_input(stage1_result, ['chain_id']):
        raise TaskValidationError(
            message="Stage 1 결과 데이터가 유효하지 않습니다",
            task_id=self.request.id,
            chain_id=stage1_result.get('chain_id'),
            stage_num=2
        )

    chain_id = stage1_result.get("chain_id")

    logger.info(f"Chain {chain_id}: 특성 추출 시작")
    time.sleep(3)
    logger.info(f"Chain {chain_id}: 벡터화 진행 중")

    # 중간 진행률 업데이트
    from app.utils.task_decorators import update_celery_progress
    update_celery_progress(self, chain_id, 2, "특성 추출", '벡터화 진행 중', 70 )

    time.sleep(2)
    logger.info(f"Chain {chain_id}: 특성 추출 완료")

    # 다음 stage로 전달할 데이터
    return create_stage_result(chain_id, 2, ProcessStatus.SUCCESS, stage1_result, 0.0)


@celery_app.task(bind=True, name=STAGES[2]["task_name"])
@pipeline_stage(stage_name=STAGES[2]["name"], stage_num=STAGES[2]["stage"])
def stage3_model_inference(self, stage2_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    3단계: 모델 추론
    """
    # stage2에서 전달받은 chain_id 추출
    if not validate_stage_input(stage2_result, ['chain_id']):
        raise TaskValidationError(
            message="Stage 2 결과 데이터가 유효하지 않습니다",
            task_id=self.request.id,
            chain_id=stage2_result.get('chain_id'),
            stage_num=3
        )

    chain_id = stage2_result.get("chain_id")

    logger.info(f"Chain {chain_id}: 모델 로딩 시작")
    time.sleep(2)
    logger.info(f"Chain {chain_id}: 모델 로딩 완료, 추론 시작")

    # 중간 진행률 업데이트
    from app.utils.task_decorators import update_celery_progress
    update_celery_progress(self, chain_id, 3, "모델 추론", '추론 실행 중', 40 )

    time.sleep(4)
    logger.info(f"Chain {chain_id}: 모델 추론 완료")

    # 다음 stage로 전달할 데이터
    return create_stage_result(chain_id, 3, ProcessStatus.SUCCESS, stage2_result, 0.0)


@celery_app.task(bind=True, name=STAGES[3]["task_name"])
@pipeline_stage(stage_name=STAGES[3]["name"], stage_num=STAGES[3]["stage"])
def stage4_post_processing(self, stage3_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    4단계: 후처리 및 결과 정리
    """
    # stage3에서 전달받은 chain_id 추출
    if not validate_stage_input(stage3_result, ['chain_id']):
        raise TaskValidationError(
            message="Stage 3 결과 데이터가 유효하지 않습니다",
            task_id=self.request.id,
            chain_id=stage3_result.get('chain_id'),
            stage_num=4
        )

    chain_id = stage3_result.get("chain_id")

    logger.info(f"Chain {chain_id}: 후처리 시작")
    time.sleep(2)
    logger.info(f"Chain {chain_id}: 최종 검증 시작")

    # 중간 진행률 업데이트
    from app.utils.task_decorators import update_celery_progress
    update_celery_progress(self, chain_id, 4, "후처리", '최종 검증 중', 80 )

    time.sleep(1)
    logger.info(f"Chain {chain_id}: 파이프라인 완료")

    # 최종 결과 반환
    return create_stage_result(chain_id, 4, ProcessStatus.SUCCESS, stage3_result, 0.0)


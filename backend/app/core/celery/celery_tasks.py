# app/celery_tasks.py

import time
from typing import Dict, Any, Optional
from app.celery_app import celery_app
from app.core.exceptions import TaskValidationError
from app.core.logging import get_logger
from app.pipeline_config import STAGES
from app.schemas.enums import ProcessStatus
from app.core.celery.task_decorators import (
    task_logger,
    create_stage_result,
)

logger = get_logger(__name__)


@celery_app.task(bind=True, name=STAGES[0]["task_name"])
@task_logger(auto_chain=True, is_pipeline=True)
def stage1_preprocessing(
    self,
    chain_id: str,
    input_data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    1단계: 데이터 전처리
    """
    # 비즈니스 로직에만 집중
    time.sleep(1)  # 시뮬레이션

    # 다음 stage로 전달할 데이터
    return create_stage_result(chain_id, 1, ProcessStatus.SUCCESS, input_data, 0.0)


@celery_app.task(bind=True, name=STAGES[1]["task_name"])
@task_logger(auto_chain=True, is_pipeline=True)
def stage2_feature_extraction(self, stage1_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    2단계: 특성 추출
    """
    chain_id = str(stage1_result.get("chain_id"))
    time.sleep(1)  # 시뮬레이션

    # 다음 stage로 전달할 데이터
    return create_stage_result(chain_id, 2, ProcessStatus.SUCCESS, stage1_result, 0.0)


@celery_app.task(bind=True, name=STAGES[2]["task_name"])
@task_logger(auto_chain=True, is_pipeline=True)
def stage3_model_inference(self, stage2_result: Dict[str, Any]) -> Dict[str, Any]:
    chain_id = str(stage2_result.get("chain_id"))
    time.sleep(1)  # 시뮬레이션

    # 다음 stage로 전달할 데이터
    return create_stage_result(chain_id, 3, ProcessStatus.SUCCESS, stage2_result, 0.0)


@celery_app.task(bind=True, name=STAGES[3]["task_name"])
@task_logger(auto_chain=True, is_pipeline=True)
def stage4_post_processing(self, stage3_result: Dict[str, Any]) -> Dict[str, Any]:
    chain_id = str(stage3_result.get("chain_id"))
    time.sleep(1)  # 시뮬레이션
    logger.info(f"Chain {chain_id}: 파이프라인 완료")

    # 최종 결과 반환
    return create_stage_result(chain_id, 4, ProcessStatus.SUCCESS, stage3_result, 0.0)

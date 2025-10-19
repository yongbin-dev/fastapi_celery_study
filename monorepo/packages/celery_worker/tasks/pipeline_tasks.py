# pipeline_tasks.py
"""
파이프라인 Celery 태스크
celery_worker에서만 정의되고 실행됨
"""

import time
from typing import Any, Dict

from celery import chain
from core.task_decorators import (
    create_stage_result,
    task_logger,
)
from shared.config.pipeline_config import STAGES
from shared.core.logging import get_logger
from shared.schemas.enums import ProcessStatus

from ..celery_app import celery_app

logger = get_logger(__name__)


@celery_app.task(bind=True, name=STAGES[0]["task_name"])
@task_logger(auto_chain=True, is_pipeline=True)
def stage1_preprocessing(
    self,  # noqa: ARG001
    chain_id: str,
    input_data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    1단계: 데이터 전처리
    """
    time.sleep(1)  # 시뮬레이션
    return create_stage_result(chain_id, 1, ProcessStatus.SUCCESS, input_data, 0.0)


@celery_app.task(bind=True, name=STAGES[1]["task_name"])
@task_logger(auto_chain=True, is_pipeline=True)
def stage2_feature_extraction(self, stage1_result: Dict[str, Any]) -> Dict[str, Any]:  # noqa: ARG001
    """
    2단계: 특성 추출
    """
    chain_id = str(stage1_result.get("chain_id"))
    time.sleep(1)  # 시뮬레이션
    return create_stage_result(chain_id, 2, ProcessStatus.SUCCESS, stage1_result, 0.0)


@celery_app.task(bind=True, name=STAGES[2]["task_name"])
@task_logger(auto_chain=True, is_pipeline=True)
def stage3_model_inference(self, stage2_result: Dict[str, Any]) -> Dict[str, Any]:  # noqa: ARG001
    """
    3단계: 모델 추론
    """
    chain_id = str(stage2_result.get("chain_id"))
    time.sleep(1)  # 시뮬레이션
    return create_stage_result(chain_id, 3, ProcessStatus.SUCCESS, stage2_result, 0.0)


@celery_app.task(bind=True, name=STAGES[3]["task_name"])
@task_logger(auto_chain=True, is_pipeline=True)
def stage4_post_processing(self, stage3_result: Dict[str, Any]) -> Dict[str, Any]:  # noqa: ARG001
    """
    4단계: 후처리
    """
    chain_id = str(stage3_result.get("chain_id"))
    time.sleep(1)  # 시뮬레이션
    logger.info(f"Chain {chain_id}: 파이프라인 완료")
    return create_stage_result(chain_id, 4, ProcessStatus.SUCCESS, stage3_result, 0.0)


def create_pipeline_chain(chain_id: str, input_data: Dict[str, Any]):
    """
    파이프라인 Celery chain 생성

    Args:
        chain_id: 파이프라인 실행 ID
        input_data: 입력 데이터

    Returns:
        Celery chain 객체
    """
    pipeline = chain(
        stage1_preprocessing.s(chain_id, input_data), # type: ignore
        stage2_feature_extraction.s(),# type: ignore
        stage3_model_inference.s(),# type: ignore
        stage4_post_processing.s(), # type: ignore
    )
    return pipeline

# app/domains/pipeline/pipelines/ai_pipeline.py
"""
AI 처리 파이프라인

OCR → LLM → Vision 도메인을 순차적으로 실행하는 파이프라인

Note: Celery tasks are defined in celery_worker package.
This module only provides pipeline configuration.
"""

from typing import Any, Dict


def create_ai_processing_pipeline(chain_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    AI 처리 파이프라인 생성

    워크플로우:
    1. 전처리 (공통)
    2. OCR 텍스트 추출
    3. LLM 텍스트 분석
    4. Vision 객체 탐지
    5. 후처리 및 결과 통합

    Args:
        chain_id: 파이프라인 실행 ID
        input_data: 입력 데이터

    Returns:
        Pipeline configuration dictionary
    """
    # Pipeline 설정 반환 (실제 Celery chain은 celery_worker에서 생성)
    return {
        "chain_id": chain_id,
        "input_data": input_data,
        "stages": [
            {"name": "stage1_preprocessing", "task": "pipeline.stage1_preprocessing"},
            {"name": "stage2_feature_extraction", "task": "pipeline.stage2_feature_extraction"},
            {"name": "stage3_model_inference", "task": "pipeline.stage3_model_inference"},
            {"name": "stage4_post_processing", "task": "pipeline.stage4_post_processing"},
        ],
    }


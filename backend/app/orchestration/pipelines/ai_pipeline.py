# app/orchestration/pipelines/ai_pipeline.py
"""
AI 처리 파이프라인

OCR → LLM → Vision 도메인을 순차적으로 실행하는 파이프라인
"""

from typing import Any, Dict

from celery import chain


def create_ai_processing_pipeline(chain_id: str, input_data: Dict[str, Any]):
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
        Celery chain 객체
    """
    # 기존 4단계 파이프라인 (현재 구현)
    from app.core.celery.celery_tasks import (
        stage1_preprocessing,
        stage2_feature_extraction,
        stage3_model_inference,
        stage4_post_processing,
    )

    pipeline = chain(
        stage1_preprocessing.s(chain_id, input_data),
        stage2_feature_extraction.s(),
        stage3_model_inference.s(),
        stage4_post_processing.s(),
    )

    return pipeline


def create_document_pipeline(chain_id: str, document_path: str):
    """
    문서 처리 파이프라인

    워크플로우:
    1. OCR 텍스트 추출
    2. LLM 텍스트 요약
    3. 결과 저장

    Args:
        chain_id: 파이프라인 실행 ID
        document_path: 문서 파일 경로

    Returns:
        Celery chain 객체
    """
    from app.domains.llm.tasks.llm_tasks import generate_text_task
    from app.domains.ocr.tasks.ocr_tasks import extract_text_task

    # 향후 구현: OCR → LLM 요약 파이프라인
    pipeline = chain(
        extract_text_task.s(document_path),
        generate_text_task.s(),  # OCR 결과를 LLM으로 전달
    )

    return pipeline


def create_image_analysis_pipeline(chain_id: str, image_path: str):
    """
    이미지 분석 파이프라인

    워크플로우:
    1. Vision 객체 탐지
    2. OCR 텍스트 추출 (이미지 내 텍스트)
    3. LLM 통합 설명 생성

    Args:
        chain_id: 파이프라인 실행 ID
        image_path: 이미지 파일 경로

    Returns:
        Celery chain 객체
    """
    from app.domains.llm.tasks.llm_tasks import generate_text_task
    from app.domains.ocr.tasks.ocr_tasks import extract_text_task

    # 향후 구현: Vision + OCR + LLM 조합
    pipeline = chain(
        extract_text_task.s(),
        generate_text_task.s(),
    )

    return pipeline

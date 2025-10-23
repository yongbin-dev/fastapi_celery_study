"""Pipeline Orchestration - 파이프라인 시작 및 관리

Celery 태스크로 파이프라인을 시작하고 관리합니다.
"""

from celery import chain
from shared.pipeline import PipelineContext, PipelineOrchestrator
from shared.core.logging import get_logger
from .stages import OCRStage, LLMStage, LayoutStage, ExcelStage

logger = get_logger(__name__)


async def start_pipeline(context_id: str, **kwargs) -> PipelineContext:
    """파이프라인 시작

    Args:
        context_id: 컨텍스트 ID
        **kwargs: 파이프라인 초기 데이터

    Returns:
        완료된 파이프라인 컨텍스트
    """
    logger.info(f"파이프라인 오케스트레이션 시작: {context_id}")

    # 컨텍스트 생성
    context = PipelineContext(
        context_id=context_id,
        data=kwargs
    )

    # 오케스트레이터 생성 및 스테이지 추가
    orchestrator = PipelineOrchestrator()
    orchestrator.add_stage(OCRStage())
    orchestrator.add_stage(LLMStage())
    orchestrator.add_stage(LayoutStage())
    orchestrator.add_stage(ExcelStage())

    # 파이프라인 실행
    result_context = await orchestrator.execute(context)

    logger.info(f"파이프라인 오케스트레이션 완료: {context_id}")
    return result_context


def create_pipeline_chain(context_id: str, **kwargs):
    """Celery Chain 생성

    각 스테이지를 Celery 태스크로 연결합니다.

    Args:
        context_id: 컨텍스트 ID
        **kwargs: 파이프라인 초기 데이터

    Returns:
        Celery chain 객체
    """
    # TODO: 실제 Celery 태스크 체인 구현
    # 현재는 placeholder
    pass

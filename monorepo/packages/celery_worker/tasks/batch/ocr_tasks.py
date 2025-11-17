from celery_app import celery_app
from shared.core.logging import get_logger
from shared.pipeline.context import PipelineContext
from shared.pipeline.exceptions import RetryableError

from tasks.stages.ocr_stage import OCRStage

logger = get_logger(__name__)


@celery_app.task(
    name="pipeline.ocr_stage",
    max_retries=3,
    autoretry_for=(ConnectionError, TimeoutError, RetryableError),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
)
def start_ocr_stage(context_dict: dict):
    """OCR 스테이지 실행

    Args:
        context_dict: PipelineContext의 딕셔너리 표현
    """
    import asyncio

    # 딕셔너리를 PipelineContext로 변환
    context = PipelineContext(**context_dict)

    stage = OCRStage()
    # 비동기 함수를 동기적으로 실행
    context = asyncio.run(stage.run(context))

    logger.info(f"ocr_stage ${context.chain_execution_id}")

    # 결과를 딕셔너리로 반환
    return context.model_dump()

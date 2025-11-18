from celery_app import celery_app
from shared.core.logging import get_logger
from shared.pipeline.cache import get_pipeline_cache_service
from shared.pipeline.context import PipelineContext
from shared.pipeline.exceptions import RetryableError
from shared.schemas.enums import ProcessStatus

logger = get_logger(__name__)


@celery_app.task(
    name="pipeline.finish_stage",
    max_retries=3,
    autoretry_for=(ConnectionError, TimeoutError, RetryableError),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
)
def start_finish_stage(context_dict: dict):
    """finish 스테이지 실행

    Args:
        context_dict: PipelineContext의 딕셔너리 표현
    """
    # 딕셔너리를 PipelineContext로 변환
    context = PipelineContext(**context_dict)

    logger.info(f"finish_stage ${context.chain_execution_id}")

    context.status = ProcessStatus.SUCCESS
    get_pipeline_cache_service().save_context(context)

    # 결과를 딕셔너리로 반환
    return context.model_dump()

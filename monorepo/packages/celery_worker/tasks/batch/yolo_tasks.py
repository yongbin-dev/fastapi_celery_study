from celery_app import celery_app
from shared.core.logging import get_logger
from shared.pipeline.context import PipelineContext
from shared.pipeline.exceptions import RetryableError

logger = get_logger(__name__)


@celery_app.task(
    name="pipeline.yolo_stage",
    max_retries=3,
    autoretry_for=(ConnectionError, TimeoutError, RetryableError),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
)
def start_yolo_stage(context_dict: dict):
    """yolo 스테이지 실행

    Args:
        context_dict: PipelineContext의 딕셔너리 표현
    """
    # 딕셔너리를 PipelineContext로 변환
    context = PipelineContext(**context_dict)

    logger.info(f"yolo_stage ${context.chain_execution_id}")

    # TODO: YOLO Stage 로직 구현

    # 결과를 딕셔너리로 반환
    return context.model_dump()

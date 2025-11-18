"""배치 OCR 파이프라인

여러 이미지를 한 번에 처리하는 배치 OCR 파이프라인
"""

from typing import Any, Dict, Optional

from celery import chain
from shared.core.database import get_db_manager
from shared.core.logging import get_logger
from shared.pipeline.cache import get_pipeline_cache_service
from shared.pipeline.context import PipelineContext
from shared.repository.crud.sync_crud.chain_execution import chain_execution_crud
from shared.schemas.common import ImageResponse
from shared.schemas.enums import ProcessStatus

from tasks.batch import start_ocr_stage

logger = get_logger(__name__)
cache_service = get_pipeline_cache_service()


def execute_batch_ocr_pipeline(
    image_responses: list[ImageResponse],
    batch_id: Optional[str],
    options: Optional[Dict[str, Any]] = None,
):
    """배치 OCR 파이프라인 실행

    여러 이미지를 한 번에 처리하여 Batch OCR API를 활용합니다.

    Args:
        image_responses: 이미지 응답 객체 리스트
        batch_id: 배치 ID
        options: 파이프라인 옵션 (기본: None)

    Returns:
        처리 결과 dict (completed_count, failed_count, chain_id)
    """

    if options is None:
        options = {}

    logger.info(
        f"배치 OCR 파이프라인 실행 시작: "
        f"batch_id={batch_id}, images={len(image_responses)}"
    )

    # batch_id가 빈 문자열이면 None으로 변환
    batch_id = batch_id if batch_id else None

    with get_db_manager().get_sync_session() as session:
        if not session:
            raise RuntimeError("DB 세션 생성 실패")

        # 2. ChainExecution 생성 (OCR Stage 시작 전)
        chain_execution = chain_execution_crud.create_chain_execution(
            db=session,
            chain_name="batch_ocr_pipeline",
            batch_id=batch_id,
            initiated_by="batch_ocr",
            input_data={"image_count": len(image_responses)},
        )
        logger.info(f"ChainExecution 생성 완료: chain_id={chain_execution.id}, ")

        # 3. PipelineContext 생성 (배치 모드, chain_execution_id 포함)
        context = PipelineContext(
            batch_id=batch_id or "",
            chain_execution_id=chain_execution.id,
            private_imgs=[img.private_img for img in image_responses],
            public_file_paths=[img.public_img for img in image_responses],
            is_batch=True,
            options=options,
        )

        # Redis에 컨텍스트 저장
        cache_service.save_context(context)

        # 4. OCR Stage 실행 (배치)
        try:
            # PipelineContext를 딕셔너리로 변환하여 Celery 태스크 실행
            context_dict = context.model_dump()

            # Celery chain을 사용하여 순차적으로 태스크 실행
            # 각 태스크의 출력이 다음 태스크의 입력으로 자동 전달됨
            workflow = chain(
                start_ocr_stage.s(context_dict),  # .s()는 signature 생성
                # start_llm_stage.s(),  # 이전 결과를 자동으로 받음
                # start_yolo_stage.s(),  # 이전 결과를 자동으로 받음
            )

            # 비동기로 실행
            result = workflow.apply_async()

            logger.info(
                f"파이프라인 체인 실행 시작: chain_id={chain_execution.id}, "
                f"task_id={result.id}"
            )

            # 6. ChainExecution 상태 업데이트 (성공)
            chain_execution_crud.update_status(
                db=session,
                chain_execution=chain_execution,
                status=ProcessStatus.SUCCESS,
            )
            logger.info(
                f"배치 OCR 파이프라인 완료: chain_execution_id={chain_execution.id}, "
            )

        except Exception as e:
            # ChainExecution 상태 업데이트 (실패)
            chain_execution_crud.update_status(
                db=session,
                chain_execution=chain_execution,
                status=ProcessStatus.FAILURE,
            )

            logger.error(
                f"배치 OCR 파이프라인 실패: chain_execution.id={chain_execution.id}"
                f":error={str(e)}",
                exc_info=True,
            )

"""파이프라인 Celery 태스크

각 스테이지를 Celery 태스크로 래핑하여 비동기 실행 및 재시도 지원
"""

import uuid
from typing import Any, Dict, Optional

from shared.core.database import get_db_manager
from shared.core.logging import get_logger
from shared.pipeline.cache import get_pipeline_cache_service
from shared.pipeline.context import PipelineContext
from shared.schemas.common import ImageResponse

from .stages.ocr_stage import OCRStage

logger = get_logger(__name__)

# PipelineCacheService 인스턴스
cache_service = get_pipeline_cache_service()


# 각 단계별 Celery 태스크
# @celery_app.task(
#     bind=True,
#     name="pipeline.ocr_stage",
#     max_retries=3,
#     autoretry_for=(ConnectionError, TimeoutError, RetryableError),
#     retry_backoff=True,
#     retry_backoff_max=600,
#     retry_jitter=True,
# )
# def ocr_stage_task(self, context_dict: Dict[str, str]) -> Dict[str, str]:
#     """OCR 단계 실행

#     Args:
#         self: Celery task instance
#         context_dict: batch_id와 chain_id를 포함하는 딕셔너리

#     Returns:
#         컨텍스트 ID (다음 단계로 전달)
#     """
#     # 딕셔너리에서 batch_id와 chain_id 추출
#     batch_id = context_dict["batch_id"]
#     chain_id = context_dict["chain_id"]

#     # Redis에서 context 로드
#     context = cache_service.load_context(batch_id, chain_id)

#     # 취소 상태 확인
#     if context.status == ProcessStatus.REVOKED:
#         logger.warning(f"⚠️ 작업 {chain_id}가 취소되었습니다 (OCR stage)")
#         raise Exception(f"작업이 취소되었습니다: {chain_id}")

#     # OCR 실행 (동기로 실행 - run_sync 필요 없음, async 함수를 직접 호출)
#     import asyncio

#     stage = OCRStage()
#     context = asyncio.run(stage.run(context))

#     # Redis에 저장
#     cache_service.save_context(context)

#     return {"batch_id": batch_id, "chain_id": chain_id}  # 다음 단계로 전달


# @celery_app.task(
#     bind=True,
#     name="pipeline.llm_stage",
#     max_retries=3,
#     autoretry_for=(ConnectionError, TimeoutError, RetryableError),
#     retry_backoff=True,
#     retry_backoff_max=600,
# )
# def llm_stage_task(self, context_dict: Dict[str, str]) -> Dict[str, str]:
#     """LLM 분석 단계 실행

#     Args:
#         self: Celery task instance
#         context_id: 컨텍스트 ID

#     Returns:
#         컨텍스트 ID
#     """

#     # 딕셔너리에서 batch_id와 chain_id 추출
#     batch_id = context_dict["batch_id"]
#     chain_id = context_dict["chain_id"]

#     # Redis에서 context 로드
#     context = cache_service.load_context(batch_id, chain_id)

#     # 취소 상태 확인
#     if context.status == ProcessStatus.REVOKED:
#         logger.warning(f"⚠️ 작업 {chain_id}가 취소되었습니다 (LLM stage)")
#         raise Exception(f"작업이 취소되었습니다: {chain_id}")

#     # OCR 실행 (동기로 실행 - run_sync 필요 없음, async 함수를 직접 호출)
#     import asyncio

#     stage = LLMStage()
#     context = asyncio.run(stage.run(context))

#     # Redis에 저장
#     cache_service.save_context(context)
#     return {"batch_id": batch_id, "chain_id": chain_id}  # 다음 단계로 전달


# @celery_app.task(
#     bind=True,
#     name="pipeline.finish_stage_task",
#     max_retries=3,
#     autoretry_for=(ConnectionError, TimeoutError, RetryableError),
#     retry_backoff=True,
#     retry_backoff_max=600,
# )
# def finish_stage_task(self, context_dict: Dict[str, str]) -> Dict[str, str]:
#     """LLM 분석 단계 실행

#     Args:
#         self: Celery task instance
#         context_id: 컨텍스트 ID

#     Returns:
#         컨텍스트 ID
#     """

#     # 딕셔너리에서 batch_id와 chain_id 추출
#     batch_id = context_dict["batch_id"]
#     chain_id = context_dict["chain_id"]

#     # Redis에서 context 로드
#     context = cache_service.load_context(batch_id, chain_id)

#     context.status = ProcessStatus.SUCCESS
#     # Redis에 저장
#     cache_service.save_context(context)

#     return {"batch_id": batch_id, "chain_id": chain_id}  # 다음 단계로 전달


# @celery_app.task(bind=True, name="tasks.start_pipeline")
# def start_pipeline_task(
#     self, image_response: ImageResponse, batch_id: str, options: Dict[str, Any]
# ) -> str:
#     """파이프라인 시작 (Celery Task)"""
#     return start_pipeline(image_response, batch_id, options)


# 파이프라인 시작 함수 (비동기 chain 방식)
# def start_pipeline(
#     image_response: ImageResponse, batch_id: Optional[str], options: Dict[str, Any]
# ) -> str:
#     """파이프라인 시작 (비동기 chain 방식)

#     Args:
#         image_response: 이미지 응답 객체
#         batch_id: 배치 ID
#         options: 파이프라인 옵션

#     Returns:
#         context_id: 파이프라인 실행 추적 ID (=chain_id)
#     """
#     # 1. Chain ID 생성
#     chain_id = str(uuid.uuid4())

#     # 2. DB에 ChainExecution 생성
#     from shared.repository.crud.sync_crud.chain_execution import chain_execution_crud

#     # batch_id가 빈 문자열이면 None으로 변환 (외래 키 제약 조건 위반 방지)
#     batch_id = batch_id if batch_id else None

#     with get_db_manager().get_sync_session() as session:
#         if not session:
#             raise RuntimeError("DB 세션 생성 실패")

#         chain_exec = chain_execution_crud.create_chain_execution(
#             db=session,
#             chain_id=chain_id,
#             batch_id=batch_id,
#             chain_name="workflow",
#             total_tasks=2,  # OCR, LLM
#             initiated_by="api_server",
#             input_data={"file_path": image_response.private_img, "options": options},
#         )

#         # 3. Context 생성 및 Redis 저장
#         context = PipelineContext(
#             batch_id=batch_id or "",
#             chain_id=chain_id,
#             private_img=image_response.private_img,
#             public_file_path=image_response.public_img,
#             options=options,
#         )

#         cache_service.save_context(context)

#         # 4. Celery chain으로 단계 연결
#         workflow = chain(
#             ocr_stage_task.s(
#                 {"batch_id": context.batch_id, "chain_id": context.chain_id}
#             ),
#             llm_stage_task.s(),
#             finish_stage_task.s(),
#         )

#         # 5. 비동기 실행
#         result = workflow.apply_async()

#         # 6. Celery task ID를 DB에 저장
#         chain_execution_crud.update_celery_task_id(
#             db=session, chain_execution=chain_exec, celery_task_id=result.id
#         )
#         logger.info(f"✅ Celery task ID 저장 완료: {result.id}
# (chain_id: {chain_id})")

#         return context.chain_id


def start_batch_pipeline_sync(
    image_responses: list[ImageResponse],
    batch_id: Optional[str],
    options: Dict[str, Any] = {},
) -> Dict[str, Any]:
    """배치 파이프라인 동기 실행 (Batch OCR 활용)

    여러 이미지를 한 번에 처리하여 Batch OCR API를 활용합니다.

    Args:
        image_responses: 이미지 응답 객체 리스트
        batch_id: 배치 ID
        options: 파이프라인 옵션

    Returns:
        처리 결과 (completed_count, failed_count)
    """
    import asyncio

    logger.info(
        f"배치 파이프라인 동기 실행 시작: "
        f"batch_id={batch_id}, images={len(image_responses)}"
    )

    # 1. Chain ID 생성 (배치 전체에 하나)
    chain_id = str(uuid.uuid4())

    # batch_id가 빈 문자열이면 None으로 변환
    batch_id = batch_id if batch_id else None

    with get_db_manager().get_sync_session() as session:
        if not session:
            raise RuntimeError("DB 세션 생성 실패")

        # 3. PipelineContext 생성 (배치 모드)
        context = PipelineContext(
            batch_id=batch_id or "",
            chain_id=chain_id,
            private_imgs=[img.private_img for img in image_responses],
            public_file_paths=[img.public_img for img in image_responses],
            is_batch=True,
            options=options,
        )

        cache_service.save_context(context)

        # 4. OCR Stage 실행 (배치)
        try:
            stage = OCRStage()
            context = asyncio.run(stage.run(context))

            # 5. 결과 집계
            if context.ocr_results:
                completed_count = sum(
                    1 for result in context.ocr_results if result.text_boxes
                )
                failed_count = len(context.ocr_results) - completed_count
            else:
                completed_count = 0
                failed_count = len(image_responses)

            logger.info(
                f"배치 파이프라인 완료: chain_id={chain_id}, "
                f"completed={completed_count}, failed={failed_count}"
            )

            return {
                "chain_id": chain_id,
                "completed_count": completed_count,
                "failed_count": failed_count,
            }

        except Exception as e:
            logger.error(f"배치 파이프라인 실패: chain_id={chain_id}, error={str(e)}")
            return {
                "chain_id": chain_id,
                "completed_count": 0,
                "failed_count": len(image_responses),
            }

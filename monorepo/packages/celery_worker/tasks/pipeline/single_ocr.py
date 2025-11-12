"""단일 OCR 파이프라인 (참고용 - 사용 안 함)

⚠️ 이 파일은 참고용으로만 보관됩니다.
현재는 배치 OCR 파이프라인(batch_ocr.py)을 사용합니다.

TODO: 필요 시 단일 이미지 처리를 위한 chain 기반 파이프라인 활성화
"""

# import uuid
# from typing import Any, Dict, Optional
#
# from celery import chain
# from celery_app import celery_app
# from shared.core.database import get_db_manager
# from shared.core.logging import get_logger
# from shared.pipeline.cache import get_pipeline_cache_service
# from shared.pipeline.context import PipelineContext
# from shared.pipeline.exceptions import RetryableError
# from shared.schemas.common import ImageResponse
# from shared.schemas.enums import ProcessStatus
# from tasks.stages.llm_stage import LLMStage
# from tasks.stages.ocr_stage import OCRStage
#
# logger = get_logger(__name__)
# cache_service = get_pipeline_cache_service()
#
#
# # ============================================================================
# # Celery Stage Tasks (Chain 기반)
# # ============================================================================
#
#
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
#
#     Args:
#         self: Celery task instance
#         context_dict: batch_id와 chain_id를 포함하는 딕셔너리
#
#     Returns:
#         컨텍스트 ID (다음 단계로 전달)
#     """
#     import asyncio
#
#     # 딕셔너리에서 batch_id와 chain_id 추출
#     batch_id = context_dict["batch_id"]
#     chain_id = context_dict["chain_id"]
#
#     # Redis에서 context 로드
#     context = cache_service.load_context(batch_id, chain_id)
#
#     # 취소 상태 확인
#     if context.status == ProcessStatus.REVOKED:
#         logger.warning(f"⚠️ 작업 {chain_id}가 취소되었습니다 (OCR stage)")
#         raise Exception(f"작업이 취소되었습니다: {chain_id}")
#
#     # OCR 실행
#     stage = OCRStage()
#     context = asyncio.run(stage.run(context))
#
#     # Redis에 저장
#     cache_service.save_context(context)
#
#     return {"batch_id": batch_id, "chain_id": chain_id}
#
#
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
#
#     Args:
#         self: Celery task instance
#         context_dict: batch_id와 chain_id를 포함하는 딕셔너리
#
#     Returns:
#         컨텍스트 ID
#     """
#     import asyncio
#
#     # 딕셔너리에서 batch_id와 chain_id 추출
#     batch_id = context_dict["batch_id"]
#     chain_id = context_dict["chain_id"]
#
#     # Redis에서 context 로드
#     context = cache_service.load_context(batch_id, chain_id)
#
#     # 취소 상태 확인
#     if context.status == ProcessStatus.REVOKED:
#         logger.warning(f"⚠️ 작업 {chain_id}가 취소되었습니다 (LLM stage)")
#         raise Exception(f"작업이 취소되었습니다: {chain_id}")
#
#     # LLM 실행
#     stage = LLMStage()
#     context = asyncio.run(stage.run(context))
#
#     # Redis에 저장
#     cache_service.save_context(context)
#
#     return {"batch_id": batch_id, "chain_id": chain_id}
#
#
# @celery_app.task(
#     bind=True,
#     name="pipeline.finish_stage",
#     max_retries=3,
#     autoretry_for=(ConnectionError, TimeoutError, RetryableError),
#     retry_backoff=True,
#     retry_backoff_max=600,
# )
# def finish_stage_task(self, context_dict: Dict[str, str]) -> Dict[str, str]:
#     """파이프라인 완료 처리
#
#     Args:
#         self: Celery task instance
#         context_dict: batch_id와 chain_id를 포함하는 딕셔너리
#
#     Returns:
#         컨텍스트 ID
#     """
#     # 딕셔너리에서 batch_id와 chain_id 추출
#     batch_id = context_dict["batch_id"]
#     chain_id = context_dict["chain_id"]
#
#     # Redis에서 context 로드
#     context = cache_service.load_context(batch_id, chain_id)
#
#     # 완료 상태로 변경
#     context.status = ProcessStatus.SUCCESS
#
#     # Redis에 저장
#     cache_service.save_context(context)
#
#     return {"batch_id": batch_id, "chain_id": chain_id}
#
#
# # ============================================================================
# # Pipeline Start Functions
# # ============================================================================
#
#
# @celery_app.task(bind=True, name="pipeline.start")
# def start_pipeline_task(
#     self,
#     image_response_dict: Dict[str, str],
#     batch_id: str,
#     options: Dict[str, Any],
# ) -> str:
#     """파이프라인 시작 (Celery Task)
#
#     Args:
#         self: Celery task instance
#         image_response_dict: ImageResponse dict
#         batch_id: 배치 ID
#         options: 파이프라인 옵션
#
#     Returns:
#         chain_id: 파이프라인 실행 추적 ID
#     """
#     image_response = ImageResponse(**image_response_dict)
#     return start_pipeline(image_response, batch_id, options)
#
#
# def start_pipeline(
#     image_response: ImageResponse,
#     batch_id: Optional[str],
#     options: Dict[str, Any],
# ) -> str:
#     """단일 이미지 파이프라인 시작 (Chain 기반)
#
#     OCR → LLM → Finish 순서로 체인 실행
#
#     Args:
#         image_response: 이미지 응답 객체
#         batch_id: 배치 ID
#         options: 파이프라인 옵션
#
#     Returns:
#         chain_id: 파이프라인 실행 추적 ID
#     """
#     from shared.repository.crud.sync_crud.chain_execution import chain_execution_crud
#
#     # 1. Chain ID 생성
#     chain_id = str(uuid.uuid4())
#
#     # batch_id가 빈 문자열이면 None으로 변환
#     batch_id = batch_id if batch_id else None
#
#     with get_db_manager().get_sync_session() as session:
#         if not session:
#             raise RuntimeError("DB 세션 생성 실패")
#
#         # 2. ChainExecution 생성
#         chain_exec = chain_execution_crud.create_chain_execution(
#             db=session,
#             chain_id=chain_id,
#             batch_id=batch_id,
#             chain_name="single_workflow",
#             total_tasks=2,  # OCR, LLM
#             initiated_by="api_server",
#             input_data={
#                 "file_path": image_response.private_img,
#                 "options": options,
#             },
#         )
#
#         # 3. Context 생성 및 Redis 저장
#         context = PipelineContext(
#             batch_id=batch_id or "",
#             chain_id=chain_id,
#             private_img=image_response.private_img,
#             public_file_path=image_response.public_img,
#             options=options,
#         )
#
#         cache_service.save_context(context)
#
#         # 4. Celery chain으로 단계 연결
#         workflow = chain(
#             ocr_stage_task.s(
#                 {"batch_id": context.batch_id, "chain_id": context.chain_id}
#             ),
#             llm_stage_task.s(),
#             finish_stage_task.s(),
#         )
#
#         # 5. 비동기 실행
#         result = workflow.apply_async()
#
#         # 6. Celery task ID를 DB에 저장
#         chain_execution_crud.update_celery_task_id(
#             db=session,
#             chain_execution=chain_exec,
#             celery_task_id=result.id,
#         )
#
#         logger.info(
#             f"✅ 단일 파이프라인 시작: chain_id={chain_id}, "
#             f"celery_task_id={result.id}"
#         )
#
#         return context.chain_id

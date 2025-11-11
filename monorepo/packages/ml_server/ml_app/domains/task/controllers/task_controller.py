# app/domains/ocr/controllers/ocr_controller.py
import uuid

from fastapi import APIRouter, Body, Depends, File, UploadFile
from ml_app.core.celery_client import get_celery_client
from shared.core.logging import get_logger
from shared.pipeline.cache import PipelineCacheService, get_pipeline_cache_service
from shared.schemas.common import ImageResponse
from shared.utils.response_builder import ResponseBuilder
from tasks.batch_tasks import start_batch_pipeline_from_pdf
from tasks.pipeline_tasks import start_pipeline

logger = get_logger(__name__)

router = APIRouter(prefix="/task", tags=["TASK"])


@router.get("/healthy")
async def healthy():
    return ResponseBuilder.success(data="정상", message="")


@router.post("/extract-pdf")
async def run_ocr_pdf_extract_async(
    pdf_file: UploadFile = File(...),
):
    """
    PDF 파일 OCR 비동기 처리

    PDF 파일을 업로드받아 이미지로 변환 후 OCR을 수행합니다.
    """
    file_bytes = await pdf_file.read()

    batch_id = str(uuid.uuid4())

    start_batch_pipeline_from_pdf(
        batch_id=batch_id,
        pdf_file_bytes=file_bytes,
        original_filename=pdf_file.filename or "",
    )

    return ResponseBuilder.success(data=batch_id)


@router.post("/extract-async")
async def run_ocr_image_extract_async(
    chain_id: str = Body(...),
    public_image_path: str = Body(...),
    private_image_path: str = Body(...),
    language: str = Body("korean"),
    confidence_threshold: float = Body(0.5),
    use_angle_cls: bool = Body(True),
):
    """
    OCR 비동기 처리 (Celery 태스크)

    태스크를 Celery에 전송하고 즉시 task_id를 반환합니다.
    결과는 /ocr/result/{task_id}로 조회할 수 있습니다.
    """
    logger.info(f"🚀 OCR 비동기 태스크 전송: {private_image_path}")

    # 태스크 전송
    start_pipeline(
        image_response=ImageResponse(
            public_img=public_image_path, private_img=private_image_path
        ),
        batch_id=None,
        options={},
    )

    return ResponseBuilder.success(
        data="",
        message="태스크 전송 완료",
    )


# batch_id로 모든 컨텍스트 조회
@router.get("/batch/{batch_id}")
async def get_batch_contexts(
    batch_id: str, cache_service=Depends(get_pipeline_cache_service)
):
    """
    batch_id로 모든 파이프라인 컨텍스트 조회

    Args:
        batch_id: 배치 ID

    Returns:
        배치에 속한 모든 파이프라인 컨텍스트 목록
    """
    logger.info(f"🔍 배치 컨텍스트 조회: batch_id={batch_id}")

    try:
        contexts = cache_service.load_all_by_batch_id(batch_id)

        # 컨텍스트 정보를 응답 형식으로 변환
        contexts_data = [
            {
                "chain_id": ctx.chain_id,
                "batch_id": ctx.batch_id,
                "current_stage": ctx.current_stage,
                "status": ctx.status,
                "private_img": ctx.private_img,
                "public_file_path": ctx.public_file_path,
                "options": ctx.options,
            }
            for ctx in contexts
        ]

        logger.info(f"✅ 배치 컨텍스트 조회 완료: {len(contexts)}개 발견")

        return ResponseBuilder.success(
            data={
                "batch_id": batch_id,
                "total_count": len(contexts),
                "contexts": contexts_data,
            },
            message=f"배치 {batch_id}의 컨텍스트 {len(contexts)}개 조회 완료",
        )

    except ValueError as e:
        logger.warning(f"⚠️ 배치 컨텍스트 없음: {str(e)}")
        return ResponseBuilder.success(
            data={"batch_id": batch_id, "total_count": 0, "contexts": []},
            message=f"배치 {batch_id}에 대한 컨텍스트가 없습니다.",
        )
    except Exception as e:
        logger.error(f"❌ 배치 컨텍스트 조회 실패: {str(e)}")
        return ResponseBuilder.error(
            message=f"배치 컨텍스트 조회 중 오류 발생: {str(e)}"
        )


# 2. Redis 직접 - 복잡한 컨텍스트 조회
@router.get("/{batch_id}/{chain_id}")
async def get_pipeline_context(
    batch_id: str, chain_id: str, cache_service=Depends(get_pipeline_cache_service)
):
    context = cache_service.load_context(batch_id, chain_id)

    return {
        "progress": context.current_stage,
        "status": context.status,
    }


@router.get("/result/{task_id}")
async def get_ocr_task_result(task_id: str):
    """
    태스크 결과 조회

    Args:
        task_id: Celery 태스크 ID

    Reclturns:
        태스크 상태 및 결과
    """
    logger.info(f"🔍 OCR 태스크 결과 조회: task_id={task_id}")

    # Celery 클라이언트 가져오기
    celery_client = get_celery_client()

    # AsyncResult 객체 생성
    async_result = celery_client.celery_app.AsyncResult(task_id)

    # 태스크 상태 확인
    if async_result.ready():
        # 완료됨
        if async_result.successful():
            result = str(async_result.result)
            logger.info(f"✅ OCR 태스크 완료: task_id={task_id}")
            logger.info(f"✅ OCR 태스크 완료 결과: {result}")
            return ResponseBuilder.success(
                data={task_id},
                message="태스크 완료",
            )
        else:
            # 실패
            error = str(async_result.result)
            logger.error(f"❌ OCR 태스크 실패: task_id={task_id}, error={error}")
            return ResponseBuilder.success(
                data={task_id},
                message="태스크 실패",
            )
    else:
        logger.info("로딩중")

    return ""


@router.delete("/cancel/{chain_id}")
async def cancel_task_result(
    chain_id: str,
    # session: AsyncSession = Depends(get_db),
    cache_service: PipelineCacheService = Depends(get_pipeline_cache_service),
):
    """
    태스크 취소

    Args:
        chain_id: chain_id
    """
    logger.info(f"🔍 OCR 태스크 결과 조회: chain_id={chain_id}")

    # Celery 클라이언트 가져오기
    celery_client = get_celery_client()

    # chain_exec = await chain_execution_crud.get_by_chain_id(session, chain_id=chain_id)
    # if chain_exec is None:
    #     raise Exception()

    # celery_client.celery_app.control.revoke(chain_exec.celery_task_id, terminate=True)
    # context: PipelineContext = cache_service.load_context(chain_exec.batch_id, chain_id)
    # if context is None:
    #     return

    # context.status = ProcessStatus.REVOKED
    # cache_service.save_context(context)

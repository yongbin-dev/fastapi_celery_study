# app/domains/ocr/controllers/ocr_controller.py
from app.domains.pipeline.schemas.pipeline_schemas import PipelineStartResponse
from fastapi import APIRouter, Body, Depends, File, UploadFile
from ml_app.core.celery_client import get_celery_client
from ml_app.models.ocr_model import get_ocr_model
from ml_app.schemas.response import TestResultDTO
from shared.core.database import get_db
from shared.core.logging import get_logger
from shared.schemas.common import ImageResponse
from shared.schemas.enums import PipelineStatus
from shared.service.common_service import CommonService, get_common_service
from shared.utils.response_builder import ResponseBuilder
from sqlalchemy.ext.asyncio import AsyncSession
from tasks.batch_tasks import start_batch_pipeline_from_pdf
from tasks.pipeline_tasks import start_pipeline

logger = get_logger(__name__)

router = APIRouter(prefix="/ocr", tags=["OCR"])


@router.get("/healthy")
async def healthy():
    return ResponseBuilder.success(data="정상", message="")


@router.post("/extract")
async def run_ocr_image_extract(
    public_image_path: str = Body(...),
    private_image_path: str = Body(...),
    language: str = Body("korean"),
    confidence_threshold: float = Body(0.5),
    use_angle_cls: bool = Body(True),
    common_service: CommonService = Depends(get_common_service),
    db: AsyncSession = Depends(get_db),
):
    """image ocr"""
    logger.info(f"OCR 실행 시작: {private_image_path}")
    image_data = await common_service.load_image(private_image_path)
    model = get_ocr_model(use_angle_cls=use_angle_cls, lang=language)
    result = model.predict(image_data, confidence_threshold)
    return result


@router.post("/extract-pdf")
async def run_ocr_pdf_extract_async(
    pdf_file: UploadFile = File(...),
):
    """
    PDF 파일 OCR 비동기 처리

    PDF 파일을 업로드받아 이미지로 변환 후 OCR을 수행합니다.
    """
    file_bytes = await pdf_file.read()

    start_batch_pipeline_from_pdf(
        pdf_file_bytes=file_bytes,
        original_filename=pdf_file.filename or "",
    )

    return ResponseBuilder.success(
        data=PipelineStartResponse(
            context_id="",
            status=PipelineStatus.STARTED,
            message=f"PDF 파일 OCR 처리 시작됨: {pdf_file.filename}",
        )
    )


@router.post("/extract-images")
async def run_ocr_images_extract_async(
    image_response_list: list[ImageResponse] = Body(...),
    common_service=Depends(get_common_service),
):
    """
    이미지 리스트 OCR 비동기 처리

    여러 이미지를 배치로 처리합니다.
    """

    result_img = []
    for image_response in image_response_list:
        image_data = await common_service.load_image(
            image_path=image_response.private_img
        )

        result_img.append(image_data)

    model = get_ocr_model()
    result = model.predict_batch(
        result_img,
        confidence_threshold=0.5,
    )

    logger.info(result)

    return ResponseBuilder.success(
        data=PipelineStartResponse(
            context_id="",
            status=PipelineStatus.STARTED,
            message=f"배치 파이프라인 시작됨: {len(image_response_list)}개 이미지",
        )
    )


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


@router.get("/result/{task_id}")
async def get_ocr_task_result(task_id: str):
    """
    태스크 결과 조회

    Args:
        task_id: Celery 태스크 ID

    Returns:
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
            return ResponseBuilder.success(
                data=TestResultDTO(
                    task_id=task_id, status=PipelineStatus.SUCCESS, result=result
                ),
                message="태스크 완료",
            )
        else:
            # 실패
            error = str(async_result.result)
            logger.error(f"❌ OCR 태스크 실패: task_id={task_id}, error={error}")
            return ResponseBuilder.success(
                data=TestResultDTO(
                    task_id=task_id, status=PipelineStatus.FAILURE, result=error
                ),
                message="태스크 실패",
            )
    else:
        # 진행 중
        logger.info(f"⏳ OCR 태스크 진행 중: task_id={task_id}")
        return ResponseBuilder.success(
            data=TestResultDTO(
                task_id=task_id, status=PipelineStatus.PENDING, result=""
            ),
            message="태스크 진행 중",
        )


@router.get("/cancel/{task_id}")
async def cancel_task_result(task_id: str):
    """
    태스크 취소

    Args:
        task_id: Celery 태스크 ID

    """
    logger.info(f"🔍 OCR 태스크 결과 조회: task_id={task_id}")

    # Celery 클라이언트 가져오기
    celery_client = get_celery_client()
    result = celery_client.celery_app.control.revoke(task_id, terminate=True)
    logger.info(result)

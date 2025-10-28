# app/domains/ocr/controllers/ocr_controller.py
from fastapi import APIRouter, Body, Depends
from ml_app.core.celery_client import get_celery_client
from ml_app.models.ocr_model import get_ocr_model
from shared.core.database import get_db
from shared.core.logging import get_logger
from shared.schemas.common import ImageResponse
from shared.service.common_service import CommonService, get_common_service
from shared.utils.response_builder import ResponseBuilder
from sqlalchemy.ext.asyncio import AsyncSession

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
    # logger.info(f"OCR 실행 시작: 이미지 크기 {len(image_data)} bytes")
    image_data = await common_service.load_image(private_image_path)
    model = get_ocr_model(use_angle_cls=use_angle_cls, lang=language)
    result = model.predict(image_data, confidence_threshold)
    return result



@router.post("/extract-pdf")
async def run_ocr_pdf_extract_async(
    chain_id: str = Body(...),
    image_response_list: list[ImageResponse] = Body(...),
):
    """
    OCR 비동기 처리 (Celery 태스크)

    태스크를 Celery에 전송하고 즉시 task_id를 반환합니다.
    결과는 /ocr/result/{task_id}로 조회할 수 있습니다.
    """

    logger.info(f"image_response : {image_response_list}",  )
    # logger.info(f"🚀 OCR 비동기 태스크 전송: {private_image_path}")

    # Celery 클라이언트 가져오기
    # celery_client = get_celery_client()

    # 태스크 전송
    # celery_client.send_task(
    #     "tasks.start_pipeline",
    #     file_path=private_image_path,
    #     public_file_path=public_image_path,
    #     options={},
    # )

    return ResponseBuilder.success(
        data="",
        message="태스크 전송 완료",
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

    # Celery 클라이언트 가져오기
    celery_client = get_celery_client()

    # 태스크 전송
    celery_client.send_task(
        "tasks.start_pipeline",
        file_path=private_image_path,
        public_file_path=public_image_path,
        options={},
    )

    return ResponseBuilder.success(
        data="",
        message="태스크 전송 완료",
    )


@router.get("/result/{task_id}")
async def get_ocr_task_result(task_id: str):
    """
    OCR 태스크 결과 조회

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
            result = async_result.result
            logger.info(f"✅ OCR 태스크 완료: task_id={task_id}")
            return ResponseBuilder.success(
                data={
                    "task_id": task_id,
                    "status": "completed",
                    "result": result,
                },
                message="태스크 완료",
            )
        else:
            # 실패
            error = str(async_result.result)
            logger.error(f"❌ OCR 태스크 실패: task_id={task_id}, error={error}")
            return ResponseBuilder.success(
                data={
                    "task_id": task_id,
                    "status": "failed",
                    "error": error,
                },
                message="태스크 실패",
            )
    else:
        # 진행 중
        logger.info(f"⏳ OCR 태스크 진행 중: task_id={task_id}")
        return ResponseBuilder.success(
            data={
                "task_id": task_id,
                "status": "pending",
                "message": "태스크가 아직 처리 중입니다.",
            },
            message="태스크 진행 중",
        )

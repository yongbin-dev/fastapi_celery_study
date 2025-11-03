# app/domains/ocr/controllers/ocr_controller.py
from app.domains.pipeline.schemas.pipeline_schemas import PipelineStartResponse
from fastapi import APIRouter, Body, Depends
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
from tasks.batch_tasks import start_batch_pipeline as start_batch

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
    logger.info(f"model_result: {result}")
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

    # ImageResponse 객체에서 private_img 경로만 추출

    # 2. 배치 파이프라인 시작
    options = {}  # 필요시 옵션 추가
    batch_id = start_batch(
        batch_name=chain_id,
        image_response_list=image_response_list,
        options=options,
        chunk_size=10,
        initiated_by="ml_server",
    )

    logger.info(
        f"배치 파이프라인 시작: batch_id={batch_id}, "
        f"batch_name={batch_id}, files={len(image_response_list)}"
    )

    return ResponseBuilder.success(
        data=PipelineStartResponse(
            context_id="",
            status=PipelineStatus.STARTED,
            message=f"배치 파이프라인 시작됨: {len(image_response_list)}개 이미지",
        )
    )
    # except Exception as e:
    #     logger.error(f"배치 파이프라인 시작 실패: {str(e)}")
    #     raise HTTPException(status_code=500, detail=str(e))


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

@router.get("/test-async")
async def run_test_task_async():

    # Celery 클라이언트 가져오기
    celery_client = get_celery_client()

    result = celery_client.send_task(
        "tasks.test_tasks",
        options={},
    )

    task_id = result.id  # AsyncResult 객체에서 ID 문자열 추출
    logger.info(f"Task ID: {task_id}")

    return ResponseBuilder.success(
        data={
            "task_id": task_id  # 문자열 키와 문자열 값으로 변경
        },
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
                                task_id=task_id ,
                                status = PipelineStatus.SUCCESS,
                                result=result
                            ),
                message="태스크 완료",
            )
        else:
            # 실패
            error = str(async_result.result)
            logger.error(f"❌ OCR 태스크 실패: task_id={task_id}, error={error}")
            return ResponseBuilder.success(
                data=TestResultDTO(
                    task_id=task_id ,
                    status = PipelineStatus.FAILURE,
                    result=error
                ),
                message="태스크 실패",
            )
    else:
        # 진행 중
        logger.info(f"⏳ OCR 태스크 진행 중: task_id={task_id}")
        return ResponseBuilder.success(
            data=TestResultDTO(
                task_id=task_id ,
                status = PipelineStatus.PENDING,
                result=""
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
    result = celery_client.celery_app.control.revoke(
        task_id,
        terminate=True
    )
    logger.info(result)


# app/domains/task/controllers/task_controller.py
import uuid

from celery import Celery
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from shared.config import settings
from shared.core.database import get_db
from shared.core.logging import get_logger
from shared.pipeline.cache import get_pipeline_cache_service
from shared.repository.crud.async_crud import chain_execution_crud
from shared.service.common_service import CommonService, get_common_service
from shared.utils.response_builder import ResponseBuilder
from sqlalchemy.ext.asyncio import AsyncSession
from tasks.batch.image_tasks import start_image_batch_pipeline

logger = get_logger(__name__)

router = APIRouter(prefix="/task", tags=["TASK"])


def _validate_content_type(content_type: str | None, filename: str) -> None:
    """파일 Content-Type 검증

    Args:
        content_type: 파일의 Content-Type
        filename: 파일명

    Raises:
        HTTPException: Content-Type이 허용되지 않는 경우
    """
    if content_type not in settings.ALLOWED_PDF_CONTENT_TYPES:
        logger.warning(
            f"⚠️ 잘못된 파일 형식: filename={filename}, content_type={content_type}"
        )
        raise HTTPException(
            status_code=400,
            detail=f"PDF 파일만 업로드 가능합니다. (현재: {content_type})",
        )


def _validate_file_size(file_size: int, filename: str) -> None:
    """파일 크기 검증

    Args:
        file_size: 파일 크기 (바이트)
        filename: 파일명

    Raises:
        HTTPException: 파일 크기가 0이거나 최대 크기를 초과할 경우
    """
    if file_size == 0:
        logger.warning(f"⚠️ 빈 파일 업로드 시도: filename={filename}")
        raise HTTPException(status_code=400, detail="빈 파일은 업로드할 수 없습니다.")

    if file_size > settings.MAX_PDF_FILE_SIZE:
        max_size_mb = settings.MAX_PDF_FILE_SIZE / (1024 * 1024)
        current_size_mb = file_size / (1024 * 1024)
        logger.warning(
            f"⚠️ 파일 크기 초과: filename={filename}, "
            f"size={current_size_mb:.2f}MB (최대: {max_size_mb}MB)"
        )
        raise HTTPException(
            status_code=413,
            detail=(
                f"파일 크기가 너무 큽니다. "
                f"(최대: {max_size_mb}MB, 현재: {current_size_mb:.2f}MB)"
            ),
        )


@router.post("/extract-pdf")
async def run_ocr_pdf_extract_async(
    pdf_file: UploadFile = File(...),
    common_service: CommonService = Depends(get_common_service),
):
    """
    PDF 파일 OCR 비동기 처리

    PDF 파일을 업로드받아 이미지로 변환 후 OCR을 수행합니다.

    Args:
        pdf_file: 업로드된 PDF 파일 (최대 50MB)

    Returns:
        batch_id: 배치 작업 ID

    Raises:
        HTTPException: 파일 검증 실패 또는 처리 중 오류 발생
    """
    batch_id = str(uuid.uuid4())
    filename = pdf_file.filename or "unknown.pdf"

    try:
        # 1. Content-Type 검증
        _validate_content_type(pdf_file.content_type, filename)

        # 2. 파일 읽기
        file_bytes = await pdf_file.read()
        file_size = len(file_bytes)

        # 3. 파일 크기 검증
        _validate_file_size(file_size, filename)

        logger.info(
            f"📄 PDF 파일 업로드 시작: batch_id={batch_id}, "
            f"filename={filename}, size={file_size / 1024:.2f}KB"
        )

        # 1. PDF를 이미지로 변환
        image_responses = await common_service.save_pdf(
            original_filename=filename,
            pdf_file_bytes=file_bytes,
        )

        batch_name = f"{filename}_{uuid.uuid4().hex[:8]}"
        chunk_size = 10

        # 4. Celery 태스크 전송
        task_id = await start_image_batch_pipeline(
            batch_id=batch_id,
            batch_name=batch_name,
            image_responses=image_responses,
            chunk_size=chunk_size,
            initiated_by="pdf_converter",
            options={},
        )

        logger.info(
            f"✅ PDF 배치 작업 시작: batch_id={batch_id}, "
            f"task_id={task_id}, filename={filename}"
        )

        return ResponseBuilder.success(
            data={"batch_id": batch_id, "task_id": task_id, "filename": filename},
            message="PDF 파일 처리가 시작되었습니다.",
        )

    except Exception as e:
        logger.error(
            f"❌ PDF 파일 처리 실패: batch_id={batch_id}, "
            f"filename={filename}, error={str(e)}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail=f"PDF 파일 처리 중 오류가 발생했습니다: {str(e)}"
        )


# batch_id로 모든 컨텍스트 조회
@router.get("/batch/{batch_id}")
async def get_batch_contexts(
    batch_id: str, cache_service=Depends(get_pipeline_cache_service)
):
    """
    batch_id로 모든 파이프라인 컨텍스트 조회 (진행 중 + 대기 중)

    Args:
        batch_id: 배치 ID

    Returns:
        배치에 속한 모든 파이프라인 컨텍스트 목록 (진행 중 작업 + 대기 중 작업)
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


@router.delete("/cancel/{chain_id}")
async def cancel_task_result(
    chain_id: str,
    session: AsyncSession = Depends(get_db),
):
    """
    태스크 취소

    Args:
        chain_id: chain_id
        session: 데이터베이스 세션

    """
    logger.info(f"🔍 태스크 취소 요청: chain_id={chain_id}")

    # Celery 앱 인스턴스 생성
    celery_app = Celery(broker=settings.REDIS_URL, backend=settings.REDIS_URL)

    chain_exec = await chain_execution_crud.get_by_chain_id(session, chain_id=chain_id)
    if chain_exec is None:
        raise HTTPException(
            status_code=404, detail=f"Chain ID {chain_id}를 찾을 수 없습니다"
        )

    celery_app.control.revoke(chain_exec.celery_task_id, terminate=True)

    return ResponseBuilder.error(
        message="태스크 취소 기능은 아직 구현되지 않았습니다.",
    )

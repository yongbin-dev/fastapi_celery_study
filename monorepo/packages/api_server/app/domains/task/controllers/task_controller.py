# app/domains/task/controllers/task_controller.py
import uuid

from celery import Celery
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from shared.config import settings
from shared.core.database import get_db
from shared.core.logging import get_logger
from shared.pipeline.cache import PipelineCacheService, get_pipeline_cache_service
from shared.repository.crud.async_crud import chain_execution_crud
from shared.utils.response_builder import ResponseBuilder
from sqlalchemy.ext.asyncio import AsyncSession
from tasks import start_pdf_batch_pipeline

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
        content_type = pdf_file.content_type
        if content_type not in settings.ALLOWED_PDF_CONTENT_TYPES:
            logger.warning(
                f"⚠️ 잘못된 파일 형식: filename={filename}, content_type={content_type}"
            )
            raise HTTPException(
                status_code=400,
                detail=f"PDF 파일만 업로드 가능합니다. (현재: {content_type})",
            )

        # 2. 파일 읽기
        file_bytes = await pdf_file.read()
        file_size = len(file_bytes)

        # 3. 파일 크기 검증
        if file_size == 0:
            logger.warning(f"⚠️ 빈 파일 업로드 시도: filename={filename}")
            raise HTTPException(
                status_code=400, detail="빈 파일은 업로드할 수 없습니다."
            )

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

        logger.info(
            f"📄 PDF 파일 업로드 시작: batch_id={batch_id}, "
            f"filename={filename}, size={file_size / 1024:.2f}KB"
        )

        # 4. Celery 태스크 전송
        task_id = start_pdf_batch_pipeline(
            batch_id=batch_id,
            pdf_file_bytes=file_bytes,
            original_filename=filename,
        )

        logger.info(
            f"✅ PDF 배치 작업 시작: batch_id={batch_id}, "
            f"task_id={task_id}, filename={filename}"
        )

        return ResponseBuilder.success(
            data={"batch_id": batch_id, "task_id": task_id, "filename": filename},
            message="PDF 파일 처리가 시작되었습니다.",
        )

    except HTTPException:
        # FastAPI HTTPException은 그대로 전파
        raise

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
    cache_service: PipelineCacheService = Depends(get_pipeline_cache_service),
):
    """
    태스크 취소

    Args:
        chain_id: chain_id
        session: 데이터베이스 세션
        cache_service: 파이프라인 캐시 서비스

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


@router.get("/celery/active")
async def get_active_tasks():
    """현재 실행 중인 Celery 태스크 조회

    Returns:
        현재 실행 중인 태스크 목록
    """
    from shared.schemas.task_status import ActiveTaskInfo, ActiveTasksResponse

    try:
        # Celery 앱 인스턴스 생성
        celery_app = Celery(broker=settings.REDIS_URL, backend=settings.REDIS_URL)

        # 현재 실행 중인 태스크 조회
        inspect = celery_app.control.inspect()
        active_tasks = inspect.active()

        if not active_tasks:
            return ResponseBuilder.success(
                data=ActiveTasksResponse(total_active_tasks=0, tasks=[], workers={}),
                message="현재 실행 중인 태스크가 없습니다",
            )

        # 태스크 정보 수집
        tasks = []
        workers_count = {}

        for worker_name, worker_tasks in active_tasks.items():
            workers_count[worker_name] = len(worker_tasks)

            for task in worker_tasks:
                tasks.append(
                    ActiveTaskInfo(
                        task_id=task.get("id", ""),
                        task_name=task.get("name", ""),
                        worker_name=worker_name,
                        time_start=task.get("time_start"),
                        args=task.get("args", []),
                        kwargs=task.get("kwargs", {}),
                        acknowledged=task.get("acknowledged", False),
                    )
                )

        response = ActiveTasksResponse(
            total_active_tasks=len(tasks), tasks=tasks, workers=workers_count
        )

        return ResponseBuilder.success(
            data=response, message=f"실행 중인 태스크 {len(tasks)}개 조회 완료"
        )

    except Exception as e:
        logger.error(f"활성 태스크 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"태스크 조회 실패: {str(e)}")


@router.get("/celery/reserved")
async def get_reserved_tasks():
    """대기 중인 Celery 태스크 조회

    Returns:
        대기 중인 태스크 목록
    """
    from shared.schemas.task_status import ReservedTaskInfo, ReservedTasksResponse

    try:
        # Celery 앱 인스턴스 생성
        celery_app = Celery(broker=settings.REDIS_URL, backend=settings.REDIS_URL)

        # 대기 중인 태스크 조회
        inspect = celery_app.control.inspect()
        reserved_tasks = inspect.reserved()

        if not reserved_tasks:
            return ResponseBuilder.success(
                data=ReservedTasksResponse(
                    total_reserved_tasks=0, tasks=[], workers={}
                ),
                message="대기 중인 태스크가 없습니다",
            )

        # 태스크 정보 수집
        tasks = []
        workers_count = {}

        for worker_name, worker_tasks in reserved_tasks.items():
            workers_count[worker_name] = len(worker_tasks)

            for task in worker_tasks:
                tasks.append(
                    ReservedTaskInfo(
                        task_id=task.get("id", ""),
                        task_name=task.get("name", ""),
                        worker_name=worker_name,
                        args=task.get("args", []),
                        kwargs=task.get("kwargs", {}),
                        acknowledged=task.get("acknowledged", False),
                    )
                )

        response = ReservedTasksResponse(
            total_reserved_tasks=len(tasks), tasks=tasks, workers=workers_count
        )

        return ResponseBuilder.success(
            data=response, message=f"대기 중인 태스크 {len(tasks)}개 조회 완료"
        )

    except Exception as e:
        logger.error(f"대기 태스크 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"태스크 조회 실패: {str(e)}")


@router.get("/celery/scheduled")
async def get_scheduled_tasks():
    """예약된 Celery 태스크 조회

    Returns:
        예약된 태스크 목록
    """
    from shared.schemas.task_status import ScheduledTaskInfo, ScheduledTasksResponse

    try:
        # Celery 앱 인스턴스 생성
        celery_app = Celery(broker=settings.REDIS_URL, backend=settings.REDIS_URL)

        # 예약된 태스크 조회
        inspect = celery_app.control.inspect()
        scheduled_tasks = inspect.scheduled()

        if not scheduled_tasks:
            return ResponseBuilder.success(
                data=ScheduledTasksResponse(
                    total_scheduled_tasks=0, tasks=[], workers={}
                ),
                message="예약된 태스크가 없습니다",
            )

        # 태스크 정보 수집
        tasks = []
        workers_count = {}

        for worker_name, worker_tasks in scheduled_tasks.items():
            workers_count[worker_name] = len(worker_tasks)

            for task in worker_tasks:
                # scheduled 태스크는 request 객체 안에 정보가 들어있음
                request = task.get("request", {})
                tasks.append(
                    ScheduledTaskInfo(
                        task_id=request.get("id", ""),
                        task_name=request.get("name", ""),
                        worker_name=worker_name,
                        eta=task.get("eta"),
                        args=request.get("args", []),
                        kwargs=request.get("kwargs", {}),
                        priority=task.get("priority"),
                    )
                )

        response = ScheduledTasksResponse(
            total_scheduled_tasks=len(tasks), tasks=tasks, workers=workers_count
        )

        return ResponseBuilder.success(
            data=response, message=f"예약된 태스크 {len(tasks)}개 조회 완료"
        )

    except Exception as e:
        logger.error(f"예약 태스크 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"태스크 조회 실패: {str(e)}")


@router.get("/celery/status")
async def get_all_tasks_status():
    """전체 Celery 태스크 상태 조회 (실행 중 + 대기 중 + 예약)

    Returns:
        전체 태스크 상태 정보
    """
    from shared.schemas.task_status import (
        ActiveTaskInfo,
        ActiveTasksResponse,
        AllTasksStatusResponse,
        ReservedTaskInfo,
        ReservedTasksResponse,
        ScheduledTaskInfo,
        ScheduledTasksResponse,
    )

    try:
        # Celery 앱 인스턴스 생성
        celery_app = Celery(broker=settings.REDIS_URL, backend=settings.REDIS_URL)
        inspect = celery_app.control.inspect()

        # 모든 태스크 정보 조회
        active_tasks_data = inspect.active() or {}
        reserved_tasks_data = inspect.reserved() or {}
        scheduled_tasks_data = inspect.scheduled() or {}

        # 1. Active tasks 처리
        active_tasks = []
        active_workers = {}
        for worker_name, worker_tasks in active_tasks_data.items():
            active_workers[worker_name] = len(worker_tasks)
            for task in worker_tasks:
                active_tasks.append(
                    ActiveTaskInfo(
                        task_id=task.get("id", ""),
                        task_name=task.get("name", ""),
                        worker_name=worker_name,
                        time_start=task.get("time_start"),
                        args=task.get("args", []),
                        kwargs=task.get("kwargs", {}),
                        acknowledged=task.get("acknowledged", False),
                    )
                )

        # 2. Reserved tasks 처리
        reserved_tasks = []
        reserved_workers = {}
        for worker_name, worker_tasks in reserved_tasks_data.items():
            reserved_workers[worker_name] = len(worker_tasks)
            for task in worker_tasks:
                reserved_tasks.append(
                    ReservedTaskInfo(
                        task_id=task.get("id", ""),
                        task_name=task.get("name", ""),
                        worker_name=worker_name,
                        args=task.get("args", []),
                        kwargs=task.get("kwargs", {}),
                        acknowledged=task.get("acknowledged", False),
                    )
                )

        # 3. Scheduled tasks 처리
        scheduled_tasks = []
        scheduled_workers = {}
        for worker_name, worker_tasks in scheduled_tasks_data.items():
            scheduled_workers[worker_name] = len(worker_tasks)
            for task in worker_tasks:
                request = task.get("request", {})
                scheduled_tasks.append(
                    ScheduledTaskInfo(
                        task_id=request.get("id", ""),
                        task_name=request.get("name", ""),
                        worker_name=worker_name,
                        eta=task.get("eta"),
                        args=request.get("args", []),
                        kwargs=request.get("kwargs", {}),
                        priority=task.get("priority"),
                    )
                )

        # 응답 구성
        response = AllTasksStatusResponse(
            active=ActiveTasksResponse(
                total_active_tasks=len(active_tasks),
                tasks=active_tasks,
                workers=active_workers,
            ),
            reserved=ReservedTasksResponse(
                total_reserved_tasks=len(reserved_tasks),
                tasks=reserved_tasks,
                workers=reserved_workers,
            ),
            scheduled=ScheduledTasksResponse(
                total_scheduled_tasks=len(scheduled_tasks),
                tasks=scheduled_tasks,
                workers=scheduled_workers,
            ),
            total_tasks=len(active_tasks) + len(reserved_tasks) + len(scheduled_tasks),
        )

        return ResponseBuilder.success(
            data=response,
            message=(
                f"전체 태스크 상태 조회 완료 "
                f"(실행: {len(active_tasks)}, 대기: {len(reserved_tasks)}, "
                f"예약: {len(scheduled_tasks)})"
            ),
        )

    except Exception as e:
        logger.error(f"전체 태스크 상태 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"태스크 조회 실패: {str(e)}")

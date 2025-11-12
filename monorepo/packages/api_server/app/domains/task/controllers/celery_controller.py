# app/domains/task/controllers/task_controller.py

from celery import Celery
from fastapi import APIRouter, HTTPException
from shared.config import settings
from shared.core.logging import get_logger
from shared.utils.response_builder import ResponseBuilder

logger = get_logger(__name__)

router = APIRouter(prefix="/celery", tags=["CELERY"])


@router.get("/active")
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


@router.get("/reserved")
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


@router.get("/scheduled")
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


@router.get("/status")
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

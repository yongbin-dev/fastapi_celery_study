# services/task_service.py

import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

import redis
from fastapi import HTTPException

from ..core.celery_app import celery_app
from ..core.config import settings
from ..schemas.tasks import (
    TaskHistoryResponse, TaskInfo, TaskStatistics, TaskFilters,
    AIPipelineRequest, AIPipelineResponse, PipelineStatusResponse,
    StageStatus, PipelineProgress
)


class TaskService:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=0,
            decode_responses=True
        )

    def create_example_task(self, message: str, delay: int = 5) -> Dict[str, Any]:
        """예제 태스크 생성"""
        task = celery_app.send_task(
            "app.tasks.example_task",
            args=[message, delay]
        )

        return {
            "task_id": task.id,
            "status": "PENDING",
            "message": "Task created successfully"
        }

    def create_long_task(self, total_steps: int = 10) -> Dict[str, Any]:
        """긴 시간 소요 태스크 생성"""
        task = celery_app.send_task(
            "app.tasks.long_running_task",
            args=[total_steps]
        )

        return {
            "task_id": task.id,
            "status": "PENDING",
            "message": "Long running task created"
        }

    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """태스크 상태 조회"""
        result = celery_app.AsyncResult(task_id)

        if result.state == 'PENDING':
            return {
                "task_id": task_id,
                "status": result.state,
                "message": "Task is waiting to be processed"
            }
        elif result.state == 'PROGRESS':
            return {
                "task_id": task_id,
                "status": result.state,
                "current": result.info.get('current', 0),
                "total": result.info.get('total', 1),
                "message": result.info.get('status', '')
            }
        elif result.state == 'SUCCESS':
            return {
                "task_id": task_id,
                "status": result.state,
                "result": result.info,
                "message": "Task completed successfully"
            }
        else:  # FAILURE
            return {
                "task_id": task_id,
                "status": result.state,
                "error": str(result.info),
                "message": "Task failed"
            }

    def cancel_task(self, task_id: str) -> Dict[str, Any]:
        """태스크 취소"""
        celery_app.control.revoke(task_id, terminate=True)

        return {
            "task_id": task_id,
            "message": "Task cancellation requested"
        }

    def list_active_tasks(self) -> Dict[str, Any]:
        """활성 태스크 목록 조회"""
        inspect = celery_app.control.inspect()
        active_tasks = inspect.active()

        if active_tasks:
            tasks_list = []
            for worker, tasks in active_tasks.items():
                for task in tasks:
                    tasks_list.append({
                        "task_id": task["id"],
                        "name": task["name"],
                        "worker": worker,
                        "args": task["args"],
                        "kwargs": task["kwargs"]
                    })
        else:
            tasks_list = []

        return {
            "active_tasks": tasks_list,
            "total_count": len(tasks_list)
        }

    def _detect_task_name(self, task_result: Dict[str, Any]) -> str:
        """태스크 결과에서 태스크 이름 추출"""
        if not isinstance(task_result, dict):
            return "Unknown"

        message = task_result.get('message', '')

        if 'Simple task completed' in message:
            return "app.tasks.simple_task"
        elif 'Task completed' in message:
            return "app.tasks.example_task"
        elif 'AI processed' in message:
            return "app.tasks.ai_processing_task"
        elif 'sent' in str(task_result.get('status', '')):
            return "app.tasks.send_email_task"
        elif task_result.get('status') == 'completed' and 'total_steps' in task_result:
            return "app.tasks.long_running_task"

        return "Unknown"

    def _parse_task_time(self, date_done: str) -> Optional[datetime]:
        """태스크 완료 시간 파싱"""
        try:
            if date_done.endswith('Z'):
                task_time = datetime.fromisoformat(date_done.replace('Z', '+00:00'))
            else:
                task_time = datetime.fromisoformat(date_done)

            return task_time.replace(tzinfo=None)
        except:
            return datetime.now()

    def get_tasks_history(
            self,
            hours: int = 1,
            status: Optional[str] = None,
            task_name: Optional[str] = None,
            limit: int = 100
    ) -> TaskHistoryResponse:
        """태스크 히스토리 조회"""

        # 시간 범위 계산
        cutoff_time = datetime.now() - timedelta(hours=hours)

        # 모든 Celery 결과 키 조회
        keys = self.redis_client.keys('celery-task-meta-*')

        if not keys:
            return TaskHistoryResponse(
                tasks=[],
                statistics=TaskStatistics(
                    total_found=0,
                    returned_count=0,
                    time_range=f"Last {hours} hour(s)",
                    by_status={},
                    by_task_type={},
                    current_active={
                        "active_tasks": 0,
                        "scheduled_tasks": 0,
                        "reserved_tasks": 0
                    },
                    workers=[]
                ),
                filters_applied=TaskFilters(
                    hours=hours,
                    status=status,
                    task_name=task_name,
                    limit=limit
                )
            )

        # 태스크 데이터 수집 및 필터링
        filtered_tasks = []
        status_counts = {}
        task_type_counts = {}
        task_list = []

        for key in keys:
            try:
                result_data = self.redis_client.get(key)
                if not result_data:
                    continue

                result = json.loads(result_data)
                task_id = key.replace('celery-task-meta-', '')

                # 날짜 필터링
                date_done = result.get('date_done')
                if not date_done:
                    continue

                task_time_local = self._parse_task_time(date_done)
                if task_time_local < cutoff_time:
                    continue

                task_status = result.get('status', 'UNKNOWN')
                task_result = result.get('result', {})
                detected_task_name = self._detect_task_name(task_result)

                # 필터링
                if status and task_status != status:
                    continue
                if task_name and task_name not in detected_task_name:
                    continue

                # 태스크 정보 구성
                task_info = TaskInfo(
                    task_id=task_id,
                    status=task_status,
                    task_name=detected_task_name,
                    date_done=date_done,
                    result=task_result,
                    traceback=result.get('traceback'),
                    task_time=task_time_local.isoformat()
                )

                filtered_tasks.append(task_info)

                # 통계 집계
                status_counts[task_status] = status_counts.get(task_status, 0) + 1
                task_type_counts[detected_task_name] = task_type_counts.get(detected_task_name, 0) + 1

            except Exception:
                continue

        # 시간순 정렬 (최신순)
        # filtered_tasks.sort(key=lambda x: x['task_time'], reverse=True)

        # 제한된 수만큼만 반환
        # limited_tasks = filtered_tasks[2]

        # 현재 활성 태스크 정보
        inspect = celery_app.control.inspect()
        active_tasks = inspect.active() or {}
        scheduled_tasks = inspect.scheduled() or {}
        reserved_tasks = inspect.reserved() or {}

        active_count = sum(len(tasks) for tasks in active_tasks.values())
        scheduled_count = sum(len(tasks) for tasks in scheduled_tasks.values())
        reserved_count = sum(len(tasks) for tasks in reserved_tasks.values())

        # 워커 통계
        worker_stats = inspect.stats() or {}

        # Pydantic 모델로 변환
        # tasks = [TaskInfo(**task_info) for task_info in limited_tasks]

        statistics = TaskStatistics(
            total_found=len([]),
            returned_count=len([]),
            time_range=f"Last {hours} hour(s)",
            by_status=status_counts,
            by_task_type=task_type_counts,
            current_active={
                "active_tasks": active_count,
                "scheduled_tasks": scheduled_count,
                "reserved_tasks": reserved_count
            },
            workers=list(worker_stats.keys()) if worker_stats else []
        )

        filters_applied = TaskFilters(
            hours=hours,
            status=status,
            task_name=task_name,
            limit=limit
        )

        return TaskHistoryResponse(
            tasks=task_list,
            statistics=statistics,
            filters_applied=filters_applied
        )

    def create_ai_pipeline(self, request: AIPipelineRequest) -> AIPipelineResponse:
        """AI 처리 파이프라인 시작"""
        input_data = {
            "text": request.text,
            "options": request.options,
            "priority": request.priority,
            "callback_url": request.callback_url
        }

        # 오케스트레이터 태스크 시작
        task = celery_app.send_task(
            "app.tasks.ai_pipeline_orchestrator",
            args=[input_data]
        )

        # Redis에 파이프라인 상태 초기화
        pipeline_key = f"pipeline:{task.id}"
        initial_state = {
            "pipeline_id": task.id,
            "status": "STARTED",
            "current_stage": 0,
            "total_stages": 4,
            "start_time": datetime.now().isoformat(),
            "stages": [
                {"stage": 1, "stage_name": "데이터 전처리", "status": "PENDING", "progress": 0},
                {"stage": 2, "stage_name": "특성 추출", "status": "PENDING", "progress": 0},
                {"stage": 3, "stage_name": "모델 추론", "status": "PENDING", "progress": 0},
                {"stage": 4, "stage_name": "후처리", "status": "PENDING", "progress": 0}
            ]
        }

        self.redis_client.setex(
            pipeline_key,
            3600,  # 1시간 TTL
            json.dumps(initial_state)
        )

        return AIPipelineResponse(
            pipeline_id=task.id,
            status="STARTED",
            message="AI 처리 파이프라인이 시작되었습니다",
            estimated_duration=20  # 예상 20초
        )

    def get_pipeline_status(self, pipeline_id: str) -> PipelineStatusResponse:
        """파이프라인 진행 상태 조회"""
        # Redis에서 파이프라인 상태 조회
        pipeline_key = f"pipeline:{pipeline_id}"
        pipeline_data = self.redis_client.get(pipeline_key)

        if not pipeline_data:
            # Celery 결과에서 직접 조회
            result = celery_app.AsyncResult(pipeline_id)

            if result.state == 'PENDING':
                return PipelineStatusResponse(
                    pipeline_id=pipeline_id,
                    status="PENDING",
                    current_stage=0,
                    current_stage_name="대기 중",
                    overall_progress=0,
                    stages=[]
                )
            elif result.state == 'SUCCESS':
                return PipelineStatusResponse(
                    pipeline_id=pipeline_id,
                    status="SUCCESS",
                    current_stage=4,
                    current_stage_name="완료",
                    overall_progress=100,
                    stages=[],
                    result=result.info
                )
            elif result.state == 'FAILURE':
                return PipelineStatusResponse(
                    pipeline_id=pipeline_id,
                    status="FAILURE",
                    current_stage=0,
                    current_stage_name="실패",
                    overall_progress=0,
                    stages=[],
                    error=str(result.info)
                )

        pipeline_state = json.loads(pipeline_data)

        # 현재 단계 정보 업데이트
        current_stage = self._get_current_pipeline_stage(pipeline_id)
        overall_progress = self._calculate_overall_progress(pipeline_state.get('stages', []))

        stages = [StageStatus(**stage) for stage in pipeline_state.get('stages', [])]

        return PipelineStatusResponse(
            pipeline_id=pipeline_id,
            status=pipeline_state.get('status', 'UNKNOWN'),
            current_stage=current_stage,
            current_stage_name=self._get_stage_name(current_stage),
            overall_progress=overall_progress,
            stages=stages
        )

    def _get_current_pipeline_stage(self, pipeline_id: str) -> int:
        """현재 실행 중인 단계 확인"""
        # 체인의 각 단계 상태 확인
        stage_tasks = [
            f"app.tasks.stage1_preprocessing",
            f"app.tasks.stage2_feature_extraction",
            f"app.tasks.stage3_model_inference",
            f"app.tasks.stage4_post_processing"
        ]

        # 간단한 로직으로 현재 단계 추정
        result = celery_app.AsyncResult(pipeline_id)
        if result.state == 'SUCCESS':
            return 4
        elif result.state == 'PROGRESS' and result.info:
            return result.info.get('stage', 1)
        else:
            return 1

    def _calculate_overall_progress(self, stages: List[Dict]) -> int:
        """전체 진행률 계산"""
        if not stages:
            return 0

        total_progress = sum(stage.get('progress', 0) for stage in stages)
        return min(100, total_progress // len(stages))

    def _get_stage_name(self, stage: int) -> str:
        """단계 번호에 따른 단계명 반환"""
        stage_names = {
            0: "대기 중",
            1: "데이터 전처리",
            2: "특성 추출",
            3: "모델 추론",
            4: "후처리"
        }
        return stage_names.get(stage, "알 수 없음")


# 전역 서비스 인스턴스
task_service = TaskService()


# 의존성 주입 함수
def get_task_service() -> TaskService:
    """Task 서비스 의존성"""
    return task_service

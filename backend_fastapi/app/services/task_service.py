# services/task_service.py

import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

import redis
from celery.result import AsyncResult
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.celery_app import celery_app
from ..core.config import settings
from ..models.task_info import TaskInfo
from ..schemas.tasks import (
    TaskHistoryResponse, TaskStatistics, AIPipelineRequest, AIPipelineResponse
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

    async def get_tasks_history(
            self,
            db: AsyncSession,
            hours: int = 1,
            status: Optional[str] = None,
            task_name: Optional[str] = None,
            limit: int = 100,
    ) -> TaskHistoryResponse:
        """태스크 히스토리 조회"""

        # 시간 범위 계산
        cutoff_time = datetime.now() - timedelta(hours=hours)

        stmt =  select(TaskInfo)
        result = await db.execute(stmt)
        taskInfos = result.scalars().all()

        task_datas = [taskInfo.dict() for taskInfo in taskInfos]

        logging.info(task_datas)
        return TaskHistoryResponse(
            tasks=task_datas,
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

    def get_pipeline_status(self, pipeline_id: str) -> Any:

        result = celery_app.AsyncResult(pipeline_id)

        detailed_tasks = []
        current = result

        while current:
            task_detail = {
                "task_id": current.id,
                "status": current.status,
            }

            # PROGRESS 상태인 경우 세부 정보
            if current.status == "PROGRESS" and hasattr(current, 'info'):
                task_detail.update({
                    "current_progress": current.info.get('current', 0),
                    "total_progress": current.info.get('total', 100),
                    "step_name": current.info.get('step_name', ''),
                    "description": current.info.get('description', ''),
                    "percentage": (current.info.get('current', 0) / current.info.get('total', 1)) * 100
                })

            detailed_tasks.append(task_detail)
            current = current.parent

        detailed_tasks.reverse()

        return {
            "chain_id": pipeline_id,
            "tasks": detailed_tasks
        }

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

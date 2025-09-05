# services/task_service.py

import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional

import redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.celery_app import celery_app
from ..core.config import settings
from ..schemas.tasks import (
    AIPipelineRequest, AIPipelineResponse, PipelineStatusResponse, TaskStatusResponse
)
from ..models.task_info import TaskInfo


class TaskService:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=0,
            decode_responses=True
        )

    async def get_tasks_from_db(
        self,
        db: AsyncSession,
        hours: int,
        status: Optional[str] = None,
        task_name: Optional[str] = None,
        limit: int = 100,
    ) -> list[PipelineStatusResponse]:
        """DB에서 TaskInfo 조회하여 PipelineStatusResponse 형태로 반환"""
        try:
            from datetime import datetime, timedelta
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            # TaskInfo 조회 쿼리 구성
            query = select(TaskInfo)
            
            # 필터링 조건 추가
            if status:
                query = query.where(TaskInfo.status == status)
            if task_name:
                query = query.where(TaskInfo.task_name.ilike(f"%{task_name}%"))
            
            # 최신순으로 정렬하고 제한
            query = query.order_by(TaskInfo.id.asc()).limit(limit)
            result = await db.execute(query)
            task_infos = result.scalars().all()
            
            # TaskInfo를 PipelineStatusResponse로 변환
            pipeline_groups = {}
            
            for task_info in task_infos:
                pipeline_id = task_info.pipeline_id or task_info.task_id or "unknown"

                if pipeline_id not in pipeline_groups:
                    pipeline_groups[pipeline_id] = {
                        "pipeline_id": pipeline_id,
                        "tasks": [],
                        "overall_state": "UNKNOWN",
                        "total_steps": 0,
                        "current_stage": 0,
                        "start_time": task_info.created_at
                    }
                
                # TaskStatusResponse 생성
                task_status = TaskStatusResponse(
                    task_id=task_info.task_id,
                    status=task_info.status,
                    task_name=task_info.stages,
                    stages=task_info.stages,
                    traceback=task_info.traceback,
                    step=task_info.step,
                    ready=task_info.ready,
                    progress=task_info.progress or 0,
                )

                pipeline_groups[pipeline_id]["tasks"].append(task_status)
                pipeline_groups[pipeline_id]["total_steps"] += 1
                pipeline_groups[pipeline_id]["current_stage"] += (1 if task_status.status == 'SUCCESS' else 0)
                
                # 전체 상태 업데이트 (가장 최근 상태 사용)
                if task_info.status:
                    pipeline_groups[pipeline_id]["overall_state"] = task_info.status
            
            # PipelineStatusResponse 리스트 생성
            pipelines = []
            for group_data in pipeline_groups.values():
                pipelines.append(PipelineStatusResponse(
                    pipeline_id=group_data["pipeline_id"],
                    overall_state=group_data["overall_state"],
                    total_steps=group_data["total_steps"],
                    current_stage=group_data["current_stage"],
                    start_time=group_data["start_time"],
                    tasks=group_data["tasks"]
                ))
            
            return pipelines
                
        except Exception as e:
            logging.error(f"DB-based task history lookup failed: {e}")
            return []

    def get_tasks_from_redis(
        self,
        hours: int,
        status: Optional[str] = None,
        task_name: Optional[str] = None,
        limit: int = 100,
    ) -> list[PipelineStatusResponse]:
        """Redis에서 파이프라인 상태 조회"""
        try:
            # 1. Celery task result keys 조회
            task_keys = self.redis_client.keys("pipeline*")
            tasks = []

            # 2. 각 태스크 정보 조회
            for task_key in task_keys[:limit]:  # 제한 적용
                try:
                    pipeline_data = self.redis_client.get(task_key)
                    if not pipeline_data:
                        continue

                    pipeline_id = task_key.replace("pipeline:", "")
                    state_info = json.loads(pipeline_data)
                    
                    # 시간 필터링 (Redis 데이터에 start_time이 있는 경우)
                    if hours <= 1 and "start_time" in state_info:
                        try:
                            from datetime import datetime, timedelta
                            start_time = datetime.fromisoformat(state_info["start_time"])
                            cutoff_time = datetime.now() - timedelta(hours=hours)
                            if start_time < cutoff_time:
                                continue
                        except Exception:
                            # 시간 파싱 실패 시 계속 진행
                            pass

                    # 각 파이프라인마다 새로운 tasks_history 생성
                    tasks_history = []
                    for stage in state_info.get("stages", []):
                        # 상태 및 태스크 이름 필터링
                        if status and stage.get("status") != status:
                            continue
                        if task_name and task_name.lower() not in stage.get("stage_name", "").lower():
                            continue
                            
                        tasks_history.append(TaskStatusResponse(
                            task_id=f"{pipeline_id}_{stage['stage']}",
                            status=stage["status"],
                            task_name=stage["stage_name"],
                            stages="",
                            step=stage["stage"],
                            ready=stage["status"] in ["SUCCESS", "FAILURE"],
                            progress=stage.get("progress", 0)
                        ))

                    if tasks_history:  # 필터링 후 남은 태스크가 있는 경우만 추가
                        tasks.append(PipelineStatusResponse(
                            pipeline_id=pipeline_id,
                            overall_state=state_info["status"],
                            total_steps=state_info["total_stages"],
                            current_stage=state_info.get("current_stage", 0),
                            start_time=state_info.get("start_time"),
                            tasks=tasks_history
                        ))

                except Exception as e:
                    logging.warning(f"Failed to process task {task_key}: {e}")
                    continue

            # 3. 시간 순으로 정렬 (최신순)
            tasks.sort(key=lambda x: x.start_time or "", reverse=True)
            
            logging.info(f"Retrieved {len(tasks)} pipelines from Redis")
            return tasks
            
        except Exception as e:
            logging.error(f"Redis-based task history lookup failed: {e}")
            return []

    async def get_tasks_history(
        self,
        db: AsyncSession,
        hours: int = 1,
        status: Optional[str] = None,
        task_name: Optional[str] = None,
        limit: int = 100,
    ) -> list[PipelineStatusResponse]:
        """
        태스크 히스토리 조회
        - 1시간 이내: Redis에서 조회 (실시간 데이터)
        - 1시간 초과: DB에서 조회 (영구 저장 데이터)
        """
        try:
            if hours <= 1:
                # 1시간 이내: Redis에서 조회
                redis_results = self.get_tasks_from_redis(hours, status, task_name, limit)
                return redis_results
                
            else:
                # 1시간 초과: DB에서 조회
                return await self.get_tasks_from_db(db, hours, status, task_name, limit)
                
        except Exception as e:
            logging.error(f"Task history lookup failed: {e}")
            # 실패 시 빈 리스트 반환
            return []

    def create_ai_pipeline(self, request: AIPipelineRequest) -> AIPipelineResponse:
        """AI 처리 파이프라인 시작"""
        input_data = {
            "text": request.text,
            "options": request.options,
            "priority": request.priority,
            "callback_url": request.callback_url,
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
        """Redis 기반 파이프라인 상태 조회"""
        try:
            # Redis에서 파이프라인 상태 조회
            pipeline_key = f"pipeline:{pipeline_id}"
            pipeline_data = self.redis_client.get(pipeline_key)
            
            if pipeline_data:
                # Redis에 상태 정보가 있는 경우
                state_info = json.loads(pipeline_data)
                
                # 단계별 태스크 정보 생성
                tasks = []
                for stage in state_info.get("stages", []):
                    tasks.append(TaskStatusResponse(
                        task_id=f"{pipeline_id}_{stage['stage']}",
                        status=stage["status"],
                        task_name=stage["stage_name"],
                        stages="",
                        step=stage["stage"],
                        ready=stage["status"] in ["SUCCESS", "FAILURE"],
                        progress=stage.get("progress", 0)
                    ))
                
                return PipelineStatusResponse(
                    pipeline_id=pipeline_id,
                    overall_state=state_info["status"],
                    total_steps=state_info["total_stages"],
                    current_stage=state_info.get("current_stage", 0),
                    start_time=state_info.get("start_time"),
                    tasks=tasks
                )
            
            else:
                # Redis에 정보가 없는 경우 Celery AsyncResult로 fallback
                result = celery_app.AsyncResult(pipeline_id)
                return PipelineStatusResponse(
                    pipeline_id=pipeline_id,
                    overall_state=result.state,
                    total_steps=1,
                    current_stage=1 if result.ready() else 0,
                    tasks=[TaskStatusResponse(
                        task_id=pipeline_id,
                        status=result.state,
                        task_name='Unknown Task',
                        stages=str(result.result) if result.ready() and result.result else '',
                        step=1,
                        ready=result.ready()
                    )]
                )
                
        except Exception as e:
            logging.error(f"Redis-based pipeline status lookup failed: {e}")
            # 에러 발생 시 Celery AsyncResult로 fallback
            result = celery_app.AsyncResult(pipeline_id)
            return PipelineStatusResponse(
                pipeline_id=pipeline_id,
                overall_state=result.state,
                total_steps=1,
                current_stage=1 if result.ready() else 0,
                tasks=[TaskStatusResponse(
                    task_id=pipeline_id,
                    status=result.state,
                    task_name='Unknown Task',
                    stages=str(result.result) if result.ready() and result.result else '',
                    step=1,
                    ready=result.ready()
                )]
            )

# 전역 서비스 인스턴스
task_service = TaskService()


# 의존성 주입 함수
def get_task_service() -> TaskService:
    return task_service

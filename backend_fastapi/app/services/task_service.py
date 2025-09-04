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
from ..models.task_info import TaskInfo
from ..schemas.tasks import (
    AIPipelineRequest, AIPipelineResponse, PipelineStatusResponse, TaskStatusResponse, TaskInfoResponse
)
from ..core.database import get_db


class TaskService:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=0,
            decode_responses=True
        )

        # 동기식 DB 연결 (task_name 조회용)
        try:
            from sqlalchemy import create_engine
            from sqlalchemy.orm import sessionmaker
            sync_db_url = settings.DATABASE_URL.replace("+asyncpg", "")
            self.sync_engine = create_engine(sync_db_url)
            self.SyncSessionLocal = sessionmaker(bind=self.sync_engine)
        except Exception as e:
            logging.warning(f"Failed to initialize sync DB connection: {e}")
            self.sync_engine = None
            self.SyncSessionLocal = None

    def get_tasks_history(
            self,
            hours: int = 1,
            status: Optional[str] = None,
            task_name: Optional[str] = None,
            limit: int = 100,
    ) -> list[TaskInfoResponse]:
        """Redis 기반 태스크 히스토리 조회"""
        try:
            # 시간 범위 계산
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            tasks_history = []
            
            # 1. Celery task result keys 조회
            task_keys = self.redis_client.keys("celery-task-meta-*")
            
            # 2. 각 태스크 정보 조회
            for task_key in task_keys[:limit]:  # 제한 적용
                try:
                    task_data_str = self.redis_client.get(task_key)
                    if not task_data_str:
                        continue

                    task_data = json.loads(task_data_str)
                    task_id = task_key.replace("celery-task-meta-", "")

                    # 시간 필터링 (date_done이 있는 경우만)
                    if task_data.get("date_done"):
                        try:
                            task_done_time = datetime.fromisoformat(task_data["date_done"].replace("Z", "+00:00"))
                            # timezone aware한 현재 시간과 비교
                            if task_done_time.replace(tzinfo=None) < cutoff_time:
                                continue
                        except:
                            pass  # 시간 파싱 실패 시 포함

                    # 상태 필터링
                    if status and task_data.get("status") != status:
                        continue

                    # 태스크명 추출 (parent_id나 결과에서)
                    extracted_task_name = "unknown"
                    if isinstance(task_data.get("result"), dict):
                        extracted_task_name = task_data["result"].get("stage_name", "unknown")

                    # 태스크명 필터링
                    if task_name and task_name.lower() not in extracted_task_name.lower():
                        continue

                    # TaskInfoResponse 형식으로 변환
                    task_info = TaskInfoResponse(
                        task_id=task_id,
                        status=task_data.get("status", "UNKNOWN"),
                        task_name=extracted_task_name,
                        args="",  # Redis에서는 args 정보가 제한적
                        kwargs="",
                        result=json.dumps(task_data.get("result", ""), ensure_ascii=False) if task_data.get("result") else "",
                        error_message="",
                        traceback=task_data.get("traceback", "") or "",
                        retry_count=0,
                        task_time=task_data.get("date_done", ""),
                        completed_time=task_data.get("date_done", "") if task_data.get("status") == "SUCCESS" else "",
                        root_task_id=task_data.get("parent_id", ""),
                        parent_task_id=task_data.get("parent_id", ""),
                        chain_total=0
                    )

                    tasks_history.append(task_info)

                except Exception as e:
                    logging.warning(f"Failed to process task {task_key}: {e}")
                    continue

            # 3. 시간 순으로 정렬 (최신순)
            tasks_history.sort(key=lambda x: x.task_time or "", reverse=True)
            
            logging.info(f"Retrieved {len(tasks_history)} tasks from Redis")
            return tasks_history
            
        except Exception as e:
            logging.error(f"Redis-based task history lookup failed: {e}")
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
                        result="",
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
                        result=str(result.result) if result.ready() and result.result else '',
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
                    result=str(result.result) if result.ready() and result.result else '',
                    step=1,
                    ready=result.ready()
                )]
            )
        # if not self.SyncSessionLocal:
        #     raise Exception("Database connection not available")
        #
        # try:
        #     with self.SyncSessionLocal() as db:
        #         # 1. 루트 태스크(파이프라인 시작점) 찾기
        #         root_task = db.query(TaskInfo).filter(TaskInfo.task_id == pipeline_id).first()
        #
        #         if not root_task:
        #             # AsyncResult로 fallback (태스크가 DB에 아직 저장되지 않은 경우)
        #             result = celery_app.AsyncResult(pipeline_id)
        #             return PipelineStatusResponse(
        #                 pipeline_id=pipeline_id,
        #                 overall_state=result.state,
        #                 total_steps=1,
        #                 tasks=[TaskStatusResponse(
        #                     task_id=pipeline_id,
        #                     status=result.state,
        #                     task_name='unknown',
        #                     result=str(result.result) if result.ready() and result.result else '',
        #                     step=1,
        #                     ready=result.ready()
        #                 )]
        #             )
        #
        #         # 2. 체인의 모든 관련 태스크 조회
        #         # root_task_id가 같거나, task_id가 pipeline_id인 모든 태스크
        #         chain_tasks = db.query(TaskInfo).filter(
        #             (TaskInfo.root_task_id == pipeline_id) |
        #             (TaskInfo.task_id == pipeline_id)
        #         ).order_by(TaskInfo.task_time).all()
        #
        #         # 3. TaskStatusResponse 객체로 변환
        #         tasks = []
        #         for step, db_task in enumerate(chain_tasks, 1):
        #             # AsyncResult에서 추가 정보 가져오기 (상태, ready 여부)
        #             try:
        #                 async_result = celery_app.AsyncResult(db_task.task_id)
        #                 current_state = async_result.state
        #                 is_ready = async_result.ready()
        #                 result_data = str(async_result.result) if is_ready and async_result.result else (
        #                             db_task.result or '')
        #             except Exception:
        #                 # AsyncResult 조회 실패 시 DB 데이터 사용
        #                 current_state = db_task.status
        #                 is_ready = db_task.status in ['SUCCESS', 'FAILURE', 'REVOKED']
        #                 result_data = db_task.result or ''
        #
        #             task_info = TaskStatusResponse(
        #                 task_id=db_task.task_id,
        #                 status=current_state,
        #                 task_name=db_task.task_name,
        #                 result=result_data,
        #                 traceback=db_task.traceback,
        #                 step=step,
        #                 ready=is_ready
        #             )
        #             tasks.append(task_info)
        #
        #         # 4. 전체 파이프라인 상태 결정
        #         if not tasks:
        #             overall_state = 'PENDING'
        #         elif all(task.status == 'SUCCESS' for task in tasks):
        #             overall_state = 'SUCCESS'
        #         elif any(task.status == 'FAILURE' for task in tasks):
        #             overall_state = 'FAILURE'
        #         elif any(task.status in ['PROGRESS', 'STARTED'] for task in tasks):
        #             overall_state = 'PROGRESS'
        #         else:
        #             overall_state = tasks[0].status if tasks else 'PENDING'
        #
        #         return PipelineStatusResponse(
        #             pipeline_id=pipeline_id,
        #             overall_state=overall_state,
        #             total_steps=len(tasks),
        #             tasks=tasks
        #         )

        # except Exception as e:
        #     logging.error(f"Database-based pipeline status lookup failed: {e}")
        #     # AsyncResult fallback
        #     result = celery_app.AsyncResult(pipeline_id)
        #     return PipelineStatusResponse(
        #         pipeline_id=pipeline_id,
        #         overall_state=result.state,
        #         total_steps=1,
        #         tasks=[TaskStatusResponse(
        #             task_id=pipeline_id,
        #             status=result.state,
        #             task_name='unknown',
        #             result=str(result.result) if result.ready() and result.result else '',
        #             step=1,
        #             ready=result.ready()
        #         )]
        #     )


# 전역 서비스 인스턴스
task_service = TaskService()


# 의존성 주입 함수
def get_task_service() -> TaskService:
    return task_service

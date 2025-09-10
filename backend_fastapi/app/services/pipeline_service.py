# services/pipeline_service.py

import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional

import redis
from celery import chain
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.celery_app import celery_app
from ..core.config import settings
from ..schemas import (
    AIPipelineRequest, AIPipelineResponse, PipelineStatusResponse, TaskStatusResponse,
    StageInfo, StageStatus
)
from ..models.pipeline_execution import PipelineExecution
from ..models.pipeline_stage import PipelineStage
# 파이프라인 단계별 태스크 임포트
from ..tasks import (
    stage1_preprocessing,
    stage2_feature_extraction,
    stage3_model_inference,
    stage4_post_processing
)


class PipelineService:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=0,
            decode_responses=True
        )

    async def get_pipelines_from_db(
        self,
        db: AsyncSession,
        hours: int,
        status: Optional[str] = None,
        task_name: Optional[str] = None,
        limit: int = 100,
    ) -> list[PipelineStatusResponse]:
        """DB에서 PipelineExecution 조회하여 PipelineStatusResponse 형태로 반환"""
        try:
            from datetime import datetime, timedelta
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            # PipelineExecution 조회 쿼리 구성
            query = select(PipelineExecution)
            
            # 필터링 조건 추가
            if status:
                query = query.where(PipelineExecution.status == status)
            
            # 최신순으로 정렬하고 제한
            query = query.order_by(PipelineExecution.id.desc()).limit(limit)
            result = await db.execute(query)
            pipeline_executions = result.scalars().all()
            
            # PipelineExecution을 PipelineStatusResponse로 변환
            pipeline_groups = []
            
            for pipeline_execution in pipeline_executions:
                pipeline_id = pipeline_execution.pipeline_id or pipeline_execution.execution_id or "unknown"

                # 각 파이프라인마다 새로운 tasks_history 생성 (정규화된 PipelineStage 테이블 사용)
                tasks_history = []
                try:
                    # 정규화된 pipeline_stages 테이블에서 로드
                    stages_query = select(PipelineStage).where(
                        PipelineStage.pipeline_execution_id == pipeline_execution.id
                    ).order_by(PipelineStage.stage_number)
                    stages_result = await db.execute(stages_query)
                    db_stages = stages_result.scalars().all()
                    
                    # DB stages가 없으면 JSON fallback
                    if not db_stages and pipeline_execution.stages_json:
                        stages_data = json.loads(pipeline_execution.stages_json)
                        db_stages = [StageInfo.from_dict(stage_data) for stage_data in stages_data]
                    
                    for stage in db_stages:
                        # PipelineStage 모델인지 StageInfo인지 확인
                        if hasattr(stage, 'stage_number'):  # DB PipelineStage 모델
                            stage_status = stage.status
                            stage_name = stage.stage_name
                            stage_number = stage.stage_number
                            stage_progress = stage.progress
                        else:  # StageInfo 스키마
                            stage_status = stage.status.value if isinstance(stage.status, StageStatus) else stage.status
                            stage_name = stage.stage_name
                            stage_number = stage.stage
                            stage_progress = stage.progress
                        
                        # 상태 및 태스크 이름 필터링
                        if status and stage_status != status:
                            continue
                        if task_name and task_name.lower() not in stage_name.lower():
                            continue

                        tasks_history.append(TaskStatusResponse(
                            task_id=f"{pipeline_id}_{stage_number}",
                            status=stage_status,
                            task_name=stage_name,
                            progress=stage_progress
                        ))
                except Exception as e:
                    logging.warning(f"Failed to load stages for pipeline {pipeline_execution.execution_id}: {e}")
                    continue

                pipeline_groups.append(PipelineStatusResponse(
                    pipeline_id=pipeline_execution.pipeline_id,
                    overall_state=pipeline_execution.status or "",
                    total_steps=len(db_stages) if db_stages else 0,
                    current_stage=pipeline_execution.current_step or 0,
                    start_time=pipeline_execution.created_at.isoformat() if pipeline_execution.created_at else None,
                    tasks=tasks_history
                ))

            return pipeline_groups
                
        except Exception as e:
            logging.error(f"DB-based pipeline history lookup failed: {e}")
            return []

    def get_pipelines_from_redis(
        self,
        hours: int,
        status: Optional[str] = None,
        task_name: Optional[str] = None,
        limit: int = 100,
    ) -> list[PipelineStatusResponse]:
        """Redis에서 파이프라인 상태 조회"""
        try:
            # 1. Celery task result keys 조회
            pipeline_keys = self.redis_client.keys("pipeline*")
            pipelines = []

            # 2. 각 파이프라인 정보 조회
            for pipeline_key in pipeline_keys[:limit]:  # 제한 적용
                try:
                    pipeline_data = self.redis_client.get(pipeline_key)
                    if not pipeline_data:
                        continue

                    pipeline_id = pipeline_key.replace("pipeline:", "")
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

                    # 각 파이프라인마다 새로운 tasks_history 생성 (StageInfo 모델 사용)
                    tasks_history = []
                    stages_data = state_info.get("stages", [])
                    
                    # StageInfo 객체로 변환
                    try:
                        stages = [StageInfo.from_dict(stage_data) for stage_data in stages_data]
                        
                        for stage in stages:
                            # 상태 및 태스크 이름 필터링
                            stage_status = stage.status.value if isinstance(stage.status, StageStatus) else stage.status
                            if status and stage_status != status:
                                continue
                            if task_name and task_name.lower() not in stage.stage_name.lower():
                                continue

                            tasks_history.append(TaskStatusResponse(
                                task_id=f"{pipeline_id}_{stage.stage}",
                                status=stage_status,
                                task_name=stage.stage_name,
                                stages="",
                                step=stage.stage,
                                ready=stage_status in ["SUCCESS", "FAILURE", "completed"],
                                progress=stage.progress
                            ))
                    except (TypeError, ValueError) as e:
                        logging.warning(f"Failed to parse stages from Redis for pipeline {pipeline_id}: {e}")
                        # Fallback to original format
                        for stage_data in stages_data:
                            if isinstance(stage_data, dict):
                                stage_status = stage_data.get("status", "UNKNOWN")
                                if status and stage_status != status:
                                    continue
                                if task_name and task_name.lower() not in stage_data.get("stage_name", "").lower():
                                    continue

                                tasks_history.append(TaskStatusResponse(
                                    task_id=f"{pipeline_id}_{stage_data.get('stage', 0)}",
                                    status=stage_status,
                                    task_name=stage_data.get("stage_name", ""),
                                    stages="",
                                    step=stage_data.get("stage", 0),
                                    ready=stage_status in ["SUCCESS", "FAILURE", "completed"],
                                    progress=stage_data.get("progress", 0)
                                ))

                    if tasks_history:  # 필터링 후 남은 태스크가 있는 경우만 추가
                        pipelines.append(PipelineStatusResponse(
                            pipeline_id=pipeline_id,
                            overall_state=state_info["status"],
                            total_steps=state_info["total_stages"],
                            current_stage=state_info.get("current_stage", 0),
                            start_time=state_info.get("start_time"),
                            tasks=tasks_history
                        ))

                except Exception as e:
                    logging.warning(f"Failed to process pipeline {pipeline_key}: {e}")
                    continue

            # 3. 시간 순으로 정렬 (최신순)
            pipelines.sort(key=lambda x: x.start_time or "", reverse=True)
            
            logging.info(f"Retrieved {len(pipelines)} pipelines from Redis")
            return pipelines
            
        except Exception as e:
            logging.error(f"Redis-based pipeline history lookup failed: {e}")
            return []

    async def get_pipeline_history(
        self,
        db: AsyncSession,
        hours: int = 1,
        status: Optional[str] = None,
        task_name: Optional[str] = None,
        limit: int = 100,
    ) -> list[PipelineStatusResponse]:
        """
        파이프라인 히스토리 조회
        - 1시간 이내: Redis에서 조회 (실시간 데이터)
        - 1시간 초과: DB에서 조회 (영구 저장 데이터)
        """
        try:
            if hours <= 1:
                # 1시간 이내: Redis에서 조회
                redis_results = self.get_pipelines_from_redis(hours, status, task_name, limit)
                return redis_results
                
            else:
                # 1시간 초과: DB에서 조회
                return await self.get_pipelines_from_db(db, hours, status, task_name, limit)
                
        except Exception as e:
            logging.error(f"Pipeline history lookup failed: {e}")
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

        # --- 새로운 방식: Celery Chain을 직접 생성 ---
        # 각 단계에 대한 서명(signature)을 생성합니다.
        # .s()는 태스크를 즉시 실행하지 않고 서명 객체로 만듭니다.

        # logging.info(input_data)

        pipeline_chain = chain(
            stage1_preprocessing.s(input_data),
            stage2_feature_extraction.s(),
            stage3_model_inference.s(),
            stage4_post_processing.s()
        )

        # 체인을 비동기적으로 실행합니다.
        task_result = pipeline_chain.apply_async()
        
        # task_result.id는 체인의 첫 번째 태스크 ID이며, 이는 전체 체인의 root_id가 됩니다.
        # 이 ID를 파이프라인의 고유 ID로 사용합니다.

        # --- 이전 방식 (주석 처리) ---
        # # 오케스트레이터 태스크 시작
        # task = celery_app.send_task(
        #     "app.tasks.ai_pipeline_orchestrator",
        #     args=[input_data]
        # )
        #
        # # Redis에 파이프라인 상태 초기화 (StageInfo 모델 사용)
        # # 이제 이 로직은 celery_signals의 task_prerun_handler가 DB에 기록하는 방식으로 대체됩니다.
        # pipeline_key = f"pipeline:{task.id}"
        #
        # # StageInfo 객체들로 초기 stages 생성
        # initial_stages = [
        #     StageInfo.create_pending_stage(1, "데이터 전처리"),
        #     StageInfo.create_pending_stage(2, "특성 추출"),
        #     StageInfo.create_pending_stage(3, "모델 추론"),
        #     StageInfo.create_pending_stage(4, "후처리")
        # ]
        #
        # initial_state = {
        #     "pipeline_id": task.id,
        #     "status": "STARTED",
        #     "current_stage": 0,
        #     "total_stages": 4,
        #     "start_time": datetime.now().isoformat(),
        #     "stages": [stage.to_dict() for stage in initial_stages]
        # }
        #
        # self.redis_client.setex(
        #     pipeline_key,
        #     3600,  # 1시간 TTL
        #     json.dumps(initial_state)
        # )
        #
        # return AIPipelineResponse(
        #     pipeline_id=task.id,
        #     status="STARTED",
        #     message="AI 처리 파이프라인이 시작되었습니다",
        #     estimated_duration=20  # 예상 20초
        # )
        # --- 이전 방식 끝 ---

        return AIPipelineResponse(
            pipeline_id=task_result.id, # 체인의 root_id를 반환
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
                
                # 단계별 태스크 정보 생성 (StageInfo 모델 사용)
                tasks = []
                stages_data = state_info.get("stages", [])
                
                try:
                    # StageInfo 객체로 변환
                    stages = [StageInfo.from_dict(stage_data) for stage_data in stages_data]
                    
                    for stage in stages:
                        stage_status = stage.status.value if isinstance(stage.status, StageStatus) else stage.status
                        tasks.append(TaskStatusResponse(
                            task_id=f"{pipeline_id}_{stage.stage}",
                            status=stage_status,
                            task_name=stage.stage_name,
                            stages="",
                            step=stage.stage,
                            ready=stage_status in ["SUCCESS", "FAILURE", "completed"],
                            progress=stage.progress
                        ))
                except (TypeError, ValueError) as e:
                    logging.warning(f"Failed to parse stages in get_pipeline_status for {pipeline_id}: {e}")
                    # Fallback to original format
                    for stage_data in stages_data:
                        if isinstance(stage_data, dict):
                            stage_status = stage_data.get("status", "UNKNOWN")
                            tasks.append(TaskStatusResponse(
                                task_id=f"{pipeline_id}_{stage_data.get('stage', 0)}",
                                status=stage_status,
                                task_name=stage_data.get("stage_name", ""),
                                stages="",
                                step=stage_data.get("stage", 0),
                                ready=stage_status in ["SUCCESS", "FAILURE", "completed"],
                                progress=stage_data.get("progress", 0)
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
pipeline_service = PipelineService()


# 의존성 주입 함수
def get_pipeline_service() -> PipelineService:
    return pipeline_service


# 하위 호환성을 위한 별칭들
TaskService = PipelineService
task_service = pipeline_service

def get_task_service() -> PipelineService:
    """하위 호환성을 위한 별칭"""
    return pipeline_service
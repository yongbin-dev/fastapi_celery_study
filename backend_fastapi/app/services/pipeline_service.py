# services/pipeline_service.py

import uuid
from typing import Optional, Dict

from app.core.logging import get_logger

logger = get_logger(__name__)
from celery import chain
from fastapi import HTTPException

from app.models.chain_execution import ChainExecution
from app.schemas import (
    AIPipelineRequest, AIPipelineResponse, PipelineStatusResponse,
    PipelineStagesResponse, StageDetailResponse, StageInfo, ProcessStatus
)
# 파이프라인 단계별 태스크 임포트
from app.tasks import (
    stage1_preprocessing,
    stage2_feature_extraction,
    stage3_model_inference,
    stage4_post_processing
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.status_manager import RedisPipelineStatusManager



class PipelineService:

    def _validate_chain_id(self , chain_id: str) -> None:
        """체인 ID 유효성 검증"""
        if not chain_id or len(chain_id) < 5:
            raise HTTPException(
                status_code=400,
                detail="유효하지 않은 체인 ID 형식입니다"
            )

    def _validate_stage(self , stage: int) -> None:
        """스테이지 번호 유효성 검증"""
        if stage < 1 or stage > 4:
            raise HTTPException(
                status_code=400,
                detail="단계는 1~4 사이의 값이어야 합니다"
            )

    async def get_pipelines_from_db(
            self,
            db: AsyncSession,
            hours: int,
            status: Optional[str] = None,
            task_name: Optional[str] = None,
            limit: int = 100,
    ) -> list[PipelineStatusResponse]:
        # TODO: DB 조회 로직 구현
        return []


    async def get_pipeline_history(
            self,
            db: AsyncSession,
            hours: int = 1,
            status: Optional[str] = None,
            task_name: Optional[str] = None,
            limit: int = 100,
    ) -> list[PipelineStatusResponse]:
        # TODO: hours > 1 이면 DB, 아니면 Redis 조회 로직 분기 구현
        return await self.get_pipelines_from_db(db=db, hours=hours, status=status, task_name=task_name, limit=limit)

    async def create_ai_pipeline(self, db : AsyncSession , status_manager : RedisPipelineStatusManager ,  request: AIPipelineRequest) -> AIPipelineResponse:
        """AI 처리 파이프라인 시작"""
        input_data = {
            "text": request.text,
            "options": request.options,
            "priority": request.priority,
            "callback_url": request.callback_url,
        }

        try:
            chain_id = str(uuid.uuid4())

            # 1. ChainExecution 테이블에 레코드 생성
            chain_execution = ChainExecution(
                chain_name="ai_processing_pipeline",
                total_tasks=4,  # 4단계 파이프라인
                initiated_by=getattr(request, 'user_id', 'system'),
                input_data=input_data,
                chain_id=chain_id
            )

            db.add(chain_execution)
            await db.commit()
            await db.refresh(chain_execution)

            logger.info(f"ChainExecution created with ID: {chain_execution.id}, chain_id: {chain_execution.chain_id}")

            # 2. 전체 스테이지 정보를 Redis에 미리 저장
            chain_id_str = str(chain_execution.chain_id)
            stages_initialized = status_manager.initialize_pipeline_stages( chain_id_str, input_data)

            if not stages_initialized:
                await db.rollback()
                logger.error(f"Pipeline {chain_id_str}: 스테이지 초기화 실패")
                raise HTTPException(status_code=500, detail="파이프라인 스테이지 초기화에 실패했습니다")

            # 3. Celery Chain 생성 및 실행
            pipeline_chain = chain(
                stage1_preprocessing.s(input_data, chain_id=chain_id_str),
                stage2_feature_extraction.s(),
                stage3_model_inference.s(),
                stage4_post_processing.s()
            )

            # 4. 체인 실행 시작
            pipeline_chain.apply_async()

            # 5. ChainExecution 상태 업데이트
            chain_execution.start_execution()
            await db.commit()

            logger.info(f"Pipeline started successfully. Chain ID: {chain_execution.chain_id}")

            return AIPipelineResponse(
                pipeline_id=str(chain_execution.chain_id),  # Celery task ID
                status="STARTED",
                message="AI 처리 파이프라인이 시작되었습니다",
                estimated_duration=20  # 예상 20초
            )

        except Exception as e:
            # 데이터베이스 에러, Redis 연결 에러 등 예상치 못한 에러
            await db.rollback()
            logger.error(f"파이프라인 생성 중 예상치 못한 에러 발생: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail="AI 파이프라인 시작 중 내부 서버 오류가 발생했습니다"
            )

    def get_pipeline_tasks(self, status_manager: RedisPipelineStatusManager, chain_id: str) -> PipelineStagesResponse:
        """파이프라인 전체 태스크 목록 조회 (구조화된 응답)"""
        # 체인 ID 검증
        self._validate_chain_id(chain_id)

        # Redis에서 파이프라인 태스크 목록 조회
        pipeline_tasks_data = status_manager.get_pipeline_status(chain_id)

        if not pipeline_tasks_data:
            raise HTTPException(
                status_code=404,
                detail=f"체인 ID '{chain_id}'에 해당하는 파이프라인을 찾을 수 없습니다"
            )

        # 딕셔너리 데이터를 StageInfo 스키마로 변환
        stages = [StageInfo.from_dict(task_data) for task_data in pipeline_tasks_data]

        # 현재 진행 중인 스테이지 및 전체 진행률 계산
        current_stage = None
        overall_progress = 0
        last_completed_stage = 0

        for stage in stages:
            # status가 Enum이면 .value 접근, 아니면 직접 사용
            status_value = stage.status.value if hasattr(stage.status, 'value') else stage.status

            if status_value == ProcessStatus.SUCCESS.value:
                # 완료된 스테이지
                overall_progress += 25  # 각 스테이지당 25%
                last_completed_stage = stage.stage
            elif status_value == ProcessStatus.PENDING.value and stage.progress > 0:
                # 현재 진행 중인 스테이지
                current_stage = stage.stage
                # 현재 스테이지의 부분 진행률 추가
                overall_progress += int(stage.progress * 0.25)
            elif status_value == ProcessStatus.FAILURE.value:
                # 실패한 스테이지는 현재 스테이지로 설정 (재시도 가능)
                current_stage = stage.stage

        # 현재 진행 중인 스테이지가 없고 파이프라인이 완전히 끝난 경우
        if current_stage is None and last_completed_stage == 4:
            current_stage = 4  # 마지막 스테이지를 현재로 표시
            overall_progress = 100

        return PipelineStagesResponse(
            chain_id=chain_id,
            total_stages=len(stages),
            current_stage=current_stage,
            overall_progress=overall_progress,
            stages=stages
        )

    def get_stage_task(self, status_manager: RedisPipelineStatusManager, chain_id: str, stage: int) -> StageDetailResponse:
        """특정 단계의 태스크 상태 조회 (구조화된 응답)"""
        # 체인 ID 및 단계 검증
        self._validate_chain_id(chain_id)
        self._validate_stage(stage)

        # Redis에서 단계 상태 조회
        stage_task_data = status_manager.get_stage_status(chain_id, stage)

        if not stage_task_data:
            raise HTTPException(
                status_code=404,
                detail=f"체인 ID '{chain_id}'의 단계 {stage}에 해당하는 태스크를 찾을 수 없습니다"
            )

        # 딕셔너리를 StageInfo 스키마로 변환
        stage_info = StageInfo.from_dict(stage_task_data)

        # 현재 상태 분석
        status_value = stage_info.status.value if hasattr(stage_info.status, 'value') else stage_info.status
        is_current = status_value == ProcessStatus.PENDING.value and stage_info.progress > 0
        is_completed = status_value == ProcessStatus.SUCCESS.value
        is_failed = status_value == ProcessStatus.FAILURE.value

        return StageDetailResponse(
            stage_info=stage_info,
            is_current=is_current,
            is_completed=is_completed,
            is_failed=is_failed
        )

    def cancel_pipeline(self, status_manager: RedisPipelineStatusManager, chain_id: str) -> Dict[str, str]:
        """파이프라인 취소 및 데이터 삭제"""
        # Celery 태스크 취소
        # TODO: chain_id를 기반으로 task_id를 조회하여 취소해야 함
        # celery_app.control.revoke(task_id, terminate=True)

        # Redis에서 파이프라인 데이터 삭제
        deleted = status_manager.delete_pipeline(chain_id)

        if deleted:
            return {
                "chain_id": chain_id,
                "status": "DELETED",
                "message": "AI 파이프라인 취소 및 데이터 삭제가 완료되었습니다"
            }
        else:
            return {
                "chain_id": chain_id,
                "status": "NOT_FOUND",
                "message": "파이프라인 데이터를 찾을 수 없어 취소만 수행되었습니다"
            }


pipeline_service_instance = PipelineService()

def get_pipeline_service() -> PipelineService:
    return pipeline_service_instance

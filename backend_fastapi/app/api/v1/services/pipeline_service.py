# services/pipeline_service.py

import uuid
from typing import Optional, Dict, List

from app.core.logging import get_logger

logger = get_logger(__name__)
from celery import chain
from fastapi import HTTPException, Depends

from app.models.chain_execution import ChainExecution
from app.schemas import (
    AIPipelineRequest,
    AIPipelineResponse,
    PipelineStagesResponse,
    StageDetailResponse,
    StageInfo,
    ProcessStatus,
)
from app.api.v1.crud import (
    async_chain_execution as chain_execution_crud,
)
from app.pipeline_config import STAGES

from sqlalchemy.ext.asyncio import AsyncSession


class PipelineService:
    def _validate_chain_id(self, chain_id: str) -> None:
        """체인 ID 유효성 검증"""
        if not chain_id or len(chain_id) < 5:
            raise HTTPException(status_code=400, detail="유효하지 않은 체인 ID 형식입니다")

    def _validate_stage(self, stage: int) -> None:
        """스테이지 번호 유효성 검증"""
        if stage < 1 or stage > 4:
            raise HTTPException(status_code=400, detail="단계는 1~4 사이의 값이어야 합니다")

    async def get_pipelines_from_db(
        self,
        db: AsyncSession,
        hours: int,
        status: Optional[str] = None,
        task_name: Optional[str] = None,
        limit: int = 100,
    ) -> List[PipelineStagesResponse]:
        # ChainExecution 조회 (최근 생성된 순으로)
        chain_executions = await chain_execution_crud.get_recent_chains(
            db, days=hours // 24 + 1, limit=limit
        )

        # 필터링
        if status:
            chain_executions = [
                chain_exec
                for chain_exec in chain_executions
                if chain_exec.status == status
            ]

        pipeline_responses = []

        for chain_exec in chain_executions:
            # 해당 체인의 TaskLog들 조회 (pipeline stage만) - AsyncSession 사용
            task_logs = await self._get_pipeline_tasks_by_chain_async(
                db, chain_id=chain_exec.chain_id
            )

            # StageInfo 리스트 생성
            stages = []
            for i, stage_config in enumerate(STAGES, 1):
                # 해당 stage의 TaskLog 찾기
                stage_task = next(
                    (task for task in task_logs if f"stage{i}" in task.task_name), None
                )

                if stage_task:
                    # TaskLog에서 StageInfo 생성
                    stage_info = StageInfo(
                        chain_id=chain_exec.chain_id,
                        stage=i,
                        stage_name=stage_config["name"],
                        task_id=stage_task.task_id,
                        status=ProcessStatus(stage_task.status),
                        progress=self._calculate_stage_progress(stage_task.status),
                        created_at=stage_task.created_at.timestamp()
                        if stage_task.created_at
                        else 0,
                        started_at=stage_task.started_at.timestamp()
                        if stage_task.started_at
                        else None,
                        updated_at=stage_task.updated_at.timestamp()
                        if stage_task.updated_at
                        else 0,
                        error_message=stage_task.error,
                        description=stage_config.get("description"),
                        expected_duration=stage_config.get("expected_duration"),
                    )
                else:
                    stage_info = StageInfo.create_pending_stage(
                        chain_id=chain_exec.chain_id,
                        stage=i,
                        stage_name=stage_config["name"],
                        description=stage_config.get("description", ""),
                        expected_duration=stage_config.get("expected_duration", ""),
                    )

                stages.append(stage_info)

            # PipelineStagesResponse 생성
            pipeline_response = self._create_pipeline_stages_response(
                chain_exec.chain_id, stages
            )
            pipeline_responses.append(pipeline_response)

        return pipeline_responses

    async def _get_pipeline_tasks_by_chain_async(
        self, db: AsyncSession, *, chain_id: str
    ) -> List:
        """파이프라인 작업들을 단계순으로 조회 (AsyncSession용)"""
        from sqlalchemy import select, desc, and_
        from app.models.task_log import TaskLog

        stage_tasks = []
        for stage_num in range(1, 5):  # stage1~4
            # 각 stage별 TaskLog 조회 - chain_id로 필터링
            stmt = (
                select(TaskLog)
                .where(
                    and_(
                        TaskLog.task_name.like(f"app.tasks.stage{stage_num}_%"),
                        TaskLog.kwargs.like(f'%"{chain_id}"%'),
                    )
                )
                .order_by(desc(TaskLog.created_at))
                .limit(1)
            )

            result = await db.execute(stmt)
            task = result.scalar_one_or_none()

            if task:
                stage_tasks.append(task)
            else:
                # 더 넓은 검색 - args에서도 찾아보기
                stmt_alt = (
                    select(TaskLog)
                    .where(
                        and_(
                            TaskLog.task_name.like(f"app.tasks.stage{stage_num}_%"),
                            TaskLog.args.like(f"%{chain_id}%"),
                        )
                    )
                    .order_by(desc(TaskLog.created_at))
                    .limit(1)
                )

                result_alt = await db.execute(stmt_alt)
                task_alt = result_alt.scalar_one_or_none()
                if task_alt:
                    stage_tasks.append(task_alt)

        return stage_tasks

    def _calculate_stage_progress(self, status: str) -> int:
        """작업 상태에 따른 진행률 계산"""
        if status == ProcessStatus.SUCCESS.value:
            return 100
        elif status == ProcessStatus.STARTED.value:
            return 50
        elif status in [ProcessStatus.FAILURE.value, ProcessStatus.REVOKED.value]:
            return 0
        else:  # PENDING, RETRY
            return 0

    def _create_pipeline_stages_response(
        self, chain_id: str, stages: List[StageInfo]
    ) -> PipelineStagesResponse:
        """StageInfo 리스트로부터 PipelineStagesResponse 생성"""
        # 현재 진행 중인 스테이지 및 전체 진행률 계산
        current_stage = None
        overall_progress = 0
        last_completed_stage = 0

        for stage in stages:
            # status가 Enum이면 .value 접근, 아니면 직접 사용
            status_value = (
                stage.status.value if hasattr(stage.status, "value") else stage.status
            )

            if status_value == ProcessStatus.SUCCESS.value:
                # 완료된 스테이지
                overall_progress += 25  # 각 스테이지당 25%
                last_completed_stage = stage.stage
            elif status_value == ProcessStatus.STARTED.value:
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
            stages=stages,
        )

    async def get_pipeline_history(
        self,
        db: AsyncSession,
        hours: int = 1,
        status: Optional[str] = None,
        task_name: Optional[str] = None,
        limit: int = 100,
    ) -> List[PipelineStagesResponse]:
        """파이프라인 히스토리 조회 - DB 기반"""
        return await self.get_pipelines_from_db(
            db=db, hours=hours, status=status, task_name=task_name, limit=limit
        )

    async def create_ai_pipeline(
        self, db: AsyncSession, redis_service, request: AIPipelineRequest
    ) -> AIPipelineResponse:
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
                initiated_by=getattr(request, "user_id", "system"),
                input_data=input_data,
                chain_id=chain_id,
            )

            db.add(chain_execution)
            await db.commit()
            await db.refresh(chain_execution)

            logger.info(
                f"ChainExecution created with ID: {chain_execution.id}, chain_id: {chain_execution.chain_id}"
            )

            # 2. 전체 스테이지 정보를 Redis에 미리 저장
            chain_id_str = str(chain_execution.chain_id)
            stages_initialized = redis_service.initialize_pipeline_stages(
                chain_id_str, input_data
            )

            if not stages_initialized:
                await db.rollback()
                logger.error(f"Pipeline {chain_id_str}: 스테이지 초기화 실패")
                raise HTTPException(status_code=500, detail="파이프라인 스테이지 초기화에 실패했습니다")

            # 3. Celery Chain 생성 및 실행 (동적 임포트 사용)
            from app.core.celery.celery_tasks import (
                stage1_preprocessing,
                stage2_feature_extraction,
                stage3_model_inference,
                stage4_post_processing,
            )

            pipeline_chain = chain(
                stage1_preprocessing.s(input_data, chain_id=chain_id_str),
                stage2_feature_extraction.s(),
                stage3_model_inference.s(),
                stage4_post_processing.s(),
            )

            # 4. 체인 실행 시작
            pipeline_chain.apply_async()

            # 5. ChainExecution 상태 업데이트
            chain_execution.start_execution()
            await db.commit()

            logger.info(
                f"Pipeline started successfully. Chain ID: {chain_execution.chain_id}"
            )

            return AIPipelineResponse(
                pipeline_id=str(chain_execution.chain_id),  # Celery task ID
                status="STARTED",
                message="AI 처리 파이프라인이 시작되었습니다",
                estimated_duration=20,  # 예상 20초
            )

        except Exception as e:
            # 데이터베이스 에러, Redis 연결 에러 등 예상치 못한 에러
            await db.rollback()
            logger.error(f"파이프라인 생성 중 예상치 못한 에러 발생: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500, detail="AI 파이프라인 시작 중 내부 서버 오류가 발생했습니다"
            )

    def get_pipeline_tasks(
        self, redis_service, chain_id: str
    ) -> PipelineStagesResponse:
        """파이프라인 전체 태스크 목록 조회 (구조화된 응답)"""
        # 체인 ID 검증
        self._validate_chain_id(chain_id)

        # Redis에서 파이프라인 태스크 목록 조회
        pipeline_tasks_data = redis_service.get_pipeline_status(chain_id)

        if not pipeline_tasks_data:
            raise HTTPException(
                status_code=404, detail=f"체인 ID '{chain_id}'에 해당하는 파이프라인을 찾을 수 없습니다"
            )

        # 딕셔너리 데이터를 StageInfo 스키마로 변환
        stages = [StageInfo.from_dict(task_data) for task_data in pipeline_tasks_data]

        # 현재 진행 중인 스테이지 및 전체 진행률 계산
        current_stage = None
        overall_progress = 0
        last_completed_stage = 0

        for stage in stages:
            # status가 Enum이면 .value 접근, 아니면 직접 사용
            status_value = (
                stage.status.value if hasattr(stage.status, "value") else stage.status
            )

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
            stages=stages,
        )

    def get_stage_task(
        self, redis_service, chain_id: str, stage: int
    ) -> StageDetailResponse:
        """특정 단계의 태스크 상태 조회 (구조화된 응답)"""
        # 체인 ID 및 단계 검증
        self._validate_chain_id(chain_id)
        self._validate_stage(stage)

        # Redis에서 단계 상태 조회
        stage_task_data = redis_service.get_stage_status(chain_id, stage)

        if not stage_task_data:
            raise HTTPException(
                status_code=404,
                detail=f"체인 ID '{chain_id}'의 단계 {stage}에 해당하는 태스크를 찾을 수 없습니다",
            )

        # 딕셔너리를 StageInfo 스키마로 변환
        stage_info = StageInfo.from_dict(stage_task_data)

        # 현재 상태 분석
        status_value = (
            stage_info.status.value
            if hasattr(stage_info.status, "value")
            else stage_info.status
        )
        is_current = (
            status_value == ProcessStatus.PENDING.value and stage_info.progress > 0
        )
        is_completed = status_value == ProcessStatus.SUCCESS.value
        is_failed = status_value == ProcessStatus.FAILURE.value

        return StageDetailResponse(
            stage_info=stage_info,
            is_current=is_current,
            is_completed=is_completed,
            is_failed=is_failed,
        )

    def cancel_pipeline(self, redis_service, chain_id: str) -> Dict[str, str]:
        """파이프라인 취소 및 데이터 삭제"""
        # Celery 태스크 취소
        # TODO: chain_id를 기반으로 task_id를 조회하여 취소해야 함
        # celery_app.control.revoke(task_id, terminate=True)

        # Redis에서 파이프라인 데이터 삭제
        deleted = redis_service.delete_pipeline(chain_id)

        if deleted:
            return {
                "chain_id": chain_id,
                "status": "DELETED",
                "message": "AI 파이프라인 취소 및 데이터 삭제가 완료되었습니다",
            }
        else:
            return {
                "chain_id": chain_id,
                "status": "NOT_FOUND",
                "message": "파이프라인 데이터를 찾을 수 없어 취소만 수행되었습니다",
            }


pipeline_service_instance = PipelineService()


def get_pipeline_service() -> PipelineService:
    return pipeline_service_instance

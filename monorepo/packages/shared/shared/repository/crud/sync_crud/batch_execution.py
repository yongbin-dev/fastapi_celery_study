# crud/batch_execution.py

from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from shared.models.batch_execution import BatchExecution
from shared.schemas.batch_execution import (
    BatchExecutionCreate,
    BatchExecutionResponse,
    BatchExecutionUpdate,
)
from shared.schemas.enums import ProcessStatus

from .base import CRUDBase


class CRUDBatchExecution(
    CRUDBase[BatchExecution, BatchExecutionCreate, BatchExecutionUpdate]
):
    """BatchExecution 모델용 CRUD 클래스"""

    def get_by_batch_id(
        self, session: Session, *, batch_id: str
    ) -> Optional[BatchExecution]:
        """batch_id로 배치 실행 조회"""
        return (
            session.query(BatchExecution)
            .filter(BatchExecution.batch_id == batch_id)
            .first()
        )

    def get_dto_by_batch_id(
        self, session: Session, *, batch_id: str
    ) -> Optional[BatchExecutionResponse]:
        """batch_id로 배치 실행 조회 (DTO 반환)"""
        batch_execution = (
            session.query(BatchExecution)
            .filter(BatchExecution.batch_id == batch_id)
            .first()
        )

        if not batch_execution:
            return None

        # progress_percentage 계산
        response = BatchExecutionResponse.model_validate(batch_execution)
        response.progress_percentage = batch_execution.get_progress_percentage()
        return response

    def create_batch_execution(
        self,
        db: Session,
        *,
        batch_id: str,
        batch_name: str,
        total_images: int,
        chunk_size: int = 10,
        initiated_by: Optional[str] = None,
        input_data: Optional[dict] = None,
        options: Optional[dict] = None,
    ) -> BatchExecution:
        """새 배치 실행 생성"""
        # 총 청크 수 계산
        total_chunks = (total_images + chunk_size - 1) // chunk_size

        batch_exec = BatchExecution(
            batch_id=batch_id,
            batch_name=batch_name,
            total_images=total_images,
            total_chunks=total_chunks,
            chunk_size=chunk_size,
            status=ProcessStatus.PENDING.value,
            initiated_by=initiated_by,
            input_data=input_data,
            options=options,
        )
        db.add(batch_exec)
        db.commit()
        db.refresh(batch_exec)
        return batch_exec

    def increment_completed_images(
        self, db: Session, *, batch_execution: BatchExecution, count: int = 1
    ) -> BatchExecution:
        """완료된 이미지 수 증가"""
        batch_execution.increment_completed_images(count)
        db.add(batch_execution)
        db.commit()
        db.refresh(batch_execution)
        return batch_execution

    def increment_failed_images(
        self, db: Session, *, batch_execution: BatchExecution, count: int = 1
    ) -> BatchExecution:
        """실패한 이미지 수 증가"""
        batch_execution.increment_failed_images(count)
        db.add(batch_execution)
        db.commit()
        db.refresh(batch_execution)
        return batch_execution

    def increment_completed_chunks(
        self, db: Session, *, batch_execution: BatchExecution
    ) -> BatchExecution:
        """완료된 청크 수 증가"""
        batch_execution.increment_completed_chunks()
        db.add(batch_execution)
        db.commit()
        db.refresh(batch_execution)
        return batch_execution

    def increment_failed_chunks(
        self, db: Session, *, batch_execution: BatchExecution
    ) -> BatchExecution:
        """실패한 청크 수 증가"""
        batch_execution.increment_failed_chunks()
        db.add(batch_execution)
        db.commit()
        db.refresh(batch_execution)
        return batch_execution

    def update_status(
        self, db: Session, *, batch_execution: BatchExecution, status: ProcessStatus
    ) -> BatchExecution:
        """배치 실행 상태 업데이트"""
        batch_execution.status = status
        if status == ProcessStatus.STARTED.value:
            batch_execution.started_at = datetime.now()
        elif status in [
            ProcessStatus.SUCCESS.value,
            ProcessStatus.FAILURE.value,
            ProcessStatus.REVOKED.value,
        ]:
            batch_execution.finished_at = datetime.now()

        db.add(batch_execution)
        db.commit()
        db.refresh(batch_execution)
        return batch_execution

    def get_active_batches(self, db: Session) -> List[BatchExecution]:
        """진행 중인 배치 목록 조회"""
        # from sqlalchemy import desc

        return (
            db.query(BatchExecution)
            # .filter(
            #     BatchExecution.status.in_(
            #         [ProcessStatus.PENDING.value, ProcessStatus.STARTED.value]
            #     )
            # )
            # .order_by(desc(BatchExecution.started_at))
            .all()
        )

    def get_recent_batches(
        self, db: Session, *, limit: int = 10
    ) -> List[BatchExecution]:
        """최근 배치 목록 조회"""
        from sqlalchemy import desc

        return (
            db.query(BatchExecution)
            .order_by(desc(BatchExecution.created_at))
            .limit(limit)
            .all()
        )


# 인스턴스 생성
batch_execution_crud = CRUDBatchExecution(BatchExecution)

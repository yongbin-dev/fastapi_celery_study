# crud/chain_execution.py

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from shared.models.chain_execution import ChainExecution
from shared.schemas.chain_execution import (
    ChainExecutionCreate,
    ChainExecutionResponse,
    ChainExecutionUpdate,
)
from shared.schemas.enums import ProcessStatus

from .base import CRUDBase


class CRUDChainExecution(
    CRUDBase[ChainExecution, ChainExecutionCreate, ChainExecutionUpdate]
):
    #     """ChainExecution 모델용 CRUD 클래스"""
    #
    def get_by_chain_id(
        self, session: Session, *, chain_id: str
    ) -> Optional[ChainExecution]:
        """chain_id로 체인 실행 조회"""
        return (
            session.query(ChainExecution)
            .filter(ChainExecution.chain_id == chain_id)
            .first()
        )

    def get_dto_by_chain_id(
        self, session: Session, *, chain_id: str
    ) -> Optional[ChainExecutionResponse]:
        """chain_id로 체인 실행 조회"""

        chain_execution = (
            session.query(ChainExecution)
            .filter(ChainExecution.chain_id == chain_id)
            .first()
        )

        return ChainExecutionResponse.model_validate(chain_execution)

    def create_chain_execution(
        self,
        db: Session,
        *,
        chain_id: str,
        chain_name: str,
        batch_id: Optional[str] = None,
        total_tasks: int = 4,
        initiated_by: Optional[str] = None,
        input_data: Optional[dict] = None,
    ) -> ChainExecution:
        """새 체인 실행 생성"""
        # batch_id가 빈 문자열이면 None으로 변환 (외래 키 제약 조건 위반 방지)
        batch_id = batch_id if batch_id else None

        chain_exec = ChainExecution(
            chain_id=chain_id,
            chain_name=chain_name,
            batch_id=batch_id,
            total_tasks=total_tasks,
            status=ProcessStatus.PENDING.value,
            initiated_by=initiated_by,
            input_data=input_data,
        )
        db.add(chain_exec)
        db.commit()
        db.refresh(chain_exec)
        return chain_exec

    def increment_completed_tasks(
        self, db: Session, *, chain_execution: ChainExecution
    ) -> ChainExecution:
        """완료된 작업 수 증가"""
        chain_execution.increment_completed_tasks()
        db.add(chain_execution)
        db.commit()
        db.refresh(chain_execution)
        return chain_execution

    #
    def increment_failed_tasks(
        self, db: Session, *, chain_execution: ChainExecution
    ) -> ChainExecution:
        """실패한 작업 수 증가"""
        chain_execution.increment_failed_tasks()
        db.add(chain_execution)
        db.commit()
        db.refresh(chain_execution)
        return chain_execution

    def update_status(
        self, db: Session, *, chain_execution: ChainExecution, status: ProcessStatus
    ) -> ChainExecution:
        """체인 실행 상태 업데이트"""
        chain_execution.status = status
        if status == ProcessStatus.STARTED.value:
            chain_execution.started_at = datetime.now()
        elif status in [
            ProcessStatus.SUCCESS.value,
            ProcessStatus.FAILURE.value,
            ProcessStatus.REVOKED.value,
        ]:
            chain_execution.finished_at = datetime.now()

        db.add(chain_execution)
        db.commit()
        db.refresh(chain_execution)
        return chain_execution

    def update_celery_task_id(
        self, db: Session, *, chain_execution: ChainExecution, celery_task_id: str
    ) -> ChainExecution:
        """Celery task ID 업데이트"""
        chain_execution.celery_task_id = celery_task_id
        db.add(chain_execution)
        db.commit()
        db.refresh(chain_execution)
        return chain_execution


# 인스턴스 생성
chain_execution_crud = CRUDChainExecution(ChainExecution)

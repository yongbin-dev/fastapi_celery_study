# crud/chain_execution.py

from datetime import datetime
from typing import Optional

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
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
            session.query(ChainExecution).filter(ChainExecution.id == chain_id).first()
        )

    def get_dto_by_chain_id(
        self, session: Session, *, chain_id: str
    ) -> Optional[ChainExecutionResponse]:
        """chain_id로 체인 실행 조회"""

        chain_execution = (
            session.query(ChainExecution).filter(ChainExecution.id == chain_id).first()
        )

        return ChainExecutionResponse.model_validate(chain_execution)

    def create_chain_execution(
        self,
        db: Session,
        *,
        chain_name: str,
        batch_id: Optional[str] = None,
        initiated_by: Optional[str] = None,
        input_data: Optional[dict] = None,
        sequence_number: Optional[int] = None,
    ) -> ChainExecution:
        """새 체인 실행 생성. 멱등성 보장.

        sequence_number가 주어지면 해당 번호를 사용하고, 없으면 새로 계산합니다.
        데이터베이스에 이미 해당 batch_id와 sequence_number가 존재하면
        IntegrityError를 잡아서 기존 객체를 반환합니다.
        """
        # batch_id가 빈 문자열이면 None으로 변환
        batch_id = batch_id if batch_id else None

        # sequence_number가 제공되지 않은 경우에만 계산
        if sequence_number is None:
            sequence_to_use = 1
            if batch_id:
                max_sequence = (
                    db.query(func.max(ChainExecution.sequence_number))
                    .filter(ChainExecution.batch_id == batch_id)
                    .scalar()
                )
                if max_sequence is not None:
                    sequence_to_use = max_sequence + 1
        else:
            sequence_to_use = sequence_number

        try:
            chain_exec = ChainExecution(
                chain_name=chain_name,
                batch_id=batch_id,
                sequence_number=sequence_to_use,
                status=ProcessStatus.PENDING.value,
                initiated_by=initiated_by,
                input_data=input_data,
                started_at=datetime.now(),
            )
            db.add(chain_exec)
            db.commit()
            db.refresh(chain_exec)
            return chain_exec
        except IntegrityError:
            db.rollback()
            # 이미 존재하는 객체를 조회하여 반환
            existing_exec = (
                db.query(ChainExecution)
                .filter_by(batch_id=batch_id, sequence_number=sequence_to_use)
                .one_or_none()
            )
            if existing_exec:
                return existing_exec
            else:
                # 예상치 못한 다른 IntegrityError일 경우를 대비해 재발생
                raise

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
        self, db: Session, *, chain_execution: ChainExecution, id: str
    ) -> ChainExecution:
        """Celery task ID 업데이트"""
        chain_execution.id = id
        db.add(chain_execution)
        db.commit()
        db.refresh(chain_execution)
        return chain_execution


# 인스턴스 생성
chain_execution_crud = CRUDChainExecution(ChainExecution)

# crud/chain_execution.py

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.models.chain_execution import ChainExecution
from app.orchestration.schemas.chain_execution import (
    ChainExecutionCreate,
    ChainExecutionUpdate,
)
from app.orchestration.schemas.enums import ProcessStatus

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

    #
    #     def get_by_chain_name(
    #         self, db: Session, *, chain_name: str, skip: int = 0, limit: int = 100
    #     ) -> List[ChainExecution]:
    #         """chain_name으로 체인 실행 목록 조회"""
    #         return (
    #             db.query(ChainExecution)
    #             .filter(ChainExecution.chain_name == chain_name)
    #             .order_by(desc(ChainExecution.created_at))
    #             .offset(skip)
    #             .limit(limit)
    #             .all()
    #         )
    #
    #     def get_by_status(
    #         self, db: Session, *, status: ProcessStatus, skip: int = 0, limit: int = 100
    #     ) -> List[ChainExecution]:
    #         """상태별 체인 실행 목록 조회"""
    #         return (
    #             db.query(ChainExecution)
    #             .filter(ChainExecution.status == status.value)  # type: ignore
    #             .order_by(desc(ChainExecution.created_at))  # type: ignore
    #             .offset(skip)
    #             .limit(limit)
    #             .all()
    #         )
    #
    #     def get_running_chains(self, db: Session) -> List[ChainExecution]:
    #         """실행 중인 체인 목록 조회"""
    #         return (
    #             db.query(ChainExecution)
    #             .filter(ChainExecution.status == ProcessStatus.STARTED.value)  # type: ignore
    #             .order_by(desc(ChainExecution.started_at))  # type: ignore
    #             .all()
    #         )
    #
    #     def get_completed_chains(
    #         self, db: Session, *, skip: int = 0, limit: int = 100
    #     ) -> List[ChainExecution]:
    #         """완료된 체인 목록 조회 (성공/실패 포함)"""
    #         return (
    #             db.query(ChainExecution)
    #             .filter(
    #                 ChainExecution.status.in_(  # type: ignore
    #                     [
    #                         ProcessStatus.SUCCESS.value,
    #                         ProcessStatus.FAILURE.value,
    #                         ProcessStatus.REVOKED.value,
    #                     ]
    #                 )
    #             )
    #             .order_by(desc(ChainExecution.finished_at))  # type: ignore
    #             .offset(skip)
    #             .limit(limit)
    #             .all()
    #         )
    #
    #     def get_failed_chains(
    #         self, db: Session, *, skip: int = 0, limit: int = 100
    #     ) -> List[ChainExecution]:
    #         """실패한 체인 목록 조회"""
    #         return (
    #             db.query(ChainExecution)
    #             .filter(ChainExecution.status == ProcessStatus.FAILURE.value)  # type: ignore
    #             .order_by(desc(ChainExecution.finished_at))  # type: ignore
    #             .offset(skip)
    #             .limit(limit)
    #             .all()
    #         )
    #
    #     def get_by_initiated_by(
    #         self, db: Session, *, initiated_by: str, skip: int = 0, limit: int = 100
    #     ) -> List[ChainExecution]:
    #         """시작한 사용자/시스템별 체인 실행 목록 조회"""
    #         return (
    #             db.query(ChainExecution)
    #             .filter(ChainExecution.initiated_by == initiated_by)
    #             .order_by(desc(ChainExecution.created_at))
    #             .offset(skip)
    #             .limit(limit)
    #             .all()
    #         )
    #
    def create_chain_execution(
        self,
        db: Session,
        *,
        chain_id: str,
        chain_name: str,
        total_tasks: int = 4,
        initiated_by: Optional[str] = None,
        input_data: Optional[dict] = None,
    ) -> ChainExecution:
        """새 체인 실행 생성"""
        chain_exec = ChainExecution(
            chain_id=chain_id,
            chain_name=chain_name,
            total_tasks=total_tasks,
            status=ProcessStatus.PENDING.value,
            initiated_by=initiated_by,
            input_data=input_data,
        )
        db.add(chain_exec)
        db.commit()
        db.refresh(chain_exec)
        return chain_exec

    #
    #     def start_chain(
    #         self,
    #         db: Session,
    #         *,
    #         chain_execution: ChainExecution,
    #     ) -> ChainExecution:
    #         """체인 실행 시작"""
    #         chain_execution.start_execution()
    #         db.add(chain_execution)
    #         db.commit()
    #         db.refresh(chain_execution)
    #         return chain_execution
    #
    #     def complete_chain(
    #         self,
    #         db: Session,
    #         *,
    #         chain_execution: ChainExecution,
    #         success: bool = True,
    #         final_result: Optional[dict] = None,
    #         error_message: Optional[str] = None,
    #     ) -> ChainExecution:
    #         """체인 실행 완료"""
    #         chain_execution.complete_execution(success, final_result, error_message)
    #         db.add(chain_execution)
    #         db.commit()
    #         db.refresh(chain_execution)
    #         return chain_execution
    #
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

    #
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


# 인스턴스 생성
chain_execution = CRUDChainExecution(ChainExecution)

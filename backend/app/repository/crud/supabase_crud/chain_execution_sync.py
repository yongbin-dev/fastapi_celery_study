# app/repository/crud/supabase_crud/chain_execution_sync.py
"""
ChainExecution Supabase CRUD operations (Synchronous for Celery)
"""

from datetime import datetime
from typing import Any, Dict, Optional

from supabase import Client

from app.core.logging import get_logger
from app.orchestration.schemas.enums import ProcessStatus

logger = get_logger(__name__)


class SupabaseCRUDChainExecutionSync:
    """ChainExecution Supabase CRUD 클래스 (동기 버전)"""

    def __init__(self):
        self.table_name = "chain_executions"

    def get_by_chain_id(
        self, client: Client, *, chain_id: str
    ) -> Optional[Dict[str, Any]]:
        """chain_id로 체인 실행 조회"""
        try:
            response = (
                client.table(self.table_name)
                .select("*")
                .eq("chain_id", chain_id)
                .execute()
            )

            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(
                f"Error getting chain execution by chain_id {chain_id}: {str(e)}",
                exc_info=True,
            )
            raise

    def create_chain_execution(
        self,
        client: Client,
        *,
        chain_id: str,
        chain_name: str,
        total_tasks: int = 4,
        initiated_by: Optional[str] = None,
        input_data: Optional[dict] = None,
    ) -> Dict[str, Any]:
        """새 체인 실행 생성"""
        try:
            data = {
                "chain_id": chain_id,
                "chain_name": chain_name,
                "total_tasks": total_tasks,
                "status": ProcessStatus.PENDING.value,
                "initiated_by": initiated_by,
                "input_data": input_data,
                "completed_tasks": 0,
                "failed_tasks": 0,
            }

            response = client.table(self.table_name).insert(data).execute()

            if response.data and len(response.data) > 0:
                logger.info(
                    f"ChainExecution created with chain_id: {chain_id}, id: {response.data[0].get('id')}"  # noqa: E501
                )
                return response.data[0]

            raise ValueError("Failed to create chain execution")
        except Exception as e:
            logger.error(f"Error creating chain execution: {str(e)}", exc_info=True)
            raise

    def increment_completed_tasks(
        self, client: Client, *, chain_id: str
    ) -> Optional[Dict[str, Any]]:
        """완료된 작업 수 증가"""
        try:
            # 현재 레코드 조회
            current = self.get_by_chain_id(client, chain_id=chain_id)
            if not current:
                logger.error(f"ChainExecution not found for chain_id: {chain_id}")
                return None

            completed_tasks = current.get("completed_tasks", 0) + 1
            total_tasks = current.get("total_tasks", 0)

            # 업데이트 데이터
            update_data = {"completed_tasks": completed_tasks}

            # 모든 작업이 완료되면 상태 업데이트
            if completed_tasks >= total_tasks:
                update_data["status"] = ProcessStatus.SUCCESS.value
                update_data["finished_at"] = datetime.now().isoformat()

            response = (
                client.table(self.table_name)
                .update(update_data)
                .eq("chain_id", chain_id)
                .execute()
            )

            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(
                f"Error incrementing completed tasks for chain_id {chain_id}: {str(e)}",
                exc_info=True,
            )
            raise

    def increment_failed_tasks(
        self, client: Client, *, chain_id: str
    ) -> Optional[Dict[str, Any]]:
        """실패한 작업 수 증가"""
        try:
            # 현재 레코드 조회
            current = self.get_by_chain_id(client, chain_id=chain_id)
            if not current:
                logger.error(f"ChainExecution not found for chain_id: {chain_id}")
                return None

            failed_tasks = current.get("failed_tasks", 0) + 1

            response = (
                client.table(self.table_name)
                .update({"failed_tasks": failed_tasks})
                .eq("chain_id", chain_id)
                .execute()
            )

            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(
                f"Error incrementing failed tasks for chain_id {chain_id}: {str(e)}",
                exc_info=True,
            )
            raise

    def update_status(
        self,
        client: Client,
        *,
        chain_id: str,
        status: ProcessStatus,
        error_message: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """체인 실행 상태 업데이트"""
        try:
            update_data: Dict[str, Any] = {"status": status.value}

            if status == ProcessStatus.STARTED:
                update_data["started_at"] = datetime.now().isoformat()
            elif status in [
                ProcessStatus.SUCCESS,
                ProcessStatus.FAILURE,
                ProcessStatus.REVOKED,
            ]:
                update_data["finished_at"] = datetime.now().isoformat()

            if error_message:
                update_data["error_message"] = error_message

            response = (
                client.table(self.table_name)
                .update(update_data)
                .eq("chain_id", chain_id)
                .execute()
            )

            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(
                f"Error updating status for chain_id {chain_id}: {str(e)}",
                exc_info=True,
            )
            raise


# 싱글톤 인스턴스
supabase_chain_execution_sync = SupabaseCRUDChainExecutionSync()

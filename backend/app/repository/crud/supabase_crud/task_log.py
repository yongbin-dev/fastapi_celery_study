# app/repository/crud/supabase_crud/task_log.py
"""
TaskLog Supabase CRUD operations
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from supabase import Client

from app.core.logging import get_logger

logger = get_logger(__name__)


class SupabaseCRUDTaskLog:
    """TaskLog Supabase CRUD 클래스"""

    def __init__(self):
        self.table_name = "task_logs"

    def create_task_log(
        self,
        client: Client,
        *,
        task_id: str,
        task_name: str,
        status: str = "STARTED",
        args: Optional[str] = None,
        kwargs: Optional[str] = None,
        chain_execution_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """TaskLog 생성"""
        try:
            data = {
                "task_id": task_id,
                "task_name": task_name,
                "status": status,
                "args": args,
                "kwargs": kwargs,
                "chain_execution_id": chain_execution_id,
                "started_at": datetime.now().isoformat(),
            }

            response = client.table(self.table_name).insert(data).execute()

            if response.data and len(response.data) > 0:
                logger.info(
                    f"TaskLog created: task_id={task_id}, id={response.data[0].get('id')}"  # noqa: E501
                )  # noqa: E501
                return response.data[0]

            raise ValueError("Failed to create task log")
        except Exception as e:
            logger.error(f"Error creating task log: {str(e)}", exc_info=True)
            raise

    def update_status(
        self,
        client: Client,
        *,
        task_log_id: int,
        status: str,
        result: Optional[str] = None,
        error: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """TaskLog 상태 업데이트"""
        try:
            update_data: Dict[str, Any] = {
                "status": status,
                "finished_at": datetime.now().isoformat(),
            }

            if result:
                update_data["result"] = result
            if error:
                update_data["error"] = error

            response = (
                client.table(self.table_name)
                .update(update_data)
                .eq("id", task_log_id)
                .execute()
            )

            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(
                f"Error updating task log status for id {task_log_id}: {str(e)}",
                exc_info=True,
            )
            raise

    def get_by_task_id(
        self, client: Client, *, task_id: str
    ) -> Optional[Dict[str, Any]]:
        """task_id로 TaskLog 조회"""
        try:
            response = (
                client.table(self.table_name)
                .select("*")
                .eq("task_id", task_id)
                .execute()
            )

            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(
                f"Error getting task log by task_id {task_id}: {str(e)}",
                exc_info=True,
            )
            raise

    def get_by_chain_execution_id(
        self, client: Client, *, chain_execution_id: int
    ) -> List[Dict[str, Any]]:
        """chain_execution_id로 TaskLog 목록 조회"""
        try:
            response = (
                client.table(self.table_name)
                .select("*")
                .eq("chain_execution_id", chain_execution_id)
                .order("started_at")
                .execute()
            )

            return response.data
        except Exception as e:
            logger.error(
                f"Error getting task logs by chain_execution_id {chain_execution_id}: {str(e)}",  # noqa: E501
                exc_info=True,
            )
            raise


# 싱글톤 인스턴스
supabase_task_log = SupabaseCRUDTaskLog()

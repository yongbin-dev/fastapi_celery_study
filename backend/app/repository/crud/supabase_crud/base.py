# app/repository/crud/supabase_crud/base.py
"""
Supabase 기반 CRUD 기본 클래스
"""

from typing import Any, Dict, Generic, List, Optional, TypeVar

from pydantic import BaseModel
from supabase import Client

from app.core.logging import get_logger

logger = get_logger(__name__)

# Pydantic 모델 타입
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class SupabaseCRUDBase(Generic[CreateSchemaType, UpdateSchemaType]):
    """
    Supabase CRUD 기본 클래스

    Args:
        table_name: Supabase 테이블 이름
    """

    def __init__(self, table_name: str):
        self.table_name = table_name

    async def get_by_id(self, client: Client, *, id: int) -> Optional[Dict[str, Any]]:
        """ID로 단일 레코드 조회"""
        try:
            response = client.table(self.table_name).select("*").eq("id", id).execute()

            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error getting record by id {id}: {str(e)}", exc_info=True)
            raise

    async def get_all(
        self, client: Client, *, skip: int = 0, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """전체 레코드 조회 (페이지네이션)"""
        try:
            response = (
                client.table(self.table_name)
                .select("*")
                .range(skip, skip + limit - 1)
                .execute()
            )
            return response.data
        except Exception as e:
            logger.error(f"Error getting all records: {str(e)}", exc_info=True)
            raise

    async def create(
        self, client: Client, *, obj_in: CreateSchemaType
    ) -> Dict[str, Any]:
        """새 레코드 생성"""
        try:
            data = obj_in.model_dump(exclude_unset=True)
            response = client.table(self.table_name).insert(data).execute()

            if response.data and len(response.data) > 0:
                return response.data[0]
            raise ValueError("Failed to create record")
        except Exception as e:
            logger.error(f"Error creating record: {str(e)}", exc_info=True)
            raise

    async def update(
        self,
        client: Client,
        *,
        id: int,
        obj_in: UpdateSchemaType,
    ) -> Optional[Dict[str, Any]]:
        """레코드 업데이트"""
        try:
            data = obj_in.model_dump(exclude_unset=True)
            response = (
                client.table(self.table_name)
                .update(data)
                .eq("id", id)
                .execute()
            )

            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error updating record {id}: {str(e)}", exc_info=True)
            raise

    async def delete(self, client: Client, *, id: int) -> bool:
        """레코드 삭제"""
        try:
            response = client.table(self.table_name).delete().eq("id", id).execute()
            return response.data is not None
        except Exception as e:
            logger.error(f"Error deleting record {id}: {str(e)}", exc_info=True)
            raise

    async def exists(self, client: Client, *, id: int) -> bool:
        """레코드 존재 여부 확인"""
        try:
            response = (
                client.table(self.table_name)
                .select("id")
                .eq("id", id)
                .execute()
            )
            return response.data is not None and len(response.data) > 0
        except Exception as e:
            logger.error(f"Error checking existence of record {id}: {str(e)}", exc_info=True)
            raise

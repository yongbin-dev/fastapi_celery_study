# crud/async_crud/base.py

"""
비동기 기본 CRUD 연산 클래스
"""

from typing import Any, Dict, Generic, Optional, Type, TypeVar, Union

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.base import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class AsyncCRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """비동기 기본 CRUD 연산 클래스"""

    def __init__(self, model: Type[ModelType]):
        """
        Async CRUD object with default methods to Create, Read, Update, Delete (CRUD).

        **Parameters**

        * `model`: SQLAlchemy 모델 클래스
        """
        self.model = model

    async def get(self, db: AsyncSession, id: Any) -> Optional[ModelType]:
        """ID로 단일 객체 조회"""
        stmt = select(self.model).where(self.model.id == id)  # type: ignore
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, db: AsyncSession, *, obj_in: CreateSchemaType) -> ModelType:
        """객체 생성"""
        obj_in_data = obj_in.dict() if hasattr(obj_in, "dict") else obj_in
        db_obj = self.model(**obj_in_data)  # type: ignore
        db.add(db_obj)
        await db.flush()  # ID 할당을 위해 flush
        await db.refresh(db_obj)  # 객체 상태 갱신
        return db_obj

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]],
    ) -> ModelType:
        """객체 업데이트"""
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)

        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)

        db.add(db_obj)
        return db_obj

    async def remove(self, db: AsyncSession, *, id: int) -> Optional[ModelType]:
        """객체 삭제"""
        stmt = select(self.model).where(self.model.id == id)  # type: ignore
        result = await db.execute(stmt)
        obj = result.scalar_one_or_none()

        if obj:
            await db.delete(obj)
            await db.commit()
        return obj

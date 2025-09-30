# crud/async_crud/base.py

"""
비동기 기본 CRUD 연산 클래스
"""

from typing import Any, Dict, Generic, Optional, Type, TypeVar, Union

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Base

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
        try:
            stmt = select(self.model).where(self.model.id == id)  # type: ignore
            result = await db.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            await db.rollback()
            raise e

    async def create(self, db: AsyncSession, *, obj_in: CreateSchemaType) -> ModelType:
        """객체 생성"""
        try:
            obj_in_data = obj_in.dict() if hasattr(obj_in, "dict") else obj_in
            db_obj = self.model(**obj_in_data)  # type: ignore
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)
            return db_obj
        except SQLAlchemyError as e:
            await db.rollback()
            raise e

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]],
    ) -> ModelType:
        """객체 업데이트"""
        try:
            if isinstance(obj_in, dict):
                update_data = obj_in
            else:
                update_data = obj_in.dict(exclude_unset=True)

            for field, value in update_data.items():
                if hasattr(db_obj, field):
                    setattr(db_obj, field, value)

            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)
            return db_obj
        except SQLAlchemyError as e:
            await db.rollback()
            raise e

    async def remove(self, db: AsyncSession, *, id: int) -> Optional[ModelType]:
        """객체 삭제"""
        try:
            stmt = select(self.model).where(self.model.id == id)  # type: ignore
            result = await db.execute(stmt)
            obj = result.scalar_one_or_none()

            if obj:
                await db.delete(obj)
                await db.commit()
            return obj
        except SQLAlchemyError as e:
            await db.rollback()
            raise e

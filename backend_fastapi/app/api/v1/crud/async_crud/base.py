# crud/async_crud/base.py

"""
비동기 기본 CRUD 연산 클래스
"""

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.exc import SQLAlchemyError

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
            stmt = select(self.model).where(self.model.id == id)
            result = await db.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            await db.rollback()
            raise e

    async def get_multi(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        """다중 객체 조회 (페이지네이션 지원)"""
        try:
            stmt = select(self.model).offset(skip).limit(limit)
            result = await db.execute(stmt)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            await db.rollback()
            raise e

    async def create(self, db: AsyncSession, *, obj_in: CreateSchemaType) -> ModelType:
        """객체 생성"""
        try:
            obj_in_data = obj_in.dict() if hasattr(obj_in, "dict") else obj_in
            db_obj = self.model(**obj_in_data)
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)
            return db_obj
        except SQLAlchemyError as e:
            await db.rollback()
            raise e

    async def create_from_dict(
        self, db: AsyncSession, *, obj_in: Dict[str, Any]
    ) -> ModelType:
        """딕셔너리에서 새 객체 생성"""
        try:
            db_obj = self.model(**obj_in)
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
            stmt = select(self.model).where(self.model.id == id)
            result = await db.execute(stmt)
            obj = result.scalar_one_or_none()

            if obj:
                await db.delete(obj)
                await db.commit()
            return obj
        except SQLAlchemyError as e:
            await db.rollback()
            raise e

    async def count(self, db: AsyncSession) -> int:
        """전체 객체 수 조회"""
        try:
            stmt = select(func.count(self.model.id))
            result = await db.execute(stmt)
            return result.scalar()
        except SQLAlchemyError as e:
            await db.rollback()
            raise e

    async def exists(self, db: AsyncSession, *, id: Any) -> bool:
        """객체 존재 여부 확인"""
        try:
            stmt = select(self.model.id).where(self.model.id == id)
            result = await db.execute(stmt)
            return result.scalar_one_or_none() is not None
        except SQLAlchemyError as e:
            await db.rollback()
            raise e

    async def get_by_field(
        self, db: AsyncSession, *, field_name: str, field_value: Any
    ) -> Optional[ModelType]:
        """특정 필드 값으로 객체 조회"""
        try:
            if hasattr(self.model, field_name):
                stmt = select(self.model).where(
                    getattr(self.model, field_name) == field_value
                )
                result = await db.execute(stmt)
                return result.scalar_one_or_none()
            return None
        except SQLAlchemyError as e:
            await db.rollback()
            raise e

    async def get_multi_by_field(
        self,
        db: AsyncSession,
        *,
        field_name: str,
        field_value: Any,
        skip: int = 0,
        limit: int = 100,
    ) -> List[ModelType]:
        """특정 필드 값으로 다중 객체 조회"""
        try:
            if hasattr(self.model, field_name):
                stmt = (
                    select(self.model)
                    .where(getattr(self.model, field_name) == field_value)
                    .offset(skip)
                    .limit(limit)
                )
                result = await db.execute(stmt)
                return list(result.scalars().all())
            return []
        except SQLAlchemyError as e:
            await db.rollback()
            raise e

    async def create_bulk(
        self, db: AsyncSession, *, objs_in: List[CreateSchemaType]
    ) -> List[ModelType]:
        """대량 객체 생성"""
        try:
            db_objs = []
            for obj_in in objs_in:
                obj_in_data = obj_in.dict() if hasattr(obj_in, "dict") else obj_in
                db_obj = self.model(**obj_in_data)
                db_objs.append(db_obj)
                db.add(db_obj)

            await db.commit()
            for db_obj in db_objs:
                await db.refresh(db_obj)

            return db_objs
        except SQLAlchemyError as e:
            await db.rollback()
            raise e

    async def delete_multi(self, db: AsyncSession, *, ids: List[int]) -> int:
        """다중 객체 삭제"""
        try:
            stmt = delete(self.model).where(self.model.id.in_(ids))
            result = await db.execute(stmt)
            await db.commit()
            return result.rowcount
        except SQLAlchemyError as e:
            await db.rollback()
            raise e


class AsyncCRUDBaseWithSoftDelete(
    AsyncCRUDBase[ModelType, CreateSchemaType, UpdateSchemaType]
):
    """소프트 삭제를 지원하는 비동기 CRUD 클래스"""

    async def get(self, db: AsyncSession, id: Any) -> Optional[ModelType]:
        """ID로 단일 객체 조회 (삭제되지 않은 것만)"""
        try:
            stmt = select(self.model).where(
                self.model.id == id, self.model.is_deleted == False  # noqa
            )
            result = await db.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            await db.rollback()
            raise e

    async def get_multi(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        """다중 객체 조회 (삭제되지 않은 것만)"""
        try:
            stmt = (
                select(self.model)
                .where(self.model.is_deleted == False)  # noqa
                .offset(skip)
                .limit(limit)
            )
            result = await db.execute(stmt)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            await db.rollback()
            raise e

    async def soft_delete(self, db: AsyncSession, *, id: int) -> ModelType:
        """소프트 삭제"""
        try:
            stmt = select(self.model).where(self.model.id == id)
            result = await db.execute(stmt)
            obj = result.scalar_one_or_none()

            if obj:
                obj.is_deleted = True
                db.add(obj)
                await db.commit()
                await db.refresh(obj)
            return obj
        except SQLAlchemyError as e:
            await db.rollback()
            raise e

    async def restore(self, db: AsyncSession, *, id: int) -> Optional[ModelType]:
        """삭제된 객체 복구"""
        try:
            stmt = select(self.model).where(
                self.model.id == id, self.model.is_deleted == True  # noqa
            )
            result = await db.execute(stmt)
            obj = result.scalar_one_or_none()

            if obj:
                obj.is_deleted = False
                db.add(obj)
                await db.commit()
                await db.refresh(obj)

            return obj
        except SQLAlchemyError as e:
            await db.rollback()
            raise e

    async def get_deleted(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        """삭제된 객체들 조회"""
        try:
            stmt = (
                select(self.model)
                .where(self.model.is_deleted == True)  # noqa
                .offset(skip)
                .limit(limit)
            )
            result = await db.execute(stmt)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            await db.rollback()
            raise e

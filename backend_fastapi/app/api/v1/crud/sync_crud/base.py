# app/crud/base.py
"""
기본 CRUD 연산 클래스
"""

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """기본 CRUD 연산 클래스"""

    def __init__(self, model: Type[ModelType]):
        """
        CRUD object with default methods to Create, Read, Update, Delete (CRUD).

        **Parameters**

        * `model`: SQLAlchemy 모델 클래스
        """
        self.model = model

    def get(self, db: Session, id: Any) -> Optional[ModelType]:
        """ID로 단일 객체 조회"""
        return db.query(self.model).filter(self.model.id == id).first()

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        """다중 객체 조회 (페이지네이션 지원)"""
        return db.query(self.model).offset(skip).limit(limit).all()

    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        """객체 생성"""
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data)  # type: ignore
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self,
        db: Session,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]],
    ) -> ModelType:
        """객체 업데이트"""
        obj_data = jsonable_encoder(db_obj)
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)

        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, *, id: int) -> ModelType:
        """객체 삭제"""
        obj = db.query(self.model).get(id)
        db.delete(obj)
        db.commit()
        return obj

    def count(self, db: Session) -> int:
        """전체 객체 수 조회"""
        return db.query(self.model).count()

    def exists(self, db: Session, *, id: int) -> bool:
        """객체 존재 여부 확인"""
        return db.query(self.model).filter(self.model.id == id).first() is not None

    def get_by_field(
        self, db: Session, *, field_name: str, field_value: Any
    ) -> Optional[ModelType]:
        """특정 필드 값으로 객체 조회"""
        return (
            db.query(self.model)
            .filter(getattr(self.model, field_name) == field_value)
            .first()
        )

    def get_multi_by_field(
        self,
        db: Session,
        *,
        field_name: str,
        field_value: Any,
        skip: int = 0,
        limit: int = 100,
    ) -> List[ModelType]:
        """특정 필드 값으로 다중 객체 조회"""
        return (
            db.query(self.model)
            .filter(getattr(self.model, field_name) == field_value)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create_bulk(
        self, db: Session, *, objs_in: List[CreateSchemaType]
    ) -> List[ModelType]:
        """대량 객체 생성"""
        db_objs = []
        for obj_in in objs_in:
            obj_in_data = jsonable_encoder(obj_in)
            db_obj = self.model(**obj_in_data)
            db_objs.append(db_obj)
            db.add(db_obj)

        db.commit()
        for db_obj in db_objs:
            db.refresh(db_obj)

        return db_objs

    def delete_multi(self, db: Session, *, ids: List[int]) -> int:
        """다중 객체 삭제"""
        deleted_count = db.query(self.model).filter(self.model.id.in_(ids)).delete()
        db.commit()
        return deleted_count


class CRUDBaseWithSoftDelete(CRUDBase[ModelType, CreateSchemaType, UpdateSchemaType]):
    """소프트 삭제를 지원하는 CRUD 클래스"""

    def get(self, db: Session, id: Any) -> Optional[ModelType]:
        """ID로 단일 객체 조회 (삭제되지 않은 것만)"""
        return (
            db.query(self.model)
            .filter(self.model.id == id, self.model.is_deleted == False)  # noqa
            .first()
        )

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        """다중 객체 조회 (삭제되지 않은 것만)"""
        return (
            db.query(self.model)
            .filter(self.model.is_deleted == False)  # noqa
            .offset(skip)
            .limit(limit)
            .all()
        )

    def soft_delete(self, db: Session, *, id: int) -> ModelType:
        """소프트 삭제"""
        obj = db.query(self.model).get(id)
        obj.is_deleted = True
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    def restore(self, db: Session, *, id: int) -> ModelType:
        """삭제된 객체 복구"""
        obj = (
            db.query(self.model)
            .filter(self.model.id == id, self.model.is_deleted == True)  # noqa
            .first()
        )

        if obj:
            obj.is_deleted = False
            db.add(obj)
            db.commit()
            db.refresh(obj)

        return obj

    def get_deleted(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        """삭제된 객체들 조회"""
        return (
            db.query(self.model)
            .filter(self.model.is_deleted == True)  # noqa
            .offset(skip)
            .limit(limit)
            .all()
        )

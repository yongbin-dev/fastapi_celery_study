# app/crud/base.py
"""
기본 CRUD 연산 클래스
"""

from typing import Any, Dict, Generic, Optional, Type, TypeVar, Union

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy.orm import Session

from shared.models.base import Base

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
        return db.query(self.model).filter(self.model.id == id).first()  # type: ignore

    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        """객체 생성"""
        # model_dump(by_alias=False)를 사용하여 원본 필드명(스네이크 케이스)으로 변환
        obj_in_data = obj_in.model_dump(by_alias=False)
        db_obj = self.model(**obj_in_data)
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
            # model_dump(by_alias=False)를 사용하여 원본 필드명(스네이크 케이스)으로 변환
            update_data = obj_in.model_dump(exclude_unset=True, by_alias=False)

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
        return obj  # type: ignore

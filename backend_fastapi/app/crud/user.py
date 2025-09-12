# app/crud/user.py
"""
사용자 CRUD 연산
"""

from typing import Any, Dict, Optional, Union, List

from sqlalchemy.orm import Session

from .base import CRUDBase
from ..models.user import User  # 실제 User 모델이 구현되면 import
# from ..schemas.user import UserCreate, UserUpdate  # 실제 스키마가 구현되면 import
# from ..security.jwt import PasswordManager
#
#
class CRUDUser(CRUDBase[User]):
#     """사용자 CRUD 클래스"""
#
    def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
        """이메일로 사용자 조회"""
        # TODO: 실제 User 모델 구현 후 활성화
        # return db.query(User).filter(User.email == email).first()
        pass
#
#     def get_by_username(self, db: Session, *, username: str) -> Optional[User]:
#         """사용자명으로 사용자 조회"""
#         # TODO: 실제 User 모델 구현 후 활성화
#         # return db.query(User).filter(User.username == username).first()
#         pass
#
#     def create(self, db: Session, *, obj_in: UserCreate) -> User:
#         """사용자 생성 (패스워드 해싱 포함)"""
#         # TODO: 실제 구현
#         # create_data = obj_in.dict()
#         # create_data.pop("password")
#         # db_obj = User(**create_data)
#         # db_obj.hashed_password = PasswordManager.get_password_hash(obj_in.password)
#         # db.add(db_obj)
#         # db.commit()
#         # db.refresh(db_obj)
#         # return db_obj
#         pass
#
#     def update(
#         self,
#         db: Session,
#         *,
#         db_obj: User,
#         obj_in: Union[UserUpdate, Dict[str, Any]]
#     ) -> User:
#         """사용자 정보 업데이트 (패스워드 해싱 포함)"""
#         # TODO: 실제 구현
#         # if isinstance(obj_in, dict):
#         #     update_data = obj_in
#         # else:
#         #     update_data = obj_in.dict(exclude_unset=True)
#         #
#         # if "password" in update_data:
#         #     hashed_password = PasswordManager.get_password_hash(update_data["password"])
#         #     del update_data["password"]
#         #     update_data["hashed_password"] = hashed_password
#         #
#         # return super().update(db, db_obj=db_obj, obj_in=update_data)
#         pass
#
#     def authenticate(
#         self,
#         db: Session,
#         *,
#         email: str,
#         password: str
#     ) -> Optional[User]:
#         """사용자 인증"""
#         # TODO: 실제 구현
#         # user = self.get_by_email(db, email=email)
#         # if not user:
#         #     return None
#         # if not PasswordManager.verify_password(password, user.hashed_password):
#         #     return None
#         # return user
#         pass
#
#     def is_active(self, user: User) -> bool:
#         """사용자 활성 상태 확인"""
#         # TODO: 실제 구현
#         # return user.is_active
#         return True
#
#     def is_superuser(self, user: User) -> bool:
#         """슈퍼유저 확인"""
#         # TODO: 실제 구현
#         # return user.is_superuser
#         return False
#
#     def activate(self, db: Session, *, db_obj: User) -> User:
#         """사용자 활성화"""
#         # TODO: 실제 구현
#         # db_obj.is_active = True
#         # db.add(db_obj)
#         # db.commit()
#         # db.refresh(db_obj)
#         # return db_obj
#         pass
#
#     def deactivate(self, db: Session, *, db_obj: User) -> User:
#         """사용자 비활성화"""
#         # TODO: 실제 구현
#         # db_obj.is_active = False
#         # db.add(db_obj)
#         # db.commit()
#         # db.refresh(db_obj)
#         # return db_obj
#         pass
#
#     def get_active_users(
#         self,
#         db: Session,
#         *,
#         skip: int = 0,
#         limit: int = 100
#     ) -> List[User]:
#         """활성 사용자 목록 조회"""
#         # TODO: 실제 구현
#         # return db.query(User).filter(User.is_active == True).offset(skip).limit(limit).all()
#         pass
#
#     def search_users(
#         self,
#         db: Session,
#         *,
#         query: str,
#         skip: int = 0,
#         limit: int = 100
#     ) -> List[User]:
#         """사용자 검색 (이메일, 사용자명, 이름으로 검색)"""
#         # TODO: 실제 구현
#         # search_filter = db.query(User).filter(
#         #     db.or_(
#         #         User.email.contains(query),
#         #         User.username.contains(query),
#         #         User.full_name.contains(query)
#         #     )
#         # )
#         # return search_filter.offset(skip).limit(limit).all()
#         pass


# 전역 인스턴스
user = CRUDUser(User)
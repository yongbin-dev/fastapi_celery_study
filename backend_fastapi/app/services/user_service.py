# services/user_service.py
from typing import Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models.user import User
from ..schemas.user import UserCreateRequest, UserUpdateRequest, UserResponse
from ..exceptions import (
    UserNotFoundException,
    UserEmailAlreadyExistsException,
    UserUsernameAlreadyExistsException,
    UserServiceException,
)


class UserService:
    def __init__(self):
        return

    async def create_user(self,
                          user_data: UserCreateRequest,
                          db: AsyncSession
                          ) -> User:

        try:
            # 이메일 중복 확인
            email_check = await db.execute(
                select(User).where(User.email == user_data.email)
            )
            if email_check.scalar_one_or_none():
                raise UserEmailAlreadyExistsException(user_data.email)

            # 사용자명 중복 확인
            username_check = await db.execute(
                select(User).where(User.username == user_data.username)
            )
            if username_check.scalar_one_or_none():
                raise UserUsernameAlreadyExistsException(user_data.username)

            # 새 사용자 생성
            new_user = User(
                email=user_data.email,
                username=user_data.username,
                full_name=user_data.full_name,
                bio=user_data.bio,
                is_active=user_data.is_active,
                is_superuser=user_data.is_superuser
            )

            db.add(new_user)
            await db.commit()
            await db.refresh(new_user)

            return new_user

        except (UserEmailAlreadyExistsException, UserUsernameAlreadyExistsException):
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            raise UserServiceException(f"사용자 생성 실패: {str(e)}")

    async def get_users(self, skip: int, limit: int, db: AsyncSession) -> Dict[str, Any]:
        """사용자 목록 조회"""
        try:
            stmt = select(User).offset(skip).limit(limit)
            result = await db.execute(stmt)
            users = result.scalars().all()
            
            users_data = [user.dict() for user in users]
            
            return {
                "users": users_data,
                "total": len(users_data),
                "skip": skip,
                "limit": limit
            }
        except Exception as e:
            raise UserServiceException(f"사용자 조회 실패: {str(e)}")

    async def get_user_by_id(self, user_id: int, db: AsyncSession) -> User:
        """특정 사용자 조회"""
        try:
            stmt = select(User).where(User.id == user_id)
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user:
                raise UserNotFoundException(user_id=user_id)
            
            return user
        except UserNotFoundException:
            raise
        except Exception as e:
            raise UserServiceException(f"사용자 조회 실패: {str(e)}")

    async def get_users(self, skip: int, limit: int, db: AsyncSession) -> Dict[str, Any]:
        """사용자 목록 조회"""
        try:
            stmt = select(User).offset(skip).limit(limit)
            result = await db.execute(stmt)
            users = result.scalars().all()
            
            users_data = [user.dict() for user in users]
            
            return {
                "users": users_data,
                "total": len(users_data),
                "skip": skip,
                "limit": limit
            }
        except Exception as e:
            raise UserServiceException(f"사용자 조회 실패: {str(e)}")

    async def update_user(self, user_id: int, user_data: UserUpdateRequest, db: AsyncSession) -> User:
        """사용자 정보 수정"""
        try:
            # 사용자 존재 확인
            stmt = select(User).where(User.id == user_id)
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user:
                raise UserNotFoundException(user_id=user_id)
            
            # 수정할 필드만 업데이트
            update_data = user_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                if hasattr(user, field):
                    setattr(user, field, value)
            
            await db.commit()
            await db.refresh(user)
            
            return user
        
        except UserNotFoundException:
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            raise UserServiceException(f"사용자 수정 실패: {str(e)}")

    async def delete_user(self, user_id: int, db: AsyncSession) -> Dict[str, Any]:
        """사용자 삭제"""
        try:
            # 사용자 존재 확인
            stmt = select(User).where(User.id == user_id)
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user:
                raise UserNotFoundException(user_id=user_id)
            
            await db.delete(user)
            await db.commit()
            
            return {
                "deleted_user_id": user_id,
                "message": f"사용자 ID {user_id}가 삭제되었습니다"
            }
        
        except UserNotFoundException:
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            raise UserServiceException(f"사용자 삭제 실패: {str(e)}")

# 전역 서비스 인스턴스
user_service = UserService()

# 의존성 주입 함수
def get_user_service() -> UserService:
    """User 서비스 의존성"""
    return user_service

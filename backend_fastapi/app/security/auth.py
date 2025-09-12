# app/security/auth.py
"""
인증 및 권한 관리
"""

from datetime import datetime
from typing import Optional, Union

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from ..core.exceptions import UnauthorizedError, ForbiddenError
from ..api.deps import get_db
from .jwt import JWTManager

# HTTP Bearer 토큰 스킴
security = HTTPBearer()


class AuthService:
    """인증 서비스 클래스"""

    @staticmethod
    def authenticate_user(
        email: str,
        password: str,
        db: Session
    ) -> Optional[dict]:
        """사용자 인증"""
        # TODO: 실제 사용자 모델과 연동
        # user = db.query(User).filter(User.email == email).first()
        # if user and PasswordManager.verify_password(password, user.hashed_password):
        #     return user
        # return None
        
        # 임시 구현
        if email == "test@example.com" and password == "password":
            return {
                "id": 1,
                "email": email,
                "username": "testuser",
                "is_active": True
            }
        return None

    @staticmethod
    def create_tokens(user_data: dict) -> dict:
        """토큰 생성"""
        access_token = JWTManager.create_access_token(
            data={"sub": str(user_data["id"]), "email": user_data["email"]}
        )
        refresh_token = JWTManager.create_refresh_token(
            data={"sub": str(user_data["id"])}
        )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }


# 의존성 함수들

async def get_current_user_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """현재 사용자 토큰 검증"""
    token = credentials.credentials
    
    try:
        payload = JWTManager.verify_token(token)
        if payload is None:
            raise UnauthorizedError("토큰이 유효하지 않습니다")
        
        user_id: str = payload.get("sub")
        if user_id is None:
            raise UnauthorizedError("토큰에서 사용자 정보를 찾을 수 없습니다")
        
        return payload
    except Exception as e:
        raise UnauthorizedError("인증에 실패했습니다") from e


async def get_current_user(
    token_payload: dict = Depends(get_current_user_token),
    db: Session = Depends(get_db)
) -> dict:
    """현재 사용자 정보 조회"""
    user_id = token_payload.get("sub")
    
    # TODO: 실제 데이터베이스에서 사용자 조회
    # user = db.query(User).filter(User.id == user_id).first()
    # if not user:
    #     raise UnauthorizedError("사용자를 찾을 수 없습니다")
    # return user
    
    # 임시 구현
    return {
        "id": int(user_id),
        "email": token_payload.get("email"),
        "username": "testuser",
        "is_active": True
    }


async def get_current_active_user(
    current_user: dict = Depends(get_current_user)
) -> dict:
    """현재 활성 사용자 조회"""
    if not current_user.get("is_active"):
        raise ForbiddenError("비활성화된 계정입니다")
    return current_user


# 권한 검사 의존성들

class RequirePermissions:
    """권한 요구사항을 확인하는 의존성 클래스"""

    def __init__(self, *permissions: str):
        self.required_permissions = permissions

    def __call__(
        self,
        current_user: dict = Depends(get_current_active_user)
    ) -> dict:
        """권한 확인"""
        # TODO: 실제 권한 시스템과 연동
        # user_permissions = get_user_permissions(current_user["id"])
        # 
        # for permission in self.required_permissions:
        #     if permission not in user_permissions:
        #         raise ForbiddenError(f"'{permission}' 권한이 필요합니다")
        
        return current_user


class RequireRoles:
    """역할 요구사항을 확인하는 의존성 클래스"""

    def __init__(self, *roles: str):
        self.required_roles = roles

    def __call__(
        self,
        current_user: dict = Depends(get_current_active_user)
    ) -> dict:
        """역할 확인"""
        # TODO: 실제 역할 시스템과 연동
        # user_roles = get_user_roles(current_user["id"])
        # 
        # if not any(role in user_roles for role in self.required_roles):
        #     raise ForbiddenError(f"다음 역할 중 하나가 필요합니다: {', '.join(self.required_roles)}")
        
        return current_user


# 편의 함수들
require_admin = RequireRoles("admin")
require_user = RequireRoles("user", "admin")
require_read_permission = RequirePermissions("read")
require_write_permission = RequirePermissions("write")
require_delete_permission = RequirePermissions("delete")
# app/security/jwt.py
"""
JWT 토큰 관련 유틸리티
"""

from datetime import datetime, timedelta
from typing import Optional, Union, Any

import jwt
from passlib.context import CryptContext

from ..core.config import settings


# 패스워드 해싱 컨텍스트
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class JWTManager:
    """JWT 토큰 관리 클래스"""

    @staticmethod
    def create_access_token(
        data: dict,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """액세스 토큰 생성"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )
        
        to_encode.update({"exp": expire})
        
        encoded_jwt = jwt.encode(
            to_encode,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
        
        return encoded_jwt

    @staticmethod
    def create_refresh_token(data: dict) -> str:
        """리프레시 토큰 생성"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=7)  # 7일
        to_encode.update({"exp": expire})
        
        encoded_jwt = jwt.encode(
            to_encode,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
        
        return encoded_jwt

    @staticmethod
    def verify_token(token: str) -> Optional[dict]:
        """토큰 검증"""
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.JWTError:
            return None

    @staticmethod
    def decode_token(token: str) -> dict:
        """토큰 디코딩 (검증 포함)"""
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise ValueError("토큰이 만료되었습니다")
        except jwt.JWTError:
            raise ValueError("유효하지 않은 토큰입니다")


class PasswordManager:
    """패스워드 관리 클래스"""

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """패스워드 검증"""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        """패스워드 해싱"""
        return pwd_context.hash(password)

    @staticmethod
    def generate_password_reset_token(email: str) -> str:
        """패스워드 재설정 토큰 생성"""
        delta = timedelta(hours=1)  # 1시간 유효
        return JWTManager.create_access_token(
            data={"sub": email, "type": "password_reset"},
            expires_delta=delta
        )

    @staticmethod
    def verify_password_reset_token(token: str) -> Optional[str]:
        """패스워드 재설정 토큰 검증"""
        try:
            payload = JWTManager.verify_token(token)
            if payload and payload.get("type") == "password_reset":
                return payload.get("sub")
        except Exception:
            pass
        return None
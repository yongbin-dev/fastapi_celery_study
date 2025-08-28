# app/schemas/user.py

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class UserCreateRequest(BaseModel):
    """사용자 생성 요청 스키마"""
    email: str
    username: str
    full_name: Optional[str] = None
    bio: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False


class UserUpdateRequest(BaseModel):
    """사용자 수정 요청 스키마"""
    full_name: Optional[str] = None
    bio: Optional[str] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None


class UserResponse(BaseModel):
    """사용자 응답 스키마"""
    id: int
    email: str
    username: str
    full_name: Optional[str]
    bio: Optional[str]
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
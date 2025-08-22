from fastapi import APIRouter, Query
from pydantic import BaseModel
from app.core.exceptions import NotFoundError, ValidationError
from app.utils.response_builder import ResponseBuilder

router = APIRouter()

class User(BaseModel):
    id: int
    name: str
    email: str


class CreateUserRequest(BaseModel):
    name: str
    email: str


# 가상 데이터
fake_users = [
    {"id": 1, "name": "홍길동", "email": "hong@example.com"},
    {"id": 2, "name": "김철수", "email": "kim@example.com"},
    {"id": 3, "name": "이영희", "email": "lee@example.com"},
]


@router.get("/users")
async def get_users(
        page: int = Query(1, ge=1),
        size: int = Query(10, ge=1, le=100)
):
    """유저 목록 조회 (자동 변환)"""
    start = (page - 1) * size
    end = start + size

    return fake_users[start:end]


@router.get("/users/paginated")
async def get_users_paginated(
        page: int = Query(1, ge=1),
        size: int = Query(10, ge=1, le=100)
):
    """유저 목록 조회 (페이지네이션)"""
    start = (page - 1) * size
    end = start + size

    return ResponseBuilder.paginated(
        data=fake_users[start:end],
        page=page,
        size=size,
        total=len(fake_users),
        message="유저 목록 조회 성공"
    )


@router.get("/users/{user_id}")
async def get_user(user_id: int):
    """유저 상세 조회"""
    if user_id <= 0:
        raise ValidationError("유저 ID는 0보다 커야 합니다")

    user = next((u for u in fake_users if u["id"] == user_id), None)
    if not user:
        raise NotFoundError(f"ID {user_id}인 유저를 찾을 수 없습니다")

    return user


@router.post("/users")
async def create_user(user_data: CreateUserRequest):
    """유저 생성"""
    new_user = {
        "id": len(fake_users) + 1,
        **user_data.dict()
    }
    fake_users.append(new_user)

    return ResponseBuilder.success(
        data=new_user,
        message="유저 생성 완료"
    )
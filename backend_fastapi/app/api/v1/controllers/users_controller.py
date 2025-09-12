# app/api/v1/controllers/users_controller.py
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.user import User, UserCreate, UserUpdate
from app.core.database import get_db
from app.services.user_service import get_user_service, UserService
from app.core.exceptions import UserAlreadyExistsException, UserNotFoundException

controller = APIRouter()


@controller.post("/", response_model=User, status_code=201)
async def create_user(
    *, 
    db: AsyncSession = Depends(get_db),
    user_in: UserCreate,
    service: UserService = Depends(get_user_service)
):
    """
    새로운 사용자를 생성합니다.
    - **email**: 사용자 이메일 (고유해야 함)
    - **username**: 사용자 이름 (고유해야 함)
    """
    try:
        user = await service.create_user(db=db, user_in=user_in)
        return user
    except UserAlreadyExistsException as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


@controller.get("/", response_model=List[User])
async def read_users(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    service: UserService = Depends(get_user_service)
):
    """
    사용자 목록을 조회합니다.
    """
    users = await service.get_users(db, skip=skip, limit=limit)
    return users


@controller.get("/{user_id}", response_model=User)
async def read_user(
    *, 
    db: AsyncSession = Depends(get_db),
    user_id: int,
    service: UserService = Depends(get_user_service)
):
    """
    ID로 특정 사용자를 조회합니다.
    """
    try:
        user = await service.get_user_by_id(db, user_id=user_id)
        return user
    except UserNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))


@controller.put("/{user_id}", response_model=User)
async def update_user(
    *, 
    db: AsyncSession = Depends(get_db),
    user_id: int,
    user_in: UserUpdate,
    service: UserService = Depends(get_user_service)
):
    """
    사용자 정보를 수정합니다.
    """
    try:
        updated_user = await service.update_user(db=db, user_id=user_id, user_in=user_in)
        return updated_user
    except UserNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))


@controller.delete("/{user_id}", response_model=User , status_code=200)
async def delete_user(
    *, 
    db: AsyncSession = Depends(get_db),
    user_id: int,
    service: UserService = Depends(get_user_service)
):
    deleted_user = await service.remove_user(db=db, user_id=user_id)
    if not deleted_user:
        raise HTTPException(status_code=404, detail="User not found")
    return deleted_user


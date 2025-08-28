# app/api/v1/endpoints/users_router.py

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ....models.user import User
from ....schemas.user import UserCreateRequest, UserUpdateRequest, UserResponse
from ....dependencies import get_database
from ....services.user_service import UserService, get_user_service
from ....utils.response_builder import ResponseBuilder
router = APIRouter()


@router.post("/")
async def create_user(
    user_data: UserCreateRequest,
    service: UserService = Depends(get_user_service),
    db: AsyncSession = Depends(get_database)
):
    """
    새로운 사용자 생성
    """
    new_user: User = await service.create_user(user_data, db)
    return ResponseBuilder.success(
        data=new_user.dict(),
        message="사용자가 성공적으로 생성되었습니다"
    )


@router.get("/")
async def get_users(
        skip: int = 0,
        limit: int = 100,
        service: UserService = Depends(get_user_service),
        db: AsyncSession = Depends(get_database)
):
    """
    사용자 목록 조회 (예시 엔드포인트)
    """
    data = await service.get_users(skip, limit, db)
    return ResponseBuilder.success(
        data=data,
        message="사용자 목록 조회 성공"
    )


@router.get("/{user_id}")
async def get_user(
        user_id: int,
        service: UserService = Depends(get_user_service),
        db: AsyncSession = Depends(get_database)
):
    """
    특정 사용자 조회 (예시 엔드포인트)
    """
    user = await service.get_user_by_id(user_id, db)
    return ResponseBuilder.success(
        data=user.dict(),
        message="사용자 조회 성공"
    )


@router.put("/{user_id}")
async def update_user(
        user_id: int,
        user_data: UserUpdateRequest,
        service: UserService = Depends(get_user_service),
        db: AsyncSession = Depends(get_database)
):
    """
    사용자 정보 수정
    """
    user = await service.update_user(user_id, user_data, db)
    return ResponseBuilder.success(
        data=user.dict(),
        message="사용자 정보가 성공적으로 수정되었습니다"
    )


@router.delete("/{user_id}")
async def delete_user(
        user_id: int,
        service: UserService = Depends(get_user_service),
        db: AsyncSession = Depends(get_database)
):
    """
    사용자 삭제
    """
    result = await service.delete_user(user_id, db)
    return ResponseBuilder.success(
        data=result,
        message="사용자가 성공적으로 삭제되었습니다"
    )



"""
User API - 用户接口
已接入用户认证和数据隔离
"""
from typing import Optional
from fastapi import APIRouter, Query, Depends, HTTPException, status

from app.schemas import ApiResponse, FeedbackRequest
from app.services import user_service
from app.core.auth import get_current_user
from app.core.data_isolation import filter_query_history_by_user, filter_favorites_by_user
from app.models.user import User

router = APIRouter()


@router.get("/profile", response_model=ApiResponse)
async def get_user_profile(
    current_user: User = Depends(get_current_user)
):
    """
    获取当前用户信息
    """
    return ApiResponse(
        code=200,
        data={
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "department": current_user.department,
            "role": current_user.role,
            "avatar": current_user.avatar,
            "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
        },
        message="success"
    )


@router.get("/history", response_model=ApiResponse)
async def get_query_history(
    limit: Optional[int] = Query(None, ge=1, le=100),
    current_user: User = Depends(get_current_user)
):
    """
    获取当前用户的查询历史

    - 用户只能看到自己的查询历史
    """
    history = user_service.get_query_history(current_user.id, limit=limit)
    return ApiResponse(
        code=200,
        data=history,
        message="success"
    )


@router.get("/favorites", response_model=ApiResponse)
async def get_favorites(
    current_user: User = Depends(get_current_user)
):
    """
    获取当前用户的收藏列表

    - 用户只能看到自己的收藏
    """
    favorites = user_service.get_favorites(current_user.id)
    return ApiResponse(
        code=200,
        data=favorites,
        message="success"
    )


@router.post("/favorites/{document_id}", response_model=ApiResponse)
async def toggle_favorite(
    document_id: str,
    document_name: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user)
):
    """
    添加/取消收藏

    - 用户只能操作自己的收藏
    """
    result = user_service.toggle_favorite(
        document_id=document_id,
        document_name=document_name or "Unknown Document",
        user_id=current_user.id
    )

    return ApiResponse(
        code=200,
        data=result,
        message="success"
    )


@router.delete("/favorites/{favorite_id}", response_model=ApiResponse)
async def delete_favorite(
    favorite_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    删除收藏

    - 用户只能删除自己的收藏
    """
    success = user_service.remove_favorite(favorite_id, current_user.id)
    if success:
        return ApiResponse(
            code=200,
            data=None,
            message="Favorite removed successfully"
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Favorite not found"
        )

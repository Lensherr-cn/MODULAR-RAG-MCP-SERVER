"""
User API - 用户接口
"""
from typing import Optional
from fastapi import APIRouter, Query

from backend.app.schemas import ApiResponse, FeedbackRequest
from backend.app.services import user_service

router = APIRouter()


@router.get("/profile", response_model=ApiResponse)
async def get_user_profile():
    """
    获取当前用户信息
    """
    # 简化实现：返回默认用户
    user = user_service.get_user_profile("user_001")
    return ApiResponse(
        code=200,
        data=user,
        message="success"
    )


@router.get("/history", response_model=ApiResponse)
async def get_query_history(
    limit: Optional[int] = Query(None, ge=1, le=100)
):
    """
    获取查询历史
    """
    history = user_service.get_query_history("user_001", limit=limit)
    return ApiResponse(
        code=200,
        data=history,
        message="success"
    )


@router.get("/favorites", response_model=ApiResponse)
async def get_favorites():
    """
    获取收藏列表
    """
    favorites = user_service.get_favorites("user_001")
    return ApiResponse(
        code=200,
        data=favorites,
        message="success"
    )


@router.post("/favorites/{document_id}", response_model=ApiResponse)
async def toggle_favorite(
    document_id: str,
    document_name: Optional[str] = Query(None)
):
    """
    添加/取消收藏
    """
    result = user_service.toggle_favorite(
        document_id=document_id,
        document_name=document_name or "Unknown Document",
        user_id="user_001"
    )

    return ApiResponse(
        code=200,
        data=result,
        message="success"
    )


@router.delete("/favorites/{favorite_id}", response_model=ApiResponse)
async def delete_favorite(favorite_id: str):
    """
    删除收藏
    """
    success = user_service.remove_favorite(favorite_id, "user_001")
    if success:
        return ApiResponse(
            code=200,
            data=None,
            message="Favorite removed successfully"
        )
    else:
        return ApiResponse(
            code=404,
            data=None,
            message="Favorite not found"
        )

"""
Feedback API - 反馈接口
已接入用户认证和数据隔离
"""
from typing import Optional
from fastapi import APIRouter, Query, Depends, HTTPException, status

from app.schemas import ApiResponse
from app.schemas.feedback import FeedbackCreate, FeedbackListResponse, FeedbackStats
from app.services.feedback_service import feedback_service
from app.core.auth import get_current_user, require_admin
from app.core.data_isolation import filter_feedbacks_by_user
from app.models.user import User

router = APIRouter()


@router.post("", response_model=ApiResponse)
async def submit_feedback(
    feedback: FeedbackCreate,
    current_user: User = Depends(get_current_user)
):
    """
    提交反馈

    支持反馈类型：
    - `like`: 点赞/有帮助
    - `dislike`: 点踩/无帮助
    - `comment`: 文本评论/建议

    - 反馈关联当前用户
    """
    result = feedback_service.create_feedback(
        feedback.model_dump(exclude_unset=True),
        user_id=current_user.id
    )

    return ApiResponse(
        code=200,
        data=result,
        message="Feedback submitted successfully"
    )


@router.get("", response_model=ApiResponse)
async def list_feedback(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    feedback_type: Optional[str] = Query(None, description="筛选类型: like/dislike/comment"),
    current_user: User = Depends(require_admin)  # 只有管理员可以查看所有反馈
):
    """
    获取反馈列表（管理后台用）

    - 仅限管理员访问
    """
    result = feedback_service.get_feedback_list(
        page=page,
        page_size=page_size,
        feedback_type=feedback_type
    )

    return ApiResponse(
        code=200,
        data=result,
        message="success"
    )


@router.get("/my", response_model=ApiResponse)
async def get_my_feedback(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user)
):
    """
    获取当前用户的反馈列表
    """
    result = feedback_service.get_user_feedback_list(
        user_id=current_user.id,
        page=page,
        page_size=page_size
    )

    return ApiResponse(
        code=200,
        data=result,
        message="success"
    )


@router.get("/stats", response_model=ApiResponse)
async def get_feedback_stats(
    current_user: User = Depends(require_admin)  # 只有管理员可以查看统计
):
    """
    获取反馈统计

    - 仅限管理员访问
    """
    stats = feedback_service.get_feedback_stats()

    return ApiResponse(
        code=200,
        data=stats,
        message="success"
    )


@router.get("/check", response_model=ApiResponse)
async def check_feedback(
    conversation_id: Optional[str] = Query(None, description="对话ID"),
    message_id: Optional[str] = Query(None, description="消息ID"),
    current_user: User = Depends(get_current_user)
):
    """
    获取用户对特定对话/消息的反馈
    """
    feedback = feedback_service.get_user_feedback(
        user_id=current_user.id,
        conversation_id=conversation_id,
        message_id=message_id
    )

    if feedback:
        return ApiResponse(
            code=200,
            data=feedback,
            message="success"
        )
    else:
        return ApiResponse(
            code=404,
            data=None,
            message="Feedback not found"
        )

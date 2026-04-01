"""
Feedback API - 反馈接口
"""
from typing import Optional
from fastapi import APIRouter, Query

from backend.app.schemas import ApiResponse
from backend.app.schemas.feedback import FeedbackCreate, FeedbackListResponse, FeedbackStats
from backend.app.services.feedback_service import feedback_service

router = APIRouter()


@router.post("", response_model=ApiResponse)
async def submit_feedback(feedback: FeedbackCreate):
    """
    提交反馈

    支持反馈类型：
    - `like`: 点赞/有帮助
    - `dislike`: 点踩/无帮助
    - `comment`: 文本评论/建议
    """
    result = feedback_service.create_feedback(feedback.model_dump(exclude_unset=True))

    return ApiResponse(
        code=200,
        data=result,
        message="Feedback submitted successfully"
    )


@router.get("", response_model=ApiResponse)
async def list_feedback(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    feedback_type: Optional[str] = Query(None, description="筛选类型: like/dislike/comment")
):
    """
    获取反馈列表（管理后台用）
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


@router.get("/stats", response_model=ApiResponse)
async def get_feedback_stats():
    """
    获取反馈统计
    """
    stats = feedback_service.get_feedback_stats()

    return ApiResponse(
        code=200,
        data=stats,
        message="success"
    )


@router.get("/user", response_model=ApiResponse)
async def get_user_feedback(
    conversation_id: Optional[str] = Query(None, description="对话ID"),
    message_id: Optional[str] = Query(None, description="消息ID")
):
    """
    获取用户对特定对话/消息的反馈
    """
    feedback = feedback_service.get_user_feedback(
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

"""
Stats API - 统计接口
"""
from typing import Optional
from fastapi import APIRouter, Query

from backend.app.schemas import ApiResponse
from backend.app.services import stats_service

router = APIRouter()


@router.get("/overview", response_model=ApiResponse)
async def get_overview_stats():
    """
    获取首页概览统计数据
    """
    stats = stats_service.get_overview_stats()
    return ApiResponse(
        code=200,
        data=stats,
        message="success"
    )


@router.get("/hot-questions", response_model=ApiResponse)
async def get_hot_questions(
    limit: Optional[int] = Query(5, ge=1, le=20)
):
    """
    获取热门问题
    """
    questions = stats_service.get_hot_questions(limit=limit)
    return ApiResponse(
        code=200,
        data=questions,
        message="success"
    )

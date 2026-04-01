from typing import List
from pydantic import BaseModel, Field


class CategoryStat(BaseModel):
    """分类统计"""
    name: str = Field(description="分类名称")
    count: int = Field(description="文档数量")


class OverviewStats(BaseModel):
    """首页概览统计"""
    document_count: int = Field(description="文档总数")
    chunk_count: int = Field(description="知识片段总数")
    today_queries: int = Field(description="今日查询数")
    total_queries: int = Field(description="总查询数")
    active_users: int = Field(description="活跃用户数")
    categories: List[CategoryStat] = Field(description="分类统计")


class HotQuestion(BaseModel):
    """热门问题"""
    id: str = Field(description="问题ID")
    question: str = Field(description="问题内容")
    count: int = Field(description="查询次数")

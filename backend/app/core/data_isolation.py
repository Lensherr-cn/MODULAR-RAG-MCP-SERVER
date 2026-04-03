"""
Data Isolation Utilities
数据隔离工具模块 - 权限检查、查询过滤器

本模块实现基于用户的数据隔离，确保：
- 用户只能访问自己有权限的文档
- 用户数据（收藏、历史记录等）相互隔离
- 支持多级权限：public / department / private
"""
from sqlalchemy import or_, and_
from sqlalchemy.orm import Session, Query
from typing import Optional

from app.models.user import User
from app.models.document import Document


def can_access_document(document: Document, user: User) -> bool:
    """
    检查用户是否有权限访问文档

    安全原则：默认拒绝，明确允许

    Args:
        document: 文档对象
        user: 用户对象

    Returns:
        是否有权限访问
    """
    # 参数校验
    if not document or not user:
        return False

    # 管理员可以访问所有
    if user.role == "admin":
        return True

    visibility = document.visibility or "public"

    # 公共文档：所有人可访问
    if visibility == "public":
        return True

    # 私有文档：仅所有者可访问
    if visibility == "private":
        if not document.owner_id:
            return False
        return document.owner_id == user.id

    # 部门文档：同部门用户可访问
    if visibility == "department":
        if not document.department or not user.department:
            return False
        return document.department == user.department

    # 未知可见性级别：默认拒绝
    return False


def get_document_query_filter(user: User):
    """
    生成文档查询的 SQLAlchemy 过滤条件

    使用示例：
        query = db.query(Document).filter(get_document_query_filter(current_user))

    Args:
        user: 当前用户

    Returns:
        SQLAlchemy 布尔表达式
    """
    if user.role == "admin":
        # 管理员不过滤，返回恒真条件
        return Document.id.isnot(None)

    # 构建权限过滤条件
    conditions = [Document.visibility == "public"]  # 公共文档

    # 用户的私有文档
    conditions.append(Document.owner_id == user.id)

    # 同部门文档（仅当用户有所属部门时）
    if user.department:
        conditions.append(
            and_(
                Document.visibility == "department",
                Document.department == user.department
            )
        )

    return or_(*conditions)


def filter_documents_by_permission(query: Query, user: User) -> Query:
    """
    对文档查询应用权限过滤

    Args:
        query: SQLAlchemy 查询对象
        user: 当前用户

    Returns:
        应用了权限过滤的查询对象
    """
    return query.filter(get_document_query_filter(user))


def filter_query_history_by_user(query: Query, user: User) -> Query:
    """
    对查询历史应用用户隔离

    用户只能看到自己的查询历史
    """
    from app.models.user import QueryHistory
    return query.filter(QueryHistory.user_id == user.id)


def filter_favorites_by_user(query: Query, user: User) -> Query:
    """
    对收藏应用用户隔离

    用户只能看到自己的收藏
    """
    from app.models.user import Favorite
    return query.filter(Favorite.user_id == user.id)


def filter_conversations_by_user(query: Query, user: User) -> Query:
    """
    对对话应用用户隔离

    用户只能看到自己的对话
    """
    from app.models.chat import Conversation
    return query.filter(Conversation.user_id == user.id)


def filter_feedbacks_by_user(query: Query, user: User, include_all: bool = False) -> Query:
    """
    对反馈应用用户隔离

    Args:
        query: SQLAlchemy 查询对象
        user: 当前用户
        include_all: 如果为 True 且用户是管理员，返回所有反馈

    Returns:
        应用了权限过滤的查询对象
    """
    from app.models.user import Feedback
    if include_all and user.role == "admin":
        return query
    return query.filter(Feedback.user_id == user.id)


def check_document_ownership(document: Document, user: User) -> bool:
    """
    检查用户是否是文档的所有者

    用于更新、删除等需要所有权的操作

    Args:
        document: 文档对象
        user: 用户对象

    Returns:
        是否是所有者或管理员
    """
    if user.role == "admin":
        return True
    if not document.owner_id:
        return False
    return document.owner_id == user.id

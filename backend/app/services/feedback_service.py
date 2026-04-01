"""
Feedback Service - 用户反馈服务 (MySQL版本)
重构为使用SQLAlchemy ORM进行MySQL持久化
"""
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy import desc

from app.models.user import Feedback


class FeedbackService:
    """反馈服务 - MySQL版本"""

    def __init__(self):
        pass

    def _get_db(self):
        """获取数据库会话"""
        from app.core.database import SessionLocal
        return SessionLocal()

    def create_feedback(
        self,
        feedback_data: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        创建反馈

        Args:
            feedback_data: {
                "query": str,
                "answer": str,
                "feedback_type": "like" | "dislike" | "comment",
                "content": str,
                "conversation_id": str,
                "message_id": str
            }
            user_id: 用户ID（可选）

        Returns:
            创建的反馈记录
        """
        db = self._get_db()
        try:
            # 如果没有用户ID，获取默认用户
            if not user_id:
                from app.services.user_service import user_service
                user_id = user_service.get_or_create_default_user()

            # 将 feedback_type 转换为数据库格式
            fb_type = feedback_data.get("feedback_type", "comment")
            if fb_type == "like":
                db_type = "positive"
            elif fb_type == "dislike":
                db_type = "negative"
            else:
                db_type = "suggestion"

            feedback = Feedback(
                id=str(uuid.uuid4()),
                user_id=user_id,
                content=feedback_data.get("content", ""),
                feedback_type=db_type,
                query_id=feedback_data.get("conversation_id")  # 临时使用conversation_id
            )

            db.add(feedback)
            db.commit()
            db.refresh(feedback)

            return {
                "id": feedback.id,
                "query": feedback_data.get("query"),
                "answer": feedback_data.get("answer"),
                "feedback_type": fb_type,
                "content": feedback.content,
                "conversation_id": feedback_data.get("conversation_id"),
                "message_id": feedback_data.get("message_id"),
                "created_at": feedback.created_at.isoformat() if feedback.created_at else None
            }
        finally:
            db.close()

    def get_feedback_list(
        self,
        page: int = 1,
        page_size: int = 20,
        feedback_type: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取反馈列表

        Args:
            page: 页码
            page_size: 每页数量
            feedback_type: 反馈类型筛选
            user_id: 用户ID（可选，用于筛选特定用户的反馈）

        Returns:
            {
                "total": int,
                "page": int,
                "page_size": int,
                "items": List[Dict]
            }
        """
        db = self._get_db()
        try:
            query = db.query(Feedback)

            # 用户筛选
            if user_id:
                query = query.filter(Feedback.user_id == user_id)

            # 类型筛选
            if feedback_type:
                if feedback_type == "like":
                    query = query.filter(Feedback.feedback_type == "positive")
                elif feedback_type == "dislike":
                    query = query.filter(Feedback.feedback_type == "negative")
                else:
                    query = query.filter(Feedback.feedback_type == feedback_type)

            # 计算总数
            total = query.count()

            # 排序和分页
            query = query.order_by(desc(Feedback.created_at))
            query = query.offset((page - 1) * page_size).limit(page_size)

            items = query.all()

            return {
                "total": total,
                "page": page,
                "page_size": page_size,
                "items": [
                    {
                        "id": f.id,
                        "content": f.content,
                        "type": f.feedback_type,
                        "query_id": f.query_id,
                        "created_at": f.created_at.isoformat() if f.created_at else None
                    }
                    for f in items
                ]
            }
        finally:
            db.close()

    def get_feedback_stats(self) -> Dict[str, Any]:
        """获取反馈统计"""
        db = self._get_db()
        try:
            total = db.query(Feedback).count()
            like_count = db.query(Feedback).filter(Feedback.feedback_type == "positive").count()
            dislike_count = db.query(Feedback).filter(Feedback.feedback_type == "negative").count()
            comment_count = db.query(Feedback).filter(Feedback.feedback_type == "suggestion").count()

            return {
                "total_count": total,
                "like_count": like_count,
                "dislike_count": dislike_count,
                "comment_count": comment_count
            }
        finally:
            db.close()

    def get_user_feedback(
        self,
        user_id: str,
        conversation_id: Optional[str] = None,
        message_id: Optional[str] = None
    ) -> Optional[Dict]:
        """
        获取特定用户的反馈

        Args:
            user_id: 用户ID
            conversation_id: 对话ID
            message_id: 消息ID

        Returns:
            反馈记录或 None
        """
        db = self._get_db()
        try:
            query = db.query(Feedback).filter(Feedback.user_id == user_id)

            if conversation_id:
                # 临时使用 query_id 存储 conversation_id
                query = query.filter(Feedback.query_id == conversation_id)

            feedback = query.first()

            if feedback:
                return {
                    "id": feedback.id,
                    "content": feedback.content,
                    "type": feedback.feedback_type,
                    "created_at": feedback.created_at.isoformat() if feedback.created_at else None
                }
            return None
        finally:
            db.close()


# 全局反馈服务实例
feedback_service = FeedbackService()

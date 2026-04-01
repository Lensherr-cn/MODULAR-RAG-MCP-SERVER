"""
User Service - 用户服务 (MySQL版本)
重构为使用SQLAlchemy ORM进行MySQL持久化
"""
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime

from sqlalchemy import desc

from app.models.user import User, QueryHistory, Favorite, Feedback
from app.models.document import Document


class UserService:
    """用户服务 - MySQL版本"""

    def __init__(self):
        pass

    def _get_db(self):
        """获取数据库会话"""
        from app.core.database import SessionLocal
        return SessionLocal()

    def get_user_profile(self, user_id: str) -> Optional[Dict]:
        """获取用户资料"""
        db = self._get_db()
        try:
            user = db.query(User).filter(User.id == user_id, User.is_active == "Y").first()
            if not user:
                return None

            return {
                "id": user.id,
                "username": user.username,
                "department": user.department,
                "email": user.email,
                "avatar": user.avatar,
                "created_at": user.created_at.isoformat() if user.created_at else None
            }
        finally:
            db.close()

    def get_or_create_default_user(self) -> str:
        """获取或创建默认用户，返回用户ID"""
        db = self._get_db()
        try:
            user = db.query(User).filter(User.username == "admin").first()
            if user:
                return user.id

            # 创建默认用户
            user = User(
                id=str(uuid.uuid4()),
                username="admin",
                email="admin@company.com",
                department="系统管理部",
                is_active="Y"
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            return user.id
        finally:
            db.close()

    def get_query_history(
        self,
        user_id: str,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """获取查询历史"""
        db = self._get_db()
        try:
            query = db.query(QueryHistory).filter(
                QueryHistory.user_id == user_id
            ).order_by(desc(QueryHistory.created_at))

            if limit:
                query = query.limit(limit)

            history = query.all()

            return [
                {
                    "id": h.id,
                    "query": h.query,
                    "conversation_id": h.conversation_id,
                    "created_at": h.created_at.isoformat() if h.created_at else None
                }
                for h in history
            ]
        finally:
            db.close()

    def add_query_history(
        self,
        query: str,
        conversation_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict:
        """添加查询历史"""
        db = self._get_db()
        try:
            # 如果没有用户ID，使用默认用户
            if not user_id:
                user_id = self.get_or_create_default_user()

            record = QueryHistory(
                id=str(uuid.uuid4()),
                user_id=user_id,
                query=query,
                conversation_id=conversation_id
            )

            db.add(record)
            db.commit()
            db.refresh(record)

            return {
                "id": record.id,
                "query": record.query,
                "conversation_id": record.conversation_id,
                "created_at": record.created_at.isoformat() if record.created_at else None
            }
        finally:
            db.close()

    def get_favorites(self, user_id: str) -> List[Dict]:
        """获取收藏列表"""
        db = self._get_db()
        try:
            favorites = db.query(Favorite).filter(
                Favorite.user_id == user_id
            ).order_by(desc(Favorite.created_at)).all()

            result = []
            for fav in favorites:
                doc = db.query(Document).filter(Document.id == fav.document_id).first()
                result.append({
                    "id": fav.id,
                    "document_id": fav.document_id,
                    "document_name": doc.name if doc else "未知文档",
                    "created_at": fav.created_at.isoformat() if fav.created_at else None
                })

            return result
        finally:
            db.close()

    def add_favorite(
        self,
        document_id: str,
        document_name: str,
        user_id: str
    ) -> Dict:
        """添加收藏"""
        db = self._get_db()
        try:
            # 检查是否已收藏
            existing = db.query(Favorite).filter(
                Favorite.user_id == user_id,
                Favorite.document_id == document_id
            ).first()

            if existing:
                return {
                    "id": existing.id,
                    "document_id": existing.document_id,
                    "document_name": document_name,
                    "created_at": existing.created_at.isoformat() if existing.created_at else None
                }

            favorite = Favorite(
                id=str(uuid.uuid4()),
                user_id=user_id,
                document_id=document_id
            )

            db.add(favorite)
            db.commit()
            db.refresh(favorite)

            return {
                "id": favorite.id,
                "document_id": favorite.document_id,
                "document_name": document_name,
                "created_at": favorite.created_at.isoformat() if favorite.created_at else None
            }
        finally:
            db.close()

    def remove_favorite(self, favorite_id: str, user_id: str) -> bool:
        """取消收藏"""
        db = self._get_db()
        try:
            favorite = db.query(Favorite).filter(
                Favorite.id == favorite_id,
                Favorite.user_id == user_id
            ).first()

            if not favorite:
                return False

            db.delete(favorite)
            db.commit()
            return True
        finally:
            db.close()

    def toggle_favorite(
        self,
        document_id: str,
        document_name: str,
        user_id: str
    ) -> Dict:
        """切换收藏状态"""
        db = self._get_db()
        try:
            # 查找是否已收藏
            favorite = db.query(Favorite).filter(
                Favorite.user_id == user_id,
                Favorite.document_id == document_id
            ).first()

            if favorite:
                # 已收藏，取消收藏
                fav_id = favorite.id
                db.delete(favorite)
                db.commit()
                return {"id": fav_id, "favorited": False}

            # 未收藏，添加收藏
            new_fav = self.add_favorite(document_id, document_name, user_id)
            return {"id": new_fav["id"], "favorited": True}
        finally:
            db.close()

    def get_feedbacks(self, user_id: str) -> List[Dict]:
        """获取反馈列表"""
        db = self._get_db()
        try:
            feedbacks = db.query(Feedback).filter(
                Feedback.user_id == user_id
            ).order_by(desc(Feedback.created_at)).all()

            return [
                {
                    "id": f.id,
                    "content": f.content,
                    "type": f.feedback_type,
                    "query_id": f.query_id,
                    "created_at": f.created_at.isoformat() if f.created_at else None
                }
                for f in feedbacks
            ]
        finally:
            db.close()

    def submit_feedback(
        self,
        content: str,
        feedback_type: str,
        query_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict:
        """提交反馈"""
        db = self._get_db()
        try:
            # 如果没有用户ID，使用默认用户
            if not user_id:
                user_id = self.get_or_create_default_user()

            feedback = Feedback(
                id=str(uuid.uuid4()),
                user_id=user_id,
                content=content,
                feedback_type=feedback_type,
                query_id=query_id
            )

            db.add(feedback)
            db.commit()
            db.refresh(feedback)

            return {
                "id": feedback.id,
                "content": feedback.content,
                "type": feedback.feedback_type,
                "query_id": feedback.query_id,
                "created_at": feedback.created_at.isoformat() if feedback.created_at else None
            }
        finally:
            db.close()


# 全局用户服务实例
user_service = UserService()

"""
User Service - 用户服务
"""
import uuid
import json
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path


class UserService:
    """用户服务"""

    def __init__(self):
        self.data_dir = Path(__file__).resolve().parents[2] / "data"
        self.data_dir.mkdir(exist_ok=True)

        # 用户数据
        self.users_file = self.data_dir / "users.json"
        self.users: Dict[str, Dict] = {}

        # 查询历史
        self.history_file = self.data_dir / "query_history.json"
        self.history: Dict[str, List[Dict]] = {}  # user_id -> history list

        # 收藏
        self.favorites_file = self.data_dir / "favorites.json"
        self.favorites: Dict[str, List[Dict]] = {}  # user_id -> favorites list

        # 反馈
        self.feedbacks_file = self.data_dir / "feedbacks.json"
        self.feedbacks: Dict[str, List[Dict]] = {}  # user_id -> feedbacks list

        self._load_all()

    def _load_all(self):
        """加载所有数据"""
        # 加载用户
        if self.users_file.exists():
            try:
                with open(self.users_file, 'r', encoding='utf-8') as f:
                    self.users = json.load(f)
            except Exception:
                self.users = {}
        else:
            self._init_default_user()

        # 加载历史
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self.history = json.load(f)
            except Exception:
                self.history = {}

        # 加载收藏
        if self.favorites_file.exists():
            try:
                with open(self.favorites_file, 'r', encoding='utf-8') as f:
                    self.favorites = json.load(f)
            except Exception:
                self.favorites = {}

        # 加载反馈
        if self.feedbacks_file.exists():
            try:
                with open(self.feedbacks_file, 'r', encoding='utf-8') as f:
                    self.feedbacks = json.load(f)
            except Exception:
                self.feedbacks = {}

    def _init_default_user(self):
        """初始化默认用户"""
        default_user = {
            "id": "user_001",
            "username": "管理员",
            "department": "技术部",
            "email": "admin@example.com",
            "avatar": None,
            "created_at": datetime.now().isoformat()
        }
        self.users["user_001"] = default_user
        self._save_users()

    def _save_users(self):
        """保存用户数据"""
        try:
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump(self.users, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving users: {e}")

    def _save_history(self):
        """保存查询历史"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving history: {e}")

    def _save_favorites(self):
        """保存收藏"""
        try:
            with open(self.favorites_file, 'w', encoding='utf-8') as f:
                json.dump(self.favorites, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving favorites: {e}")

    def _save_feedbacks(self):
        """保存反馈"""
        try:
            with open(self.feedbacks_file, 'w', encoding='utf-8') as f:
                json.dump(self.feedbacks, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving feedbacks: {e}")

    def get_user_profile(self, user_id: str = "user_001") -> Optional[Dict]:
        """获取用户资料"""
        return self.users.get(user_id)

    def get_query_history(
        self,
        user_id: str = "user_001",
        limit: Optional[int] = None
    ) -> List[Dict]:
        """获取查询历史"""
        history = self.history.get(user_id, [])
        # 按时间倒序
        history = sorted(history, key=lambda x: x.get("created_at", ""), reverse=True)
        if limit:
            history = history[:limit]
        return history

    def add_query_history(
        self,
        query: str,
        conversation_id: Optional[str] = None,
        user_id: str = "user_001"
    ) -> Dict:
        """添加查询历史"""
        if user_id not in self.history:
            self.history[user_id] = []

        record = {
            "id": str(uuid.uuid4()),
            "query": query,
            "conversation_id": conversation_id,
            "created_at": datetime.now().isoformat()
        }

        self.history[user_id].append(record)
        self._save_history()
        return record

    def get_favorites(self, user_id: str = "user_001") -> List[Dict]:
        """获取收藏列表"""
        return self.favorites.get(user_id, [])

    def add_favorite(
        self,
        document_id: str,
        document_name: str,
        user_id: str = "user_001"
    ) -> Dict:
        """添加收藏"""
        if user_id not in self.favorites:
            self.favorites[user_id] = []

        # 检查是否已收藏
        for fav in self.favorites[user_id]:
            if fav["document_id"] == document_id:
                return fav

        favorite = {
            "id": str(uuid.uuid4()),
            "document_id": document_id,
            "document_name": document_name,
            "created_at": datetime.now().isoformat()
        }

        self.favorites[user_id].append(favorite)
        self._save_favorites()
        return favorite

    def remove_favorite(self, favorite_id: str, user_id: str = "user_001") -> bool:
        """取消收藏"""
        if user_id not in self.favorites:
            return False

        favorites = self.favorites[user_id]
        for i, fav in enumerate(favorites):
            if fav["id"] == favorite_id:
                favorites.pop(i)
                self._save_favorites()
                return True
        return False

    def toggle_favorite(
        self,
        document_id: str,
        document_name: str,
        user_id: str = "user_001"
    ) -> Dict:
        """切换收藏状态"""
        if user_id not in self.favorites:
            self.favorites[user_id] = []

        favorites = self.favorites[user_id]
        for i, fav in enumerate(favorites):
            if fav["document_id"] == document_id:
                # 已收藏，取消收藏
                favorites.pop(i)
                self._save_favorites()
                return {"id": fav["id"], "favorited": False}

        # 未收藏，添加收藏
        favorite = self.add_favorite(document_id, document_name, user_id)
        return {"id": favorite["id"], "favorited": True}

    def get_feedbacks(self, user_id: str = "user_001") -> List[Dict]:
        """获取反馈列表"""
        return self.feedbacks.get(user_id, [])

    def submit_feedback(
        self,
        content: str,
        feedback_type: str,
        query_id: Optional[str] = None,
        user_id: str = "user_001"
    ) -> Dict:
        """提交反馈"""
        if user_id not in self.feedbacks:
            self.feedbacks[user_id] = []

        feedback = {
            "id": str(uuid.uuid4()),
            "content": content,
            "type": feedback_type,
            "query_id": query_id,
            "created_at": datetime.now().isoformat()
        }

        self.feedbacks[user_id].append(feedback)
        self._save_feedbacks()
        return feedback


# 全局用户服务实例
user_service = UserService()

"""
Feedback Service - 用户反馈服务
"""
import uuid
import json
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path


class FeedbackService:
    """反馈服务"""

    def __init__(self):
        self.data_dir = Path(__file__).resolve().parents[2] / "data"
        self.data_dir.mkdir(exist_ok=True)
        self.feedback_file = self.data_dir / "feedback.json"
        self.feedback_list: List[Dict] = []
        self._load_feedback()

    def _load_feedback(self):
        """加载反馈数据"""
        if self.feedback_file.exists():
            try:
                with open(self.feedback_file, 'r', encoding='utf-8') as f:
                    self.feedback_list = json.load(f)
            except Exception:
                self.feedback_list = []
        else:
            self.feedback_list = []

    def _save_feedback(self):
        """保存反馈数据"""
        try:
            with open(self.feedback_file, 'w', encoding='utf-8') as f:
                json.dump(self.feedback_list, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving feedback: {e}")

    def create_feedback(self, feedback_data: Dict[str, Any]) -> Dict[str, Any]:
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

        Returns:
            创建的反馈记录
        """
        feedback_id = str(uuid.uuid4())
        now = datetime.now().isoformat()

        feedback = {
            "id": feedback_id,
            "query": feedback_data.get("query"),
            "answer": feedback_data.get("answer"),
            "feedback_type": feedback_data.get("feedback_type", "comment"),
            "content": feedback_data.get("content"),
            "conversation_id": feedback_data.get("conversation_id"),
            "message_id": feedback_data.get("message_id"),
            "created_at": now
        }

        self.feedback_list.append(feedback)
        self._save_feedback()

        return feedback

    def get_feedback_list(
        self,
        page: int = 1,
        page_size: int = 20,
        feedback_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取反馈列表

        Args:
            page: 页码
            page_size: 每页数量
            feedback_type: 反馈类型筛选

        Returns:
            {
                "total": int,
                "page": int,
                "page_size": int,
                "items": List[Dict]
            }
        """
        items = self.feedback_list.copy()

        # 类型筛选
        if feedback_type:
            items = [f for f in items if f.get("feedback_type") == feedback_type]

        # 按时间倒序
        items.sort(key=lambda x: x.get("created_at", ""), reverse=True)

        # 分页
        total = len(items)
        start = (page - 1) * page_size
        end = start + page_size
        items = items[start:end]

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": items
        }

    def get_feedback_stats(self) -> Dict[str, Any]:
        """获取反馈统计"""
        total = len(self.feedback_list)
        like_count = sum(1 for f in self.feedback_list if f.get("feedback_type") == "like")
        dislike_count = sum(1 for f in self.feedback_list if f.get("feedback_type") == "dislike")
        comment_count = sum(1 for f in self.feedback_list if f.get("feedback_type") == "comment")

        return {
            "total_count": total,
            "like_count": like_count,
            "dislike_count": dislike_count,
            "comment_count": comment_count
        }

    def get_user_feedback(
        self,
        conversation_id: Optional[str] = None,
        message_id: Optional[str] = None
    ) -> Optional[Dict]:
        """
        获取特定对话/消息的反馈

        Args:
            conversation_id: 对话ID
            message_id: 消息ID

        Returns:
            反馈记录或 None
        """
        for feedback in self.feedback_list:
            if conversation_id and feedback.get("conversation_id") == conversation_id:
                return feedback
            if message_id and feedback.get("message_id") == message_id:
                return feedback
        return None


# 全局反馈服务实例
feedback_service = FeedbackService()

"""
Stats Service - 统计服务 (MySQL版本)
重构为使用SQLAlchemy ORM进行MySQL持久化
"""
from typing import List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import func

from app.services.document_service import document_service
from app.models.user import QueryHistory
from app.models.document import Document


class StatsService:
    """统计服务 - MySQL版本"""

    # 热门问题（简化实现，实际应基于真实查询统计）
    HOT_QUESTIONS = [
        {"id": "q1", "question": "报销流程是什么？", "count": 128},
        {"id": "q2", "question": "如何申请年假？", "count": 96},
        {"id": "q3", "question": "公司福利有哪些？", "count": 84},
        {"id": "q4", "question": "考勤制度是怎样的？", "count": 72},
        {"id": "q5", "question": "培训资料在哪里？", "count": 65},
        {"id": "q6", "question": "绩效考核标准是什么？", "count": 58},
        {"id": "q7", "question": "加班怎么计算？", "count": 52},
        {"id": "q8", "question": "离职流程是什么？", "count": 48},
    ]

    def __init__(self):
        pass

    def _get_db(self):
        """获取数据库会话"""
        from backend.app.core.database import SessionLocal
        return SessionLocal()

    def record_query(self, user_id: str, query: str, conversation_id: str = None):
        """记录一次查询到历史表"""
        from app.services.user_service import user_service
        user_service.add_query_history(
            query=query,
            conversation_id=conversation_id,
            user_id=user_id
        )

    def get_overview_stats(self) -> Dict[str, Any]:
        """获取首页概览统计"""
        db = self._get_db()
        try:
            # 文档统计
            doc_stats = document_service.get_stats()

            # 今日查询数
            today = datetime.now().strftime("%Y-%m-%d")
            today_start = datetime.strptime(today, "%Y-%m-%d")
            today_end = today_start + timedelta(days=1)

            today_queries = db.query(QueryHistory).filter(
                QueryHistory.created_at >= today_start,
                QueryHistory.created_at < today_end
            ).count()

            # 总查询数
            total_queries = db.query(QueryHistory).count()

            # 如果没有真实数据，使用示例数据
            if today_queries == 0 and total_queries == 0:
                today_queries = 42
                total_queries = 1250

            # 活跃用户（简化实现，实际应基于活跃会话统计）
            active_users = 38

            return {
                "document_count": doc_stats["document_count"],
                "chunk_count": doc_stats["chunk_count"],
                "today_queries": today_queries,
                "total_queries": total_queries,
                "active_users": active_users,
                "categories": doc_stats["categories"]
            }
        finally:
            db.close()

    def get_hot_questions(self, limit: int = 5) -> List[Dict[str, Any]]:
        """获取热门问题"""
        # 实际应用中应该从查询历史统计得出
        return self.HOT_QUESTIONS[:limit]


# 全局统计服务实例
stats_service = StatsService()

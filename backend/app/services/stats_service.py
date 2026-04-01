"""
Stats Service - 统计服务
"""
import json
from typing import List, Dict, Any
from datetime import datetime, timedelta
from pathlib import Path

from app.services.document_service import document_service
from app.services.user_service import user_service


class StatsService:
    """统计服务"""

    def __init__(self):
        self.data_dir = Path(__file__).resolve().parents[2] / "data"
        self.data_dir.mkdir(exist_ok=True)

        # 查询统计
        self.query_stats_file = self.data_dir / "query_stats.json"
        self.query_stats: Dict[str, Any] = {
            "total_queries": 0,
            "daily_queries": {}  # date -> count
        }
        self._load_stats()

        # 热门问题（简化实现，实际应基于真实查询统计）
        self.hot_questions = [
            {"id": "q1", "question": "报销流程是什么？", "count": 128},
            {"id": "q2", "question": "如何申请年假？", "count": 96},
            {"id": "q3", "question": "公司福利有哪些？", "count": 84},
            {"id": "q4", "question": "考勤制度是怎样的？", "count": 72},
            {"id": "q5", "question": "培训资料在哪里？", "count": 65},
            {"id": "q6", "question": "绩效考核标准是什么？", "count": 58},
            {"id": "q7", "question": "加班怎么计算？", "count": 52},
            {"id": "q8", "question": "离职流程是什么？", "count": 48},
        ]

    def _load_stats(self):
        """加载统计数据"""
        if self.query_stats_file.exists():
            try:
                with open(self.query_stats_file, 'r', encoding='utf-8') as f:
                    self.query_stats = json.load(f)
            except Exception:
                pass

    def _save_stats(self):
        """保存统计数据"""
        try:
            with open(self.query_stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.query_stats, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving stats: {e}")

    def record_query(self):
        """记录一次查询"""
        self.query_stats["total_queries"] += 1

        today = datetime.now().strftime("%Y-%m-%d")
        self.query_stats["daily_queries"][today] = \
            self.query_stats["daily_queries"].get(today, 0) + 1

        self._save_stats()

    def get_overview_stats(self) -> Dict[str, Any]:
        """获取首页概览统计"""
        # 文档统计
        doc_stats = document_service.get_stats()

        # 今日查询数
        today = datetime.now().strftime("%Y-%m-%d")
        today_queries = self.query_stats["daily_queries"].get(today, 0)

        # 如果没有真实数据，返回示例数据
        if today_queries == 0 and self.query_stats["total_queries"] == 0:
            today_queries = 42
            total_queries = 1250
        else:
            total_queries = self.query_stats["total_queries"]

        # 活跃用户（简化实现）
        active_users = 38

        return {
            "document_count": doc_stats["document_count"],
            "chunk_count": doc_stats["chunk_count"],
            "today_queries": today_queries,
            "total_queries": total_queries,
            "active_users": active_users,
            "categories": doc_stats["categories"]
        }

    def get_hot_questions(self, limit: int = 5) -> List[Dict[str, Any]]:
        """获取热门问题"""
        return self.hot_questions[:limit]


# 全局统计服务实例
stats_service = StatsService()

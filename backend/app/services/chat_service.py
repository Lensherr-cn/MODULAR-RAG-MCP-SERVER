"""
Chat Service - 问答服务
"""
import uuid
import json
from typing import List, Optional, Dict, Any, AsyncGenerator
from datetime import datetime
from pathlib import Path

from app.services.rag_service import rag_service


class ChatService:
    """聊天服务"""

    def __init__(self):
        self.conversations: Dict[str, Dict] = {}  # 内存存储，实际应用应使用数据库
        self.data_dir = Path(__file__).resolve().parents[2] / "data"
        self.data_dir.mkdir(exist_ok=True)
        self._load_conversations()

    def _load_conversations(self):
        """加载对话历史"""
        conversations_file = self.data_dir / "conversations.json"
        if conversations_file.exists():
            try:
                with open(conversations_file, 'r', encoding='utf-8') as f:
                    self.conversations = json.load(f)
            except Exception:
                self.conversations = {}

    def _save_conversations(self):
        """保存对话历史"""
        conversations_file = self.data_dir / "conversations.json"
        try:
            with open(conversations_file, 'w', encoding='utf-8') as f:
                json.dump(self.conversations, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving conversations: {e}")

    def get_or_create_conversation(self, conversation_id: Optional[str] = None) -> str:
        """获取或创建对话"""
        if conversation_id and conversation_id in self.conversations:
            return conversation_id

        new_id = str(uuid.uuid4())
        self.conversations[new_id] = {
            "id": new_id,
            "messages": [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        self._save_conversations()
        return new_id

    def get_conversation_history(self, conversation_id: str) -> List[Dict]:
        """获取对话历史"""
        if conversation_id in self.conversations:
            return self.conversations[conversation_id].get("messages", [])
        return []

    async def chat(
        self,
        query: str,
        conversation_id: Optional[str] = None,
        collection: str = "default"
    ) -> Dict[str, Any]:
        """
        执行问答

        Returns:
            {
                "answer": str,
                "sources": List[Dict],
                "related_questions": List[str],
                "conversation_id": str
            }
        """
        # 获取或创建对话
        conv_id = self.get_or_create_conversation(conversation_id)

        # 检索相关文档
        search_results = await rag_service.search(query, collection)

        # 构建上下文
        context = []
        sources = []
        for result in search_results[:5]:  # 取前5个结果
            context.append(result)
            sources.append({
                "document_id": result.get("document_id", ""),
                "document_name": result.get("document_name", "Unknown"),
                "chunk_id": result.get("chunk_id", ""),
                "content": result.get("content", "")[:500],  # 截取前500字符
                "page": result.get("page"),
                "score": result.get("score", 0.0)
            })

        # 获取对话历史
        history = self.get_conversation_history(conv_id)

        # 生成回答（简化实现）
        if context:
            answer = f"根据相关文档，我为您找到以下信息：\n\n"
            for i, ctx in enumerate(context[:3], 1):
                answer += f"{i}. {ctx.get('content', '')[:300]}...\n\n"
            answer += "如需更详细的解答，请告诉我具体想了解哪方面内容。"
        else:
            answer = "抱歉，我暂时没有找到与您问题相关的文档内容。您可以尝试：\n\n1. 使用不同的关键词重新提问\n2. 检查文档是否已上传到知识库\n3. 联系管理员添加相关文档"
            sources = []

        # 生成相关问题
        related_questions = self._generate_related_questions(query, answer)

        # 保存消息到对话历史
        timestamp = datetime.now().isoformat()
        self.conversations[conv_id]["messages"].append({
            "id": str(uuid.uuid4()),
            "role": "user",
            "content": query,
            "created_at": timestamp
        })
        self.conversations[conv_id]["messages"].append({
            "id": str(uuid.uuid4()),
            "role": "assistant",
            "content": answer,
            "sources": sources,
            "created_at": timestamp
        })
        self.conversations[conv_id]["updated_at"] = timestamp
        self._save_conversations()

        return {
            "answer": answer,
            "sources": sources,
            "related_questions": related_questions,
            "conversation_id": conv_id
        }

    async def chat_stream(
        self,
        query: str,
        conversation_id: Optional[str] = None,
        collection: str = "default"
    ) -> AsyncGenerator[str, None]:
        """
        流式问答

        Yields:
            SSE格式的数据行
        """
        # 获取或创建对话
        conv_id = self.get_or_create_conversation(conversation_id)

        # 检索相关文档
        search_results = await rag_service.search(query, collection)

        # 构建回答
        if search_results:
            answer_parts = [
                "根据相关文档，",
                "我为您找到",
                "以下信息：",
                "\n\n"
            ]
            for i, result in enumerate(search_results[:3], 1):
                content = result.get('content', '')[:200]
                answer_parts.append(f"{i}. {content}...\n\n")
            answer_parts.append("如需更详细的解答，请告诉我具体想了解哪方面内容。")
        else:
            answer_parts = [
                "抱歉，",
                "我暂时没有找到",
                "与您问题相关的",
                "文档内容。",
                "\n\n",
                "您可以尝试使用",
                "不同的关键词",
                "重新提问。"
            ]

        # 构建sources
        sources = []
        for result in search_results[:5]:
            sources.append({
                "document_id": result.get("document_id", ""),
                "document_name": result.get("document_name", "Unknown"),
                "chunk_id": result.get("chunk_id", ""),
                "content": result.get("content", "")[:500],
                "page": result.get("page"),
                "score": result.get("score", 0.0)
            })

        # 流式返回
        full_answer = ""
        for part in answer_parts:
            full_answer += part
            yield f'data: {json.dumps({"type": "token", "content": part}, ensure_ascii=False)}\n\n'

        # 返回sources
        if sources:
            yield f'data: {json.dumps({"type": "sources", "sources": sources}, ensure_ascii=False)}\n\n'

        # 返回相关问题
        related = self._generate_related_questions(query, full_answer)
        if related:
            yield f'data: {json.dumps({"type": "related_questions", "related_questions": related}, ensure_ascii=False)}\n\n'

        # 返回conversation_id和结束标记
        yield f'data: {json.dumps({"type": "done", "conversation_id": conv_id}, ensure_ascii=False)}\n\n'

        # 保存到历史
        timestamp = datetime.now().isoformat()
        self.conversations[conv_id]["messages"].append({
            "id": str(uuid.uuid4()),
            "role": "user",
            "content": query,
            "created_at": timestamp
        })
        self.conversations[conv_id]["messages"].append({
            "id": str(uuid.uuid4()),
            "role": "assistant",
            "content": full_answer,
            "sources": sources,
            "created_at": timestamp
        })
        self.conversations[conv_id]["updated_at"] = timestamp
        self._save_conversations()

    def _generate_related_questions(self, query: str, answer: str) -> List[str]:
        """生成相关问题"""
        # 简化实现，返回固定模板
        templates = [
            "{topic}的具体流程是什么？",
            "如何申请{topic}？",
            "{topic}有哪些注意事项？",
            "{topic}的截止时间是什么时候？"
        ]

        # 提取关键词（简化处理）
        keywords = ["报销", "年假", "福利", "培训", "考勤", "绩效"]
        topic = "相关事项"
        for kw in keywords:
            if kw in query:
                topic = kw
                break

        import random
        random.seed(hash(query))
        selected = random.sample(templates, min(3, len(templates)))
        return [t.format(topic=topic) for t in selected]


# 全局聊天服务实例
chat_service = ChatService()

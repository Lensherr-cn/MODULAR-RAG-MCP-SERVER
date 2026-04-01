"""
Chat Service - 问答服务 (MySQL版本)
重构为使用SQLAlchemy ORM进行MySQL持久化
"""
import uuid
import json
from typing import List, Optional, Dict, Any, AsyncGenerator
from datetime import datetime

from sqlalchemy import desc

from app.models.chat import Conversation, ChatMessage
from app.models.user import User
from app.services.rag_service import rag_service
from app.services.user_service import user_service


class ChatService:
    """聊天服务 - MySQL版本"""

    def __init__(self):
        pass

    def _get_db(self):
        """获取数据库会话"""
        from backend.app.core.database import SessionLocal
        return SessionLocal()

    def get_or_create_conversation(
        self,
        conversation_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> str:
        """获取或创建对话"""
        db = self._get_db()
        try:
            # 如果提供了conversation_id，检查是否存在
            if conversation_id:
                conv = db.query(Conversation).filter(
                    Conversation.id == conversation_id,
                    Conversation.is_active == "Y"
                ).first()
                if conv:
                    return conversation_id

            # 如果没有user_id，获取默认用户
            if not user_id:
                from app.services.user_service import user_service
                user_id = user_service.get_or_create_default_user()

            # 创建新对话
            new_id = str(uuid.uuid4())
            conv = Conversation(
                id=new_id,
                user_id=user_id,
                title="新对话",  # 可以根据第一条消息自动生成
                collection="default",
                is_active="Y"
            )

            db.add(conv)
            db.commit()
            db.refresh(conv)

            return new_id
        finally:
            db.close()

    def get_conversation_history(self, conversation_id: str) -> List[Dict]:
        """获取对话历史"""
        db = self._get_db()
        try:
            messages = db.query(ChatMessage).filter(
                ChatMessage.conversation_id == conversation_id
            ).order_by(ChatMessage.message_index).all()

            return [
                {
                    "id": msg.id,
                    "role": msg.role,
                    "content": msg.content,
                    "sources": json.loads(msg.sources_json) if msg.sources_json else None,
                    "created_at": msg.created_at.isoformat() if msg.created_at else None
                }
                for msg in messages
            ]
        finally:
            db.close()

    async def chat(
        self,
        query: str,
        conversation_id: Optional[str] = None,
        collection: str = "default",
        user_id: Optional[str] = None
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
        db = self._get_db()
        try:
            # 获取或创建对话
            conv_id = self.get_or_create_conversation(conversation_id, user_id)

            # 获取当前消息序号
            last_msg = db.query(ChatMessage).filter(
                ChatMessage.conversation_id == conv_id
            ).order_by(desc(ChatMessage.message_index)).first()

            msg_index = (last_msg.message_index + 1) if last_msg else 0

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

            # 保存用户消息
            user_msg = ChatMessage(
                id=str(uuid.uuid4()),
                conversation_id=conv_id,
                role="user",
                content=query,
                message_index=msg_index
            )
            db.add(user_msg)

            # 保存助手消息
            assistant_msg = ChatMessage(
                id=str(uuid.uuid4()),
                conversation_id=conv_id,
                role="assistant",
                content=answer,
                message_index=msg_index + 1,
                sources_json=json.dumps(sources) if sources else None
            )
            db.add(assistant_msg)

            # 更新对话消息数
            conv = db.query(Conversation).filter(Conversation.id == conv_id).first()
            if conv:
                conv.message_count = db.query(ChatMessage).filter(
                    ChatMessage.conversation_id == conv_id
                ).count() + 2  # +2 因为上面刚添加了两条

                # 如果是第一条消息，更新对话标题
                if msg_index == 0:
                    conv.title = query[:50] + "..." if len(query) > 50 else query

            db.commit()

            return {
                "answer": answer,
                "sources": sources,
                "related_questions": related_questions,
                "conversation_id": conv_id
            }
        finally:
            db.close()

    async def chat_stream(
        self,
        query: str,
        conversation_id: Optional[str] = None,
        collection: str = "default",
        user_id: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        流式问答

        Yields:
            SSE格式的数据行
        """
        db = self._get_db()
        try:
            # 获取或创建对话
            conv_id = self.get_or_create_conversation(conversation_id, user_id)

            # 获取当前消息序号
            last_msg = db.query(ChatMessage).filter(
                ChatMessage.conversation_id == conv_id
            ).order_by(desc(ChatMessage.message_index)).first()

            msg_index = (last_msg.message_index + 1) if last_msg else 0

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

            # 保存用户消息
            user_msg = ChatMessage(
                id=str(uuid.uuid4()),
                conversation_id=conv_id,
                role="user",
                content=query,
                message_index=msg_index
            )
            db.add(user_msg)

            # 保存助手消息
            assistant_msg = ChatMessage(
                id=str(uuid.uuid4()),
                conversation_id=conv_id,
                role="assistant",
                content=full_answer,
                message_index=msg_index + 1,
                sources_json=json.dumps(sources) if sources else None
            )
            db.add(assistant_msg)

            # 更新对话
            conv = db.query(Conversation).filter(Conversation.id == conv_id).first()
            if conv:
                conv.message_count = db.query(ChatMessage).filter(
                    ChatMessage.conversation_id == conv_id
                ).count() + 2

                if msg_index == 0:
                    conv.title = query[:50] + "..." if len(query) > 50 else query

            db.commit()
        finally:
            db.close()

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

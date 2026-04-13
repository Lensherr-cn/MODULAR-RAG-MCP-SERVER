"""
Chat Service - 问答服务 (MySQL版本)
重构为使用SQLAlchemy ORM进行MySQL持久化
集成了完整的RAG流程：检索 -> 生成回答
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
        from app.core.database import SessionLocal
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
                title="新对话",
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
        执行问答 - 完整RAG流程

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

            # 获取对话历史（用于上下文理解）
            history = self.get_conversation_history(conv_id)

            # 步骤1：检索相关文档
            print(f"[ChatService] Searching for: {query[:50]}...")
            search_results = await rag_service.search(query, collection, top_k=10)
            print(f"[ChatService] Found {len(search_results)} results")

            # 步骤2：生成回答
            if search_results:
                # 按rerank_score重新排序（如果存在该字段）
                if any("rerank_score" in r for r in search_results):
                    search_results.sort(key=lambda x: x.get("rerank_score", 0.0), reverse=True)
                
                result = await rag_service.generate_answer(
                    query=query,
                    context=search_results,
                    conversation_history=history[-6:] if len(history) > 0 else None
                )
                answer = result["answer"]
                sources = result["sources"]
                related_questions = result["related_questions"]
            else:
                # 没有检索到结果时的友好回复
                answer = """抱歉，我暂时没有找到与您问题相关的文档内容。

您可以尝试：
1. 使用不同的关键词重新提问
2. 检查文档是否已上传到知识库
3. 联系管理员添加相关文档

如果您有紧急问题，建议直接联系相关部门咨询。"""
                sources = []
                related_questions = [
                    "如何上传文档到知识库？",
                    "支持哪些类型的文档？",
                    "如何联系管理员？"
                ]

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

            # 更新对话消息数和标题
            conv = db.query(Conversation).filter(Conversation.id == conv_id).first()
            if conv:
                conv.message_count = db.query(ChatMessage).filter(
                    ChatMessage.conversation_id == conv_id
                ).count()

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
        流式问答 - 完整RAG流程

        Yields:
            SSE格式的数据行
        """
        db = self._get_db()
        full_answer = ""
        sources = []
        conv_id = None

        try:
            # 获取或创建对话
            conv_id = self.get_or_create_conversation(conversation_id, user_id)

            # 获取当前消息序号
            last_msg = db.query(ChatMessage).filter(
                ChatMessage.conversation_id == conv_id
            ).order_by(desc(ChatMessage.message_index)).first()

            msg_index = (last_msg.message_index + 1) if last_msg else 0

            # 获取对话历史
            history = self.get_conversation_history(conv_id)

            # 步骤1：检索相关文档
            print(f"[ChatService] Searching for: {query[:50]}...")
            search_results = await rag_service.search(query, top_k=10)
            print(f"[ChatService] Found {len(search_results)} results")

            # 步骤2：流式生成回答
            if search_results:
                # 按rerank_score重新排序（如果存在该字段）
                if any("rerank_score" in r for r in search_results):
                    search_results.sort(key=lambda x: x.get("rerank_score", 0.0), reverse=True)
                
                async for line in rag_service.generate_answer_stream(
                    query=query,
                    context=search_results,
                    conversation_history=history[-6:] if len(history) > 0 else None
                ):
                    # 解析SSE数据，收集完整回答
                    if line.startswith("data: "):
                        try:
                            data = json.loads(line[6:])
                            if data.get("type") == "token":
                                full_answer += data.get("content", "")
                            elif data.get("type") == "sources":
                                sources = data.get("sources", [])
                        except:
                            pass
                    yield line
            else:
                # 没有检索到结果时的友好回复
                no_result_msg = """抱歉，我暂时没有找到与您问题相关的文档内容。

您可以尝试：
1. 使用不同的关键词重新提问
2. 检查文档是否已上传到知识库
3. 联系管理员添加相关文档"""

                sources = []
                yield f'data: {json.dumps({"type": "sources", "sources": sources}, ensure_ascii=False)}\n\n'

                # 流式返回消息
                for chunk in no_result_msg.split("\n"):
                    newline = "\n"
                    full_answer += chunk + newline
                    content_with_newline = chunk + newline
                    yield f'data: {json.dumps({"type": "token", "content": content_with_newline}, ensure_ascii=False)}\n\n'

                # 返回相关问题
                related = [
                    "如何上传文档到知识库？",
                    "支持哪些类型的文档？",
                    "如何联系管理员？"
                ]
                yield f'data: {json.dumps({"type": "related_questions", "related_questions": related}, ensure_ascii=False)}\n\n'
                yield f'data: {json.dumps({"type": "done"}, ensure_ascii=False)}\n\n'

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
                content=full_answer.strip(),
                message_index=msg_index + 1,
                sources_json=json.dumps(sources) if sources else None
            )
            db.add(assistant_msg)

            # 更新对话
            conv = db.query(Conversation).filter(Conversation.id == conv_id).first()
            if conv:
                conv.message_count = db.query(ChatMessage).filter(
                    ChatMessage.conversation_id == conv_id
                ).count()

                if msg_index == 0:
                    conv.title = query[:50] + "..." if len(query) > 50 else query

            db.commit()

        except Exception as e:
            print(f"[ChatService] Stream error: {e}")
            import traceback
            traceback.print_exc()

            # 返回错误信息
            error_msg = "抱歉，处理您的请求时出现错误，请稍后重试。"
            yield f'data: {json.dumps({"type": "token", "content": error_msg}, ensure_ascii=False)}\n\n'
            yield f'data: {json.dumps({"type": "done"}, ensure_ascii=False)}\n\n'

            # 即使出错也要保存用户消息
            if conv_id:
                try:
                    user_msg = ChatMessage(
                        id=str(uuid.uuid4()),
                        conversation_id=conv_id,
                        role="user",
                        content=query,
                        message_index=0
                    )
                    db.add(user_msg)
                    db.commit()
                except:
                    pass
        finally:
            db.close()

    def _generate_related_questions(self, query: str, answer: str) -> List[str]:
        """生成相关问题（备用方法）"""
        # 实际由rag_service.generate_related_questions处理
        return rag_service.generate_related_questions(query, answer)


# 全局聊天服务实例
chat_service = ChatService()

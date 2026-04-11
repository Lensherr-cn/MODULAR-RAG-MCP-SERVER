"""
Chat API - 问答接口
已接入用户认证和数据隔离
"""
from typing import Optional
from fastapi import APIRouter, Query, Depends, Request
from fastapi.responses import StreamingResponse, JSONResponse

from app.schemas import ApiResponse, ChatRequest, ChatResponse
from app.schemas.chat import ChatHistoryResponse
from app.services import chat_service, stats_service
from app.core.auth import get_current_user
from app.core.data_isolation import filter_conversations_by_user
from app.models.user import User

router = APIRouter()


@router.post("", response_model=ApiResponse)
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user)
):
    """
    智能问答（非流式）

    - 记录查询历史关联当前用户
    """
    # 记录查询统计
    stats_service.record_query(
        user_id=current_user.id,
        query=request.query,
        conversation_id=request.conversation_id
    )

    # 执行问答
    result = await chat_service.chat(
        query=request.query,
        conversation_id=request.conversation_id,
        collection=request.collection or "knowledge-hub",
        user_id=current_user.id
    )

    return ApiResponse(
        code=200,
        data=result,
        message="success"
    )


@router.get("/stream")
async def chat_stream(
    query: str,
    conversation_id: Optional[str] = Query(None),
    collection: str = Query("knowledge-hub"),
    current_user: User = Depends(get_current_user)
):
    """
    流式问答（SSE）

    使用 EventSource 接收流式响应
    """
    # 记录查询统计
    stats_service.record_query(
        user_id=current_user.id,
        query=query,
        conversation_id=conversation_id
    )

    async def event_generator():
        async for line in chat_service.chat_stream(
            query=query,
            conversation_id=conversation_id,
            collection=collection,
            user_id=current_user.id
        ):
            yield line

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/debug")
async def chat_debug(request: Request):
    """
    调试端点 - 查看请求头信息
    """
    headers = dict(request.headers)
    # 隐藏敏感信息
    if "authorization" in headers:
        auth = headers["authorization"]
        headers["authorization"] = auth[:20] + "..." if len(auth) > 20 else auth
    if "cookie" in headers:
        headers["cookie"] = "[hidden]"

    return ApiResponse(
        code=200,
        data={
            "headers": headers,
            "cookies": list(request.cookies.keys()),
            "client": str(request.client) if request.client else None,
        },
        message="debug info"
    )


@router.get("/recent", response_model=ApiResponse)
async def get_recent_conversations(
    current_user: User = Depends(get_current_user)
):
    """
    获取最近 5 轮对话（用于页面初始加载）

    返回最近更新过的 5 个对话及其消息，按 updated_at 降序排列
    """
    from sqlalchemy import desc
    from app.core.database import SessionLocal
    from app.models.chat import Conversation, ChatMessage
    import json

    db = SessionLocal()
    try:
        # 获取当前用户最近更新的 5 个对话（检查实际有消息的）
        from sqlalchemy import exists
        query = db.query(Conversation).filter(
            Conversation.is_active == "Y",
            Conversation.user_id == current_user.id,
            exists().where(ChatMessage.conversation_id == Conversation.id)
        ).order_by(desc(Conversation.updated_at)).limit(5)

        conversations = query.all()

        result = []
        for conv in conversations:
            # 获取该对话的所有消息（按 message_index 排序）
            messages = db.query(ChatMessage).filter(
                ChatMessage.conversation_id == conv.id
            ).order_by(ChatMessage.message_index).all()

            message_list = [
                {
                    "id": msg.id,
                    "role": msg.role,
                    "content": msg.content,
                    "sources": json.loads(msg.sources_json) if msg.sources_json else None,
                    "created_at": msg.created_at.isoformat() if msg.created_at else None
                }
                for msg in messages
            ]

            result.append({
                "id": conv.id,
                "title": conv.title,
                "message_count": conv.message_count,
                "created_at": conv.created_at.isoformat() if conv.created_at else None,
                "updated_at": conv.updated_at.isoformat() if conv.updated_at else None,
                "messages": message_list
            })

        return ApiResponse(
            code=200,
            data={
                "conversations": result,
                "total": len(result)
            },
            message="success"
        )
    finally:
        db.close()


@router.get("/history", response_model=ApiResponse)
async def get_chat_history(
    conversation_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user)
):
    """
    获取对话历史

    - 用户只能看到自己的对话
    """
    if conversation_id:
        # 验证对话属于当前用户
        from app.core.database import SessionLocal
        from app.models.chat import Conversation

        db = SessionLocal()
        try:
            conv = db.query(Conversation).filter(
                Conversation.id == conversation_id
            ).first()

            if not conv or conv.user_id != current_user.id:
                return ApiResponse(
                    code=404,
                    data=None,
                    message="Conversation not found"
                )
        finally:
            db.close()

        messages = chat_service.get_conversation_history(conversation_id)
        return ApiResponse(
            code=200,
            data={
                "conversation_id": conversation_id,
                "messages": messages
            },
            message="success"
        )
    else:
        # 从数据库获取当前用户的所有对话列表
        from sqlalchemy import desc
        from app.core.database import SessionLocal
        from app.models.chat import Conversation

        db = SessionLocal()
        try:
            query = db.query(Conversation).filter(
                Conversation.is_active == "Y"
            )
            # 数据隔离：只查询当前用户的对话
            query = filter_conversations_by_user(query, current_user)

            conversations_db = query.order_by(desc(Conversation.updated_at)).all()

            conversations = []
            for conv in conversations_db:
                conversations.append({
                    "id": conv.id,
                    "title": conv.title,
                    "created_at": conv.created_at.isoformat() if conv.created_at else None,
                    "updated_at": conv.updated_at.isoformat() if conv.updated_at else None,
                    "message_count": conv.message_count
                })

            return ApiResponse(
                code=200,
                data={"conversations": conversations},
                message="success"
            )
        finally:
            db.close()

"""
Chat API - 问答接口
"""
from typing import Optional
from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from app.schemas import ApiResponse, ChatRequest, ChatResponse
from app.schemas.chat import ChatHistoryResponse
from app.services import chat_service, stats_service

router = APIRouter()


@router.post("", response_model=ApiResponse)
async def chat(request: ChatRequest):
    """
    智能问答（非流式）
    """
    # 记录查询统计
    stats_service.record_query()

    # 执行问答
    result = await chat_service.chat(
        query=request.query,
        conversation_id=request.conversation_id,
        collection=request.collection or "default"
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
    collection: str = Query("default")
):
    """
    流式问答（SSE）

    使用 EventSource 接收流式响应
    """
    # 记录查询统计
    stats_service.record_query()

    async def event_generator():
        async for line in chat_service.chat_stream(
            query=query,
            conversation_id=conversation_id,
            collection=collection
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


@router.get("/history", response_model=ApiResponse)
async def get_chat_history(conversation_id: Optional[str] = Query(None)):
    """
    获取对话历史
    """
    if conversation_id:
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
        # 从数据库获取所有对话列表
        from sqlalchemy import desc
        from app.core.database import SessionLocal
        from app.models.chat import Conversation

        db = SessionLocal()
        try:
            conversations_db = db.query(Conversation).filter(
                Conversation.is_active == "Y"
            ).order_by(desc(Conversation.updated_at)).all()

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

"""
MCP Server Tools.

This package contains the MCP tool definitions exposed to clients.
"""

from src.mcp_server.tools.query_knowledge_hub import (
    TOOL_NAME as QUERY_KNOWLEDGE_HUB_NAME,
    TOOL_DESCRIPTION as QUERY_KNOWLEDGE_HUB_DESCRIPTION,
    TOOL_INPUT_SCHEMA as QUERY_KNOWLEDGE_HUB_SCHEMA,
    QueryKnowledgeHubTool,
    query_knowledge_hub_handler,
    register_tool as register_query_knowledge_hub,
)

from src.mcp_server.tools.rag_chat import (
    TOOL_NAME as RAG_CHAT_NAME,
    TOOL_DESCRIPTION as RAG_CHAT_DESCRIPTION,
    TOOL_INPUT_SCHEMA as RAG_CHAT_SCHEMA,
    RagChatTool,
    rag_chat_handler,
    register_tool as register_rag_chat,
)

__all__ = [
    "QUERY_KNOWLEDGE_HUB_NAME",
    "QUERY_KNOWLEDGE_HUB_DESCRIPTION",
    "QUERY_KNOWLEDGE_HUB_SCHEMA",
    "QueryKnowledgeHubTool",
    "query_knowledge_hub_handler",
    "register_query_knowledge_hub",
    "RAG_CHAT_NAME",
    "RAG_CHAT_DESCRIPTION",
    "RAG_CHAT_SCHEMA",
    "RagChatTool",
    "rag_chat_handler",
    "register_rag_chat",
]

"""MCP Tool: rag_chat

This tool provides the full RAG chat capability through the MCP protocol.
It combines HybridSearch (Dense + Sparse + RRF Fusion) with optional Reranking
and LLM answer generation to produce complete responses with sources.

This is the MCP-native equivalent of the backend's `chat_stream` endpoint,
adapted for stdio transport (returns complete answer rather than SSE stream).

Usage via MCP:
    Tool name: rag_chat
    Input schema:
        - query (string, required): The user's question
        - collection (string, optional): Collection name (default: "knowledge-hub")
        - conversation_history (array, optional): Array of {role, content} messages
        - top_k (integer, optional): Number of search results (default: 10)
        - generate_related_questions (boolean, optional): Generate follow-up questions (default: true)
"""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from mcp import types

from src.core.settings import load_settings, Settings
from src.core.trace import TraceContext, TraceCollector
from src.core.types import RetrievalResult

if TYPE_CHECKING:
    from src.libs.llm.base_llm import BaseLLM
    from src.mcp_server.protocol_handler import ProtocolHandler

logger = logging.getLogger(__name__)


# Tool metadata
TOOL_NAME = "rag_chat"
TOOL_DESCRIPTION = """Full RAG chat: search the knowledge base and generate an AI answer based on retrieved documents.

This tool performs the complete RAG (Retrieval-Augmented Generation) pipeline:
1. Hybrid search (semantic + keyword) to find relevant documents
2. Optional reranking for better result ordering
3. LLM generates answer grounded in the retrieved context
4. Returns sources, citations, and optionally related follow-up questions

Use this when you need AI-generated answers based on the knowledge base, not just search results.

Parameters:
- query: The user's question or search query (required)
- collection: Limit search to a specific collection (default: "knowledge-hub")
- conversation_history: Previous messages for context, array of {role: "user"|"assistant", content: string}
- top_k: Number of documents to retrieve (default: 10, max: 20)
- generate_related_questions: Whether to generate follow-up questions (default: true)
"""

TOOL_INPUT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "query": {
            "type": "string",
            "description": "The user's question or query to answer based on knowledge base documents.",
        },
        "collection": {
            "type": "string",
            "description": "Collection name to search in. Defaults to 'knowledge-hub'.",
            "default": "knowledge-hub",
        },
        "conversation_history": {
            "type": "array",
            "description": "Previous conversation messages for context. Array of objects with 'role' ('user' or 'assistant') and 'content' fields.",
            "items": {
                "type": "object",
                "properties": {
                    "role": {"type": "string", "enum": ["user", "assistant"]},
                    "content": {"type": "string"},
                },
                "required": ["role", "content"],
            },
        },
        "top_k": {
            "type": "integer",
            "description": "Number of documents to retrieve for context.",
            "default": 10,
            "minimum": 1,
            "maximum": 20,
        },
        "generate_related_questions": {
            "type": "boolean",
            "description": "Whether to generate follow-up questions based on the answer.",
            "default": True,
        },
    },
    "required": ["query"],
}


@dataclass
class RagChatConfig:
    """Configuration for rag_chat tool.

    Attributes:
        default_top_k: Default number of results to retrieve
        max_top_k: Maximum allowed top_k value
        default_collection: Default collection name
        enable_rerank: Whether to apply reranking
        system_prompt: System prompt template for the LLM
    """
    default_top_k: int = 10
    max_top_k: int = 20
    default_collection: str = "knowledge-hub"
    enable_rerank: bool = True

    SYSTEM_PROMPT: str = """你是一个专业的企业知识库助手，基于提供的文档内容回答用户问题。

请遵循以下原则：
1. 只基于提供的上下文信息回答，不要编造信息
2. 如果上下文不足以回答问题，请明确告知用户
3. 回答要简洁、准确、专业
4. 如果涉及多个文档，请综合信息给出完整回答
5. 可以引用具体的文档来源

--- 以下是检索到的上下文 ---
{context}
--- 上下文结束 ---"""


class RagChatTool:
    """MCP Tool for full RAG chat (search + LLM answer generation).

    This tool combines the existing hybrid search infrastructure with LLM
    answer generation to provide a complete RAG pipeline via MCP.

    Design Principles:
    - Reuses existing search components (QueryKnowledgeHubTool pattern)
    - LLM created via LLMFactory for provider flexibility
    - Lazy initialization of heavy components
    - Error resilience with clear error messages
    - Observable with trace collection

    Example:
        >>> tool = RagChatTool(settings)
        >>> result = await tool.execute(query="年假有多少天？")
        >>> print(result.content)
    """

    def __init__(
        self,
        settings: Optional[Settings] = None,
        config: Optional[RagChatConfig] = None,
        llm: Optional[BaseLLM] = None,
    ) -> None:
        """Initialize RagChatTool.

        Args:
            settings: Application settings. If None, loaded from default path.
            config: Tool configuration. If None, uses defaults.
            llm: Optional pre-configured LLM instance. If None, created via LLMFactory.
        """
        self._settings = settings
        self.config = config or RagChatConfig()
        self._llm = llm
        self._hybrid_search = None
        self._reranker = None
        self._embedding_client = None
        self._initialized = False
        self._current_collection: Optional[str] = None

    @property
    def settings(self) -> Settings:
        """Get settings, loading if necessary."""
        if self._settings is None:
            self._settings = load_settings()
        return self._settings

    def _get_llm(self) -> BaseLLM:
        """Get or create LLM instance."""
        if self._llm is None:
            from src.libs.llm.llm_factory import LLMFactory
            self._llm = LLMFactory.create(self.settings)
        return self._llm

    def _ensure_initialized(self, collection: str) -> None:
        """Ensure search components are initialized for the given collection.

        Follows the same pattern as QueryKnowledgeHubTool._ensure_initialized.
        """
        # Always rebuild vector_store and retriever components so that
        # data ingested by other processes is visible immediately.

        if self._initialized and self._current_collection == collection:
            return

        logger.info(f"Initializing RAG components for collection: {collection}")

        from src.core.query_engine.query_processor import QueryProcessor
        from src.core.query_engine.hybrid_search import create_hybrid_search
        from src.core.query_engine.dense_retriever import create_dense_retriever
        from src.core.query_engine.sparse_retriever import create_sparse_retriever
        from src.core.query_engine.reranker import create_core_reranker
        from src.ingestion.storage.bm25_indexer import BM25Indexer
        from src.libs.embedding.embedding_factory import EmbeddingFactory
        from src.libs.vector_store.vector_store_factory import VectorStoreFactory

        # Fully cached components (stateless, never go stale)
        if self._embedding_client is None:
            self._embedding_client = EmbeddingFactory.create(self.settings)

        if self._reranker is None:
            self._reranker = create_core_reranker(settings=self.settings)

        # Rebuild for new collection
        vector_store = VectorStoreFactory.create(
            self.settings,
            collection_name=collection,
        )

        dense_retriever = create_dense_retriever(
            settings=self.settings,
            embedding_client=self._embedding_client,
            vector_store=vector_store,
        )

        from src.core.settings import resolve_path
        bm25_indexer = BM25Indexer(index_dir=str(resolve_path(f"data/db/bm25/{collection}")))
        sparse_retriever = create_sparse_retriever(
            settings=self.settings,
            bm25_indexer=bm25_indexer,
            vector_store=vector_store,
        )
        sparse_retriever.default_collection = collection

        query_processor = QueryProcessor()
        self._hybrid_search = create_hybrid_search(
            settings=self.settings,
            query_processor=query_processor,
            dense_retriever=dense_retriever,
            sparse_retriever=sparse_retriever,
        )

        self._current_collection = collection
        self._initialized = True
        logger.info(f"RAG components initialized for collection: {collection}")

    def _perform_search(
        self,
        query: str,
        top_k: int,
        trace: Optional[Any] = None,
    ) -> List[RetrievalResult]:
        """Perform hybrid search.

        Args:
            query: Search query.
            top_k: Maximum results.
            trace: Optional TraceContext for observability.

        Returns:
            List of RetrievalResult.
        """
        if self._hybrid_search is None:
            raise RuntimeError("HybridSearch not initialized")

        # Use a larger initial retrieval for reranking
        initial_top_k = top_k * 2 if self.config.enable_rerank else top_k

        try:
            results = self._hybrid_search.search(
                query=query,
                top_k=initial_top_k,
                filters=None,
                trace=trace,
                return_details=False,
            )
            return results if isinstance(results, list) else results.results
        except Exception as e:
            logger.warning(f"Hybrid search failed: {e}")
            return []

    def _apply_rerank(
        self,
        query: str,
        results: List[RetrievalResult],
        top_k: int,
        trace: Optional[Any] = None,
    ) -> List[RetrievalResult]:
        """Apply reranking to search results.

        Args:
            query: Original query.
            results: Search results to rerank.
            top_k: Final number of results.
            trace: Optional TraceContext for observability.

        Returns:
            Reranked results (or original if reranking fails).
        """
        if self._reranker is None or not self._reranker.is_enabled:
            return results[:top_k]

        try:
            rerank_result = self._reranker.rerank(
                query=query,
                results=results,
                top_k=top_k,
                trace=trace,
            )

            if rerank_result.used_fallback:
                logger.warning(f"Reranker fallback: {rerank_result.fallback_reason}")

            return rerank_result.results
        except Exception as e:
            logger.warning(f"Reranking failed, using original order: {e}")
            return results[:top_k]

    def _build_context(self, results: List[RetrievalResult]) -> str:
        """Format search results into context string for the LLM.

        Args:
            results: List of RetrievalResult.

        Returns:
            Formatted context string with source citations.
        """
        if not results:
            return "（未检索到相关文档）"

        context_parts = []
        for i, r in enumerate(results, 1):
            source = r.metadata.get("source_path", r.metadata.get("source", "未知来源"))
            source_name = source.split("/")[-1] if source else "未知文档"
            page_info = f" (第{r.metadata.get('page', '?')}页)" if r.metadata.get("page") else ""
            title = r.metadata.get("title", "")
            title_str = f" - {title}" if title else ""
            context_parts.append(
                f"[{i}] {source_name}{title_str}{page_info}:\n{r.text or ''}"
            )

        return "\n\n".join(context_parts)

    def _generate_related_questions(self, query: str, answer: str) -> List[str]:
        """Generate follow-up questions based on the answer.

        Uses keyword matching and template-based generation,
        same as the backend's RAGService.generate_related_questions.

        Args:
            query: Original user query.
            answer: Generated answer text.

        Returns:
            List of 3 follow-up questions.
        """
        keywords = ["报销", "年假", "福利", "培训", "考勤", "绩效", "请假", "加班", "入职", "离职"]

        topic = "相关事项"
        for kw in keywords:
            if kw in query or kw in answer:
                topic = kw
                break

        templates = [
            f"{topic}的具体流程是什么？",
            f"如何申请{topic}？",
            f"{topic}需要准备哪些材料？",
            f"{topic}的审批周期是多久？",
            f"{topic}有哪些注意事项？"
        ]

        import random
        random.seed(hash(query) % 10000)
        selected = random.sample(templates, min(3, len(templates)))
        return selected

    async def execute(
        self,
        query: str,
        collection: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        top_k: Optional[int] = None,
        generate_related_questions: bool = True,
    ) -> types.CallToolResult:
        """Execute the rag_chat tool.

        Args:
            query: User's question or query.
            collection: Target collection name.
            conversation_history: Previous conversation messages.
            top_k: Number of documents to retrieve.
            generate_related_questions: Whether to generate follow-up questions.

        Returns:
            CallToolResult with the complete answer, sources, and metadata.
        """
        # Validate query
        if not query or not query.strip():
            return types.CallToolResult(
                content=[types.TextContent(type="text", text="错误: 查询不能为空")],
                isError=True,
            )

        # Apply defaults
        effective_top_k = min(
            top_k or self.config.default_top_k,
            self.config.max_top_k
        )
        effective_collection = collection or self.config.default_collection

        logger.info(
            f"Executing rag_chat: query='{query[:50]}...', "
            f"top_k={effective_top_k}, collection={effective_collection}"
        )

        trace = TraceContext(trace_type="rag_chat")
        trace.metadata["query"] = query[:200]
        trace.metadata["top_k"] = effective_top_k
        trace.metadata["collection"] = effective_collection
        trace.metadata["source"] = "mcp"

        try:
            # Initialize components (blocking I/O in thread)
            import time as _time
            _init_t0 = _time.monotonic()
            await asyncio.to_thread(self._ensure_initialized, effective_collection)
            _init_elapsed = (_time.monotonic() - _init_t0) * 1000.0
            trace.record_stage("initialization", {
                "collection": effective_collection,
                "cold_start": _init_elapsed > 500,
            }, elapsed_ms=_init_elapsed)

            # Step 1: Hybrid search (blocking: embedding API + DB queries)
            _search_t0 = _time.monotonic()
            results = await asyncio.to_thread(
                self._perform_search, query, effective_top_k, trace,
            )
            _search_elapsed = (_time.monotonic() - _search_t0) * 1000.0
            trace.record_stage("search", {
                "result_count": len(results),
            }, elapsed_ms=_search_elapsed)

            # Step 1b: Rerank (blocking: may call cross-encoder or LLM API)
            if self.config.enable_rerank and results:
                _rerank_t0 = _time.monotonic()
                results = await asyncio.to_thread(
                    self._apply_rerank, query, results, effective_top_k, trace,
                )
                _rerank_elapsed = (_time.monotonic() - _rerank_t0) * 1000.0
                trace.record_stage("rerank", {
                    "result_count": len(results),
                }, elapsed_ms=_rerank_elapsed)

            # Build sources list
            sources = []
            for r in results[:5]:
                sources.append({
                    "chunk_id": r.chunk_id,
                    "document_name": r.metadata.get("source_path", "Unknown").split("/")[-1],
                    "content": (r.text or "")[:500],
                    "page": r.metadata.get("page"),
                    "score": round(r.score, 4) if hasattr(r, "score") else 0.0,
                    "title": r.metadata.get("title", ""),
                })

            # Handle no results case
            if not results:
                no_result_msg = """抱歉，我暂时没有找到与您问题相关的文档内容。

您可以尝试：
1. 使用不同的关键词重新提问
2. 检查文档是否已上传到知识库
3. 联系管理员添加相关文档"""

                response = {
                    "answer": no_result_msg,
                    "sources": [],
                    "result_count": 0,
                }
                if generate_related_questions:
                    response["related_questions"] = [
                        "如何上传文档到知识库？",
                        "支持哪些类型的文档？",
                        "如何联系管理员？"
                    ]

                response_text = f"## 未找到相关结果\n\n{no_result_msg}"
                if response.get("related_questions"):
                    response_text += "\n\n### 您可能还想了解\n\n"
                    for q in response["related_questions"]:
                        response_text += f"- {q}\n"

                # Add structured JSON for machine consumption
                structured_json = json.dumps(response, ensure_ascii=False)
                response_text += f"\n\n---\n**响应数据 (JSON):**\n```json\n{structured_json}\n```"

                trace.metadata["no_results"] = True
                TraceCollector().collect(trace)

                return types.CallToolResult(
                    content=[types.TextContent(type="text", text=response_text)],
                    isError=False,
                )

            # Step 2: LLM answer generation (blocking: LLM API call)
            _llm_t0 = _time.monotonic()
            answer = await asyncio.to_thread(
                self._generate_answer, query, results, conversation_history, trace,
            )
            _llm_elapsed = (_time.monotonic() - _llm_t0) * 1000.0
            trace.record_stage("llm_generation", {
                "answer_length": len(answer),
            }, elapsed_ms=_llm_elapsed)

            # Build response
            response_text = self._format_response(answer, sources)

            # Generate related questions if requested
            related_questions = []
            if generate_related_questions:
                related_questions = self._generate_related_questions(query, answer)
                if related_questions:
                    response_text += "\n\n### 您可能还想了解\n\n"
                    for q in related_questions:
                        response_text += f"- {q}\n"

            # Build structured response data
            response_data = {
                "answer": answer,
                "sources": sources,
                "result_count": len(results),
            }
            if related_questions:
                response_data["related_questions"] = related_questions

            # Append structured JSON for machine consumption
            structured_json = json.dumps(response_data, ensure_ascii=False, indent=2)
            response_text += f"\n\n---\n**响应数据 (JSON):**\n```json\n{structured_json}\n```"

            trace.metadata["answer_length"] = len(answer)
            trace.metadata["source_count"] = len(sources)
            TraceCollector().collect(trace)

            return types.CallToolResult(
                content=[types.TextContent(type="text", text=response_text)],
                isError=False,
            )

        except Exception as e:
            logger.exception("rag_chat failed")
            TraceCollector().collect(trace)
            return types.CallToolResult(
                content=[
                    types.TextContent(
                        type="text",
                        text=f"## 查询失败\n\n处理请求时发生错误: {str(e)}\n\n请检查:\n- 数据库连接是否正常\n- 集合是否已创建并包含数据\n- 配置文件是否正确",
                    )
                ],
                isError=True,
            )

    def _generate_answer(
        self,
        query: str,
        results: List[RetrievalResult],
        conversation_history: Optional[List[Dict[str, str]]] = None,
        trace: Optional[Any] = None,
    ) -> str:
        """Generate LLM answer based on retrieved context.

        This runs synchronously (it will be called via asyncio.to_thread).

        Args:
            query: User's query.
            results: Search results.
            conversation_history: Previous messages.
            trace: Optional TraceContext.

        Returns:
            Generated answer text.
        """
        from src.libs.llm.base_llm import Message

        llm = self._get_llm()
        context = self._build_context(results)
        system_prompt = self.config.SYSTEM_PROMPT.format(context=context)

        # Build messages
        messages = [Message(role="system", content=system_prompt)]

        # Add conversation history (last 3 turns = 6 messages)
        if conversation_history:
            for msg in conversation_history[-6:]:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role in ("user", "assistant") and content:
                    messages.append(Message(role=role, content=content))

        # Add current query
        messages.append(Message(role="user", content=query))

        # Call LLM
        try:
            response = llm.chat(messages, trace=trace)
            return response.content
        except Exception as e:
            logger.warning(f"LLM generation failed: {e}")
            # Return context-based fallback answer
            return f"""根据检索到的文档，以下是相关信息：

{context[:1000]}...

注意：AI 生成服务暂时不可用，以上为检索到的原始内容摘要。"""

    def _format_response(self, answer: str, sources: List[Dict[str, Any]]) -> str:
        """Format the response with answer and sources.

        Args:
            answer: Generated answer text.
            sources: List of source dictionaries.

        Returns:
            Formatted markdown string.
        """
        lines = [
            "## AI 回答",
            "",
            answer,
            "",
            "---",
            "",
            "## 参考来源",
            "",
        ]

        if not sources:
            lines.append("未找到相关参考来源。")
        else:
            for i, src in enumerate(sources, 1):
                doc_name = src.get("document_name", "未知文档")
                title = src.get("title", "")
                page = src.get("page")
                score = src.get("score", 0.0)
                chunk_id = src.get("chunk_id", "")

                line = f"**[{i}]** {doc_name}"
                if title:
                    line += f" - {title}"
                if page:
                    line += f" (第{page}页)"
                line += f" (相关度: {score:.2%})"
                lines.append(line)

                if chunk_id:
                    lines.append(f"     `ID: {chunk_id}`")

                # Preview first 150 chars of content
                content_preview = src.get("content", "")[:150]
                if content_preview:
                    lines.append(f"     > {content_preview}...")
                lines.append("")

        return "\n".join(lines)


# Module-level tool instance (lazy-initialized)
_tool_instance: Optional[RagChatTool] = None


def get_tool_instance(settings: Optional[Settings] = None) -> RagChatTool:
    """Get or create the tool instance.

    Args:
        settings: Optional settings to use for initialization.

    Returns:
        RagChatTool instance.
    """
    global _tool_instance
    if _tool_instance is None:
        _tool_instance = RagChatTool(settings=settings)
    return _tool_instance


async def rag_chat_handler(
    query: str,
    collection: Optional[str] = None,
    conversation_history: Optional[List[Dict[str, str]]] = None,
    top_k: int = 10,
    generate_related_questions: bool = True,
) -> types.CallToolResult:
    """Handler function for MCP tool registration.

    This function is registered with the ProtocolHandler and called
    when the MCP client invokes the rag_chat tool.

    Args:
        query: User's question or query.
        collection: Optional collection name.
        conversation_history: Optional previous conversation messages.
        top_k: Number of documents to retrieve.
        generate_related_questions: Whether to generate follow-up questions.

    Returns:
        MCP CallToolResult with the complete answer and sources.
    """
    tool = get_tool_instance()

    return await tool.execute(
        query=query,
        collection=collection,
        conversation_history=conversation_history,
        top_k=top_k,
        generate_related_questions=generate_related_questions,
    )


def register_tool(protocol_handler: ProtocolHandler) -> None:
    """Register rag_chat tool with the protocol handler.

    Args:
        protocol_handler: ProtocolHandler instance to register with.
    """
    protocol_handler.register_tool(
        name=TOOL_NAME,
        description=TOOL_DESCRIPTION,
        input_schema=TOOL_INPUT_SCHEMA,
        handler=rag_chat_handler,
    )
    logger.info(f"Registered MCP tool: {TOOL_NAME}")

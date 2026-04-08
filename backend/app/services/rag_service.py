"""
RAG Service - 复用现有RAG模块提供检索和生成能力
实现了完整的RAG流程：检索 -> 构建上下文 -> LLM生成
"""
import os
import sys
import json
import asyncio
from typing import List, Optional, Dict, Any, AsyncGenerator
from pathlib import Path

# 添加项目src目录到Python路径
PROJECT_ROOT = Path(__file__).resolve().parents[3]
src_path = PROJECT_ROOT / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# 导入RAG模块
from src.core.settings import load_settings
from src.core.query_engine.hybrid_search import HybridSearch, create_hybrid_search, HybridSearchConfig
from src.core.query_engine.dense_retriever import DenseRetriever, create_dense_retriever
from src.core.query_engine.sparse_retriever import SparseRetriever
from src.core.query_engine.query_processor import QueryProcessor
from src.core.query_engine.fusion import RRFFusion
from src.core.types import RetrievalResult
from src.libs.llm.qwen_llm import QwenLLM
from src.libs.llm.base_llm import Message


class RAGService:
    """RAG服务 - 封装检索和生成能力"""

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if RAGService._initialized:
            return

        self.settings = None
        self.hybrid_search: Optional[HybridSearch] = None
        self.llm: Optional[QwenLLM] = None
        self._load_settings()
        self._init_hybrid_search()
        self._init_llm()
        RAGService._initialized = True

    def _load_settings(self):
        """加载配置"""
        try:
            settings_path = PROJECT_ROOT / "config" / "settings.yaml"
            if settings_path.exists():
                self.settings = load_settings(str(settings_path))
                print(f"[RAGService] Settings loaded from {settings_path}")
            else:
                print(f"[RAGService] Warning: Settings file not found at {settings_path}")
                self.settings = None
        except Exception as e:
            print(f"[RAGService] Warning: Failed to load settings: {e}")
            self.settings = None

    def _init_hybrid_search(self):
        """初始化混合检索引擎"""
        if self.settings is None:
            print("[RAGService] Warning: Cannot initialize hybrid search without settings")
            return

        try:
            # 创建QueryProcessor
            query_processor = QueryProcessor()

            # 创建DenseRetriever
            dense_retriever = create_dense_retriever(self.settings)

            # 创建SparseRetriever（可选，如果有BM25索引）
            sparse_retriever = None
            try:
                from src.ingestion.storage.bm25_indexer import BM25Indexer
                from src.libs.vector_store.vector_store_factory import VectorStoreFactory
                from pathlib import Path
                
                # 初始化 BM25 索引器（使用绝对路径确保可靠性）
                project_root = Path(__file__).parent.parent.parent.parent
                bm25_index_path = project_root / "data" / "db" / "bm25" / "knowledge-hub"
                bm25_indexer = BM25Indexer(index_dir=str(bm25_index_path))
                
                # 初始化向量存储
                vector_store = VectorStoreFactory.create(self.settings)
                
                # 创建 SparseRetriever
                sparse_retriever = SparseRetriever(
                    settings=self.settings,
                    bm25_indexer=bm25_indexer,
                    vector_store=vector_store,
                )
                # 设置正确的 collection 名称以匹配现有的 BM25 索引文件
                sparse_retriever.default_collection = "knowledge-hub"
                print(f"[RAGService] SparseRetriever initialized successfully (BM25 path: {bm25_index_path})")
            except Exception as e:
                print(f"[RAGService] SparseRetriever not available: {e}")
                import traceback
                traceback.print_exc()

            # 创建RRFFusion
            rrf_k = getattr(self.settings, 'retrieval', None) and getattr(
                self.settings.retrieval, 'rrf_k', 60
            ) or 60
            fusion = RRFFusion(k=rrf_k)

            # 创建HybridSearch
            self.hybrid_search = HybridSearch(
                settings=self.settings,
                query_processor=query_processor,
                dense_retriever=dense_retriever,
                sparse_retriever=sparse_retriever,
                fusion=fusion,
            )
            print("[RAGService] HybridSearch initialized successfully")

        except Exception as e:
            print(f"[RAGService] Error initializing HybridSearch: {e}")
            import traceback
            traceback.print_exc()
            self.hybrid_search = None

    def _init_llm(self):
        """初始化LLM"""
        if self.settings is None:
            print("[RAGService] Warning: Cannot initialize LLM without settings")
            return

        self.llm = QwenLLM(settings=self.settings)
        print(f"[RAGService] QwenLLM initialized with main llm config")

    async def search(
        self,
        query: str,
        collection: str = "default",  # 保留参数以兼容旧接口，但不再使用
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None  # 新增：支持真正的元数据过滤
    ) -> List[Dict[str, Any]]:
        """
        执行混合检索

        Args:
            query: 查询文本
            collection: 集合名称（已废弃，Collection 在初始化时已确定）
            top_k: 返回结果数量
            filters: 可选的元数据过滤器（如 {"department": "研发部", "file_type": "pdf"}）

        Returns:
            检索结果列表
        """
        if self.hybrid_search is None:
            print("[RAGService] Warning: HybridSearch not initialized, returning empty results")
            return []

        try:
            # 执行混合检索
            # 注意：collection 已在 HybridSearch 初始化时通过 VectorStore 确定
            # filters 用于过滤文档元数据，而非指定 collection
            results = self.hybrid_search.search(
                query=query,
                top_k=top_k,
                filters=filters,  # 使用真正的元数据过滤器
                return_details=False
            )

            # 转换为字典列表
            search_results = []
            for r in results:
                search_results.append({
                    "chunk_id": r.chunk_id,
                    "document_id": r.metadata.get("document_id", ""),
                    "document_name": r.metadata.get("source_path", "Unknown").split("/")[-1],
                    "content": r.text or "",
                    "page": r.metadata.get("page"),
                    "score": r.score,
                    "metadata": r.metadata
                })

            return search_results

        except Exception as e:
            print(f"[RAGService] Search error: {e}")
            import traceback
            traceback.print_exc()
            return []

    def _build_system_prompt(self) -> str:
        """构建系统提示词"""
        return """你是一个专业的企业知识库助手，基于提供的文档内容回答用户问题。

请遵循以下原则：
1. 只基于提供的上下文信息回答，不要编造信息
2. 如果上下文不足以回答问题，请明确告知用户
3. 回答要简洁、准确、专业
4. 如果涉及多个文档，请综合信息给出完整回答
5. 可以引用具体的文档来源

上下文信息："""

    def _build_context_prompt(self, search_results: List[Dict[str, Any]]) -> str:
        """构建上下文提示词"""
        if not search_results:
            return "（暂无相关文档内容）"

        context_parts = []
        for i, result in enumerate(search_results, 1):
            source = result.get("document_name", "未知文档")
            page_info = f" (第{result['page']}页)" if result.get("page") else ""
            content = result.get("content", "")
            context_parts.append(f"[{i}] {source}{page_info}:\n{content}")

        return "\n\n".join(context_parts)

    async def generate_answer(
        self,
        query: str,
        context: List[Dict[str, Any]],
        conversation_history: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        生成回答

        Args:
            query: 用户问题
            context: 检索到的上下文
            conversation_history: 对话历史

        Returns:
            包含answer、sources和related_questions的字典
        """
        if self.llm is None:
            print("[RAGService] Warning: LLM not initialized, returning fallback answer")
            return {
                "answer": "抱歉，AI服务暂时不可用，请稍后重试。",
                "sources": context[:5],
                "related_questions": []
            }

        try:
            # 构建消息列表
            messages = []

            # 添加系统提示
            system_prompt = self._build_system_prompt()
            context_prompt = self._build_context_prompt(context)
            full_system = f"{system_prompt}\n\n{context_prompt}"
            messages.append(Message(role="system", content=full_system))

            # 添加历史对话（最多3轮）
            if conversation_history:
                for msg in conversation_history[-6:]:  # 最近6条消息（3轮）
                    role = msg.get("role", "user")
                    content = msg.get("content", "")
                    messages.append(Message(role=role, content=content))

            # 添加当前问题
            messages.append(Message(role="user", content=query))

            # 调用LLM生成回答
            response = self.llm.chat(messages)

            # 生成相关问题
            related_questions = self.generate_related_questions(query, response.content)

            # 构建sources
            sources = []
            for result in context[:5]:
                sources.append({
                    "document_id": result.get("document_id", ""),
                    "document_name": result.get("document_name", "Unknown"),
                    "chunk_id": result.get("chunk_id", ""),
                    "content": result.get("content", "")[:500],
                    "page": result.get("page"),
                    "score": result.get("score", 0.0)
                })

            return {
                "answer": response.content,
                "sources": sources,
                "related_questions": related_questions
            }

        except Exception as e:
            print(f"[RAGService] Generate answer error: {e}")
            import traceback
            traceback.print_exc()
            return {
                "answer": "抱歉，生成回答时出现错误，请稍后重试。",
                "sources": context[:5],
                "related_questions": []
            }

    async def generate_answer_stream(
        self,
        query: str,
        context: List[Dict[str, Any]],
        conversation_history: Optional[List[Dict]] = None
    ) -> AsyncGenerator[str, None]:
        """
        流式生成回答

        Args:
            query: 用户问题
            context: 检索到的上下文
            conversation_history: 对话历史

        Yields:
            SSE格式的数据行
        """
        # 首先返回sources
        sources = []
        for result in context[:5]:
            sources.append({
                "document_id": result.get("document_id", ""),
                "document_name": result.get("document_name", "Unknown"),
                "chunk_id": result.get("chunk_id", ""),
                "content": result.get("content", "")[:500],
                "page": result.get("page"),
                "score": result.get("score", 0.0)
            })

        yield f'data: {json.dumps({"type": "sources", "sources": sources}, ensure_ascii=False)}\n\n'

        if self.llm is None:
            yield f'data: {json.dumps({"type": "token", "content": "抱歉，AI服务暂时不可用，请稍后重试。"}, ensure_ascii=False)}\n\n'
            yield f'data: {json.dumps({"type": "done"}, ensure_ascii=False)}\n\n'
            return

        try:
            # 构建消息列表
            messages = []

            # 添加系统提示
            system_prompt = self._build_system_prompt()
            context_prompt = self._build_context_prompt(context)
            full_system = f"{system_prompt}\n\n{context_prompt}"
            messages.append(Message(role="system", content=full_system))

            # 添加历史对话（最多3轮）
            if conversation_history:
                for msg in conversation_history[-6:]:
                    role = msg.get("role", "user")
                    content = msg.get("content", "")
                    messages.append(Message(role=role, content=content))

            # 添加当前问题
            messages.append(Message(role="user", content=query))

            # 调用LLM流式生成
            # 注意：当前QwenLLM不支持流式，我们模拟流式效果
            response = self.llm.chat(messages)

            # 模拟流式输出（按句子分割）
            import re
            content = response.content
            sentences = re.split(r'([。！？.!?\n])', content)

            full_answer = ""
            for i in range(0, len(sentences) - 1, 2):
                sentence = sentences[i]
                punct = sentences[i + 1] if i + 1 < len(sentences) else ""
                chunk = sentence + punct
                full_answer += chunk
                yield f'data: {json.dumps({"type": "token", "content": chunk}, ensure_ascii=False)}\n\n'
                await asyncio.sleep(0.05)  # 模拟打字效果

            # 如果有剩余内容
            if len(sentences) % 2 == 1:
                remaining = sentences[-1]
                if remaining:
                    full_answer += remaining
                    yield f'data: {json.dumps({"type": "token", "content": remaining}, ensure_ascii=False)}\n\n'

            # 生成并返回相关问题
            related_questions = self.generate_related_questions(query, full_answer)
            if related_questions:
                yield f'data: {json.dumps({"type": "related_questions", "related_questions": related_questions}, ensure_ascii=False)}\n\n'

            yield f'data: {json.dumps({"type": "done"}, ensure_ascii=False)}\n\n'

        except Exception as e:
            print(f"[RAGService] Stream generation error: {e}")
            import traceback
            traceback.print_exc()
            yield f'data: {json.dumps({"type": "token", "content": "抱歉，生成回答时出现错误，请稍后重试。"}, ensure_ascii=False)}\n\n'
            yield f'data: {json.dumps({"type": "done"}, ensure_ascii=False)}\n\n'

    def generate_related_questions(self, query: str, answer: str) -> List[str]:
        """生成相关问题"""
        # 基于关键词生成相关问题
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


# 全局RAG服务实例
rag_service = RAGService()

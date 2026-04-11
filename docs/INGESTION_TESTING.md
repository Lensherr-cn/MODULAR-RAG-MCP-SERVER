# 数据摄取流水线测试指南

> 本文档介绍如何测试 Modular RAG MCP Server 的数据摄取流水线功能。

---

## 目录

1. [测试环境准备](#测试环境准备)
2. [快速开始（5分钟上手）](#快速开始5分钟上手)
3. [测试方法详解](#测试方法详解)
4. [测试场景覆盖](#测试场景覆盖)
5. [常见问题排查](#常见问题排查)

---

## 测试环境准备

### 1. 安装依赖

```bash
# 进入项目目录
cd MODULAR-RAG-MCP-SERVER

# 安装 Python 依赖
pip install -r requirements.txt

# 验证关键依赖
python -c "import markitdown; print('✓ MarkItDown')"
python -c "import fitz; print('✓ PyMuPDF')"
python -c "import chromadb; print('✓ ChromaDB')"
```

### 2. 配置 API 密钥

```bash
# 方式1：环境变量（推荐）
export AZURE_API_KEY="your-azure-api-key"
export AZURE_ENDPOINT="https://your-resource.openai.azure.com/"

# 方式2：.env 文件
cp .env.example .env
# 编辑 .env 填入密钥
```

### 3. 准备测试文档

```bash
# 创建测试目录
mkdir -p data/documents

# 放入测试 PDF 文件
cp your-test-file.pdf data/documents/

# 或使用项目自带的测试文档
ls tests/fixtures/sample_documents/
```

---

## 快速开始（5分钟上手）

### 方式一：命令行快速测试

```bash
# 1. 干运行 - 查看会处理哪些文件
python scripts/ingest.py --path data/documents/ --dry-run

# 2. 处理单个文件（详细输出）
python scripts/ingest.py \
    --path data/documents/test.pdf \
    --collection test_collection \
    --verbose

# 3. 强制重新处理
python scripts/ingest.py \
    --path data/documents/test.pdf \
    --collection test_collection \
    --force \
    --verbose
```

### 方式二：Python 交互式测试

```python
# test_ingestion.py
from src.core.settings import load_settings
from src.ingestion.pipeline import IngestionPipeline

# 加载配置
settings = load_settings("config/settings.yaml")

# 创建流水线
pipeline = IngestionPipeline(
    settings=settings,
    collection="test_collection",
    force=True  # 强制重新处理
)

# 运行测试
result = pipeline.run("data/documents/test.pdf")

# 检查结果
print(f"成功: {result.success}")
print(f"Chunks: {result.chunk_count}")
print(f"Images: {result.image_count}")
print(f"Vectors: {len(result.vector_ids)}")

# 查看各阶段详情
for stage_name, stage_data in result.stages.items():
    print(f"\n{stage_name}:")
    print(f"  {stage_data}")

pipeline.close()
```

运行：
```bash
python test_ingestion.py
```

---

## 测试方法详解

### 方法一：单元测试

```bash
# 运行所有单元测试
pytest tests/unit/ -v

# 运行特定测试
pytest tests/unit/test_document_chunker.py -v
pytest tests/unit/test_chunk_refiner.py -v
pytest tests/unit/test_metadata_enricher_contract.py -v
```

### 方法二：集成测试

```bash
# 运行摄取流水线集成测试（需要配置 API 密钥）
pytest tests/integration/test_ingestion_pipeline.py -v -s

# 测试输出示例：
# [OK] Generated 32 chunks
# [OK] Stored 32 vectors
# [OK] Dense vectors: 32 x 1536dim
# SUCCESS - All pipeline stages completed!
```

### 方法三：端到端测试

```bash
# E2E 测试（完整流程）
pytest tests/e2e/test_data_ingestion.py -v -s
```

### 方法四：手动验证各阶段

#### 4.1 测试文件完整性检查

```python
from src.libs.loader.file_integrity import SQLiteIntegrityChecker
import tempfile
import os

# 创建临时文件
with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
    f.write("test content")
    temp_path = f.name

try:
    # 初始化检查器
    checker = SQLiteIntegrityChecker("data/db/test_integrity.db")

    # 第一次：计算哈希
    file_hash = checker.compute_sha256(temp_path)
    print(f"文件哈希: {file_hash}")

    # 检查是否应该跳过
    should_skip = checker.should_skip(file_hash)
    print(f"应该跳过: {should_skip}")  # False

    # 标记成功
    checker.mark_success(file_hash, temp_path, "test_collection")

    # 再次检查
    should_skip = checker.should_skip(file_hash)
    print(f"应该跳过: {should_skip}")  # True

    # 列出已处理文件
    records = checker.list_processed("test_collection")
    print(f"已处理记录: {len(records)}")

finally:
    os.unlink(temp_path)
    checker.close()
```

#### 4.2 测试 PDF 加载

```python
from src.libs.loader.pdf_loader import PdfLoader

loader = PdfLoader(extract_images=True)

document = loader.load("data/documents/test.pdf")

print(f"文档ID: {document.id}")
print(f"文本长度: {len(document.text)} 字符")
print(f"图片数量: {len(document.metadata.get('images', []))}")
print(f"\n前500字符预览:\n{document.text[:500]}")

# 查看图片元数据
for img in document.metadata.get('images', []):
    print(f"\n图片: {img['id']}")
    print(f"  路径: {img['path']}")
    print(f"  页码: {img['page']}")
```

#### 4.3 测试文档分块

```python
from src.core.settings import load_settings
from src.ingestion.chunking.document_chunker import DocumentChunker
from src.core.types import Document

settings = load_settings("config/settings.yaml")

# 创建测试文档
doc = Document(
    id="test_doc",
    text="# 第一章\n\n这是第一节的内容。\n\n# 第二章\n\n这是第二节的内容。",
    metadata={"source_path": "test.md"}
)

# 分块
chunker = DocumentChunker(settings)
chunks = chunker.split_document(doc)

print(f"生成 {len(chunks)} 个 chunks:")
for i, chunk in enumerate(chunks):
    print(f"\nChunk {i}:")
    print(f"  索引: {chunk.metadata['chunk_index']}")
    print(f"  内容: {chunk.text[:100]}...")
```

#### 4.4 测试 Transform 阶段

```python
from src.core.settings import load_settings
from src.ingestion.transform.chunk_refiner import ChunkRefiner
from src.ingestion.transform.metadata_enricher import MetadataEnricher
from src.core.types import Chunk

settings = load_settings("config/settings.yaml")

# 创建测试 chunks
chunks = [
    Chunk(
        id="chunk_0",
        text="机器学习是人工智能的一个分支。它使计算机能够从数据中学习。",
        metadata={"source_path": "test.pdf", "chunk_index": 0}
    )
]

# 测试 Refiner
refiner = ChunkRefiner(settings)
refined_chunks = refiner.transform(chunks)
print(f"精炼后: {refined_chunks[0].metadata.get('refined_by')}")

# 测试 Enricher
enricher = MetadataEnricher(settings)
enriched_chunks = enricher.transform(refined_chunks)
print(f"增强后元数据:")
print(f"  标题: {enriched_chunks[0].metadata.get('title')}")
print(f"  摘要: {enriched_chunks[0].metadata.get('summary')}")
print(f"  标签: {enriched_chunks[0].metadata.get('tags')}")
```

#### 4.5 测试编码阶段

```python
from src.core.settings import load_settings
from src.ingestion.embedding.dense_encoder import DenseEncoder
from src.ingestion.embedding.sparse_encoder import SparseEncoder
from src.ingestion.embedding.batch_processor import BatchProcessor
from src.libs.embedding.embedding_factory import EmbeddingFactory
from src.core.types import Chunk

settings = load_settings("config/settings.yaml")

chunks = [
    Chunk(id="c1", text="机器学习是人工智能的一个分支", metadata={}),
    Chunk(id="c2", text="深度学习是机器学习的一种方法", metadata={})
]

# 测试 Dense Encoding
embedding = EmbeddingFactory.create(settings)
dense_encoder = DenseEncoder(embedding, batch_size=2)
dense_vectors = dense_encoder.encode(chunks)
print(f"Dense vectors: {len(dense_vectors)} x {len(dense_vectors[0])}")

# 测试 Sparse Encoding
sparse_encoder = SparseEncoder()
sparse_stats = sparse_encoder.encode(chunks)
print(f"Sparse stats: {len(sparse_stats)}")
print(f"第一个文档的 term frequencies: {list(sparse_stats[0]['term_frequencies'].items())[:5]}")

# 测试 Batch Processor
batch_processor = BatchProcessor(dense_encoder, sparse_encoder, batch_size=2)
result = batch_processor.process(chunks)
print(f"Batch result: {len(result.dense_vectors)} dense, {len(result.sparse_stats)} sparse")
```

#### 4.6 测试存储阶段

```python
from src.core.settings import load_settings
from src.ingestion.storage.vector_upserter import VectorUpserter
from src.ingestion.storage.bm25_indexer import BM25Indexer
from src.core.types import Chunk
import tempfile
import shutil

settings = load_settings("config/settings.yaml")

chunks = [
    Chunk(
        id="temp_chunk",
        text="测试文本",
        metadata={"source_path": "test.pdf", "chunk_index": 0}
    )
]
vectors = [[0.1] * 1536]  # 模拟 1536 维向量

# 测试 Vector Upserter
upserter = VectorUpserter(settings, collection_name="test_collection")
chunk_ids = upserter.upsert(chunks, vectors)
print(f"存储的 chunk IDs: {chunk_ids}")

# 测试 BM25 Indexer
with tempfile.TemporaryDirectory() as tmpdir:
    indexer = BM25Indexer(index_dir=tmpdir)
    sparse_stats = [{
        "doc_length": 4,
        "unique_terms": 2,
        "term_frequencies": {"测试": 1, "文本": 1}
    }]
    indexer.add_documents(sparse_stats, collection="test", doc_id="doc_1")
    print(f"BM25 索引构建完成")
```

---

## 测试场景覆盖

### 场景1：基本功能测试

```python
# test_basic_ingestion.py
"""测试基本摄取功能"""
import pytest
from src.core.settings import load_settings
from src.ingestion.pipeline import IngestionPipeline

class TestBasicIngestion:
    @pytest.fixture
    def settings(self):
        return load_settings("config/settings.yaml")

    def test_single_pdf_ingestion(self, settings):
        """测试单个 PDF 摄取"""
        pipeline = IngestionPipeline(settings, collection="test_basic", force=True)
        try:
            result = pipeline.run("data/documents/test.pdf")

            assert result.success, f"摄取失败: {result.error}"
            assert result.chunk_count > 0, "应该生成至少一个 chunk"
            assert len(result.vector_ids) == result.chunk_count, "向量数应等于 chunk 数"

            # 验证各阶段
            assert "integrity" in result.stages
            assert "loading" in result.stages
            assert "chunking" in result.stages
            assert "transform" in result.stages
            assert "encoding" in result.stages
            assert "storage" in result.stages

            print(f"\n✓ 成功摄取: {result.chunk_count} chunks, {result.image_count} images")
        finally:
            pipeline.close()
```

### 场景2：增量更新测试

```python
# test_incremental.py
"""测试增量更新功能"""
from src.ingestion.pipeline import IngestionPipeline

def test_incremental_skip(settings):
    """测试相同文件被跳过"""
    collection = "test_incremental"

    # 第一次处理
    pipeline1 = IngestionPipeline(settings, collection=collection, force=False)
    try:
        result1 = pipeline1.run("data/documents/test.pdf")
        assert result1.success
        assert result1.chunk_count > 0
    finally:
        pipeline1.close()

    # 第二次处理（应该跳过）
    pipeline2 = IngestionPipeline(settings, collection=collection, force=False)
    try:
        result2 = pipeline2.run("data/documents/test.pdf")
        assert result2.success
        assert result2.stages["integrity"].get("skipped") == True
        print("\n✓ 增量跳过工作正常")
    finally:
        pipeline2.close()

def test_force_reprocess(settings):
    """测试强制重新处理"""
    pipeline = IngestionPipeline(settings, collection="test_incremental", force=True)
    try:
        result = pipeline.run("data/documents/test.pdf")
        assert result.success
        assert result.stages["integrity"].get("skipped") != True
        print("\n✓ 强制重新处理工作正常")
    finally:
        pipeline.close()
```

### 场景3：错误处理测试

```python
# test_error_handling.py
"""测试错误处理"""
import pytest
from src.ingestion.pipeline import IngestionPipeline, PipelineResult

def test_nonexistent_file(settings):
    """测试文件不存在时的处理"""
    pipeline = IngestionPipeline(settings, collection="test_error")
    try:
        result = pipeline.run("data/documents/nonexistent.pdf")
        assert not result.success
        assert "No such file" in result.error or "not found" in result.error.lower()
        print(f"\n✓ 正确处理文件不存在: {result.error}")
    finally:
        pipeline.close()

def test_invalid_file(settings):
    """测试无效文件的处理"""
    import tempfile
    import os

    # 创建一个假的 PDF 文件
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
        f.write(b"not a valid pdf content")
        temp_path = f.name

    pipeline = IngestionPipeline(settings, collection="test_error")
    try:
        result = pipeline.run(temp_path)
        # 应该失败或优雅处理
        print(f"\n✓ 无效文件处理结果: success={result.success}")
    finally:
        pipeline.close()
        os.unlink(temp_path)
```

### 场景4：性能测试

```python
# test_performance.py
"""测试性能"""
import time
from src.ingestion.pipeline import IngestionPipeline

def test_ingestion_performance(settings):
    """测试摄取性能"""
    pipeline = IngestionPipeline(settings, collection="test_perf", force=True)

    start_time = time.time()
    try:
        result = pipeline.run("data/documents/test.pdf")
        elapsed = time.time() - start_time

        if result.success:
            print(f"\n性能指标:")
            print(f"  总耗时: {elapsed:.2f}s")
            print(f"  Chunks: {result.chunk_count}")
            print(f"  每 chunk 耗时: {elapsed/result.chunk_count:.2f}s")

            # 各阶段耗时（如果有 trace）
            for stage_name, stage_data in result.stages.items():
                print(f"  {stage_name}: {stage_data}")
    finally:
        pipeline.close()
```

### 场景5：DocumentManager 测试

```python
# test_document_manager.py
"""测试文档管理功能"""
from src.ingestion.document_manager import DocumentManager
from src.libs.vector_store.chroma_store import ChromaStore
from src.ingestion.storage.bm25_indexer import BM25Indexer
from src.ingestion.storage.image_storage import ImageStorage
from src.libs.loader.file_integrity import SQLiteIntegrityChecker

def test_document_lifecycle(settings):
    """测试文档完整生命周期"""

    # 初始化各组件
    chroma = ChromaStore(
        persist_directory="data/db/chroma",
        collection_name="test_lifecycle"
    )
    bm25 = BM25Indexer(index_dir="data/db/bm25/test_lifecycle")
    image_storage = ImageStorage(
        db_path="data/db/test_image_index.db",
        images_root="data/images"
    )
    integrity = SQLiteIntegrityChecker("data/db/test_ingestion.db")

    # 创建 DocumentManager
    doc_manager = DocumentManager(chroma, bm25, image_storage, integrity)

    # 1. 列出文档
    docs = doc_manager.list_documents("test_lifecycle")
    print(f"\n当前文档数: {len(docs)}")

    # 2. 获取集合统计
    stats = doc_manager.get_collection_stats("test_lifecycle")
    print(f"统计: {stats.document_count} docs, {stats.chunk_count} chunks")

    # 3. 如果有文档，测试详情和删除
    if docs:
        doc = docs[0]
        print(f"\n测试文档: {doc.source_path}")

        # 获取详情
        detail = doc_manager.get_document_detail(doc.source_hash)
        print(f"详情: {len(detail.chunk_ids)} chunks, {len(detail.image_ids)} images")

        # 删除文档（谨慎！）
        # result = doc_manager.delete_document(doc.source_path, "test_lifecycle")
        # print(f"删除结果: {result}")
```

---

## 常见问题排查

### 问题1：API 密钥错误

```
Error: Authentication failed
```

**解决**：
```bash
# 检查环境变量
echo $AZURE_API_KEY
echo $AZURE_ENDPOINT

# 或检查 .env 文件
cat .env

# 测试连接
python -c "
from src.core.settings import load_settings
from src.libs.llm.llm_factory import LLMFactory
settings = load_settings()
llm = LLMFactory.create(settings)
print('连接成功')
"
```

### 问题2：MarkItDown 未安装

```
ImportError: MarkItDown is required for PdfLoader
```

**解决**：
```bash
pip install markitdown
```

### 问题3：PyMuPDF 未安装（图片提取失败）

```
Warning: PyMuPDF not available, skipping image extraction
```

**解决**：
```bash
pip install pymupdf
```

### 问题4：数据库锁定

```
sqlite3.OperationalError: database is locked
```

**解决**：
```python
# 检查是否有其他进程占用
# 删除锁文件（谨慎）
rm data/db/ingestion_history.db-journal

# 或等待其他进程完成
```

### 问题5：内存不足

```
MemoryError
```

**解决**：
```python
# 减小批处理大小
settings.ingestion.batch_size = 50  # 默认 100

# 或减小 chunk_size
settings.ingestion.chunk_size = 300  # 默认 500
```

---

## 测试检查清单

| 检查项 | 命令/方法 | 预期结果 |
|--------|-----------|----------|
| 依赖安装 | `pip install -r requirements.txt` | 无错误 |
| 配置加载 | `load_settings()` | 返回 Settings 对象 |
| 文件完整性 | `SQLiteIntegrityChecker` | 哈希计算正确，跳过逻辑正常 |
| PDF 加载 | `PdfLoader.load()` | 返回 Document，包含 text 和 metadata |
| 分块 | `DocumentChunker.split()` | 生成合理数量的 chunks |
| Transform | `ChunkRefiner.transform()` | chunks 被标记 refined_by |
| Dense 编码 | `DenseEncoder.encode()` | 返回正确维度的向量 |
| Sparse 编码 | `SparseEncoder.encode()` | 返回 term frequencies |
| 向量存储 | `VectorUpserter.upsert()` | 返回 chunk_ids |
| BM25 索引 | `BM25Indexer.add_documents()` | 索引文件生成 |
| 完整流水线 | `IngestionPipeline.run()` | success=True，各阶段正常 |
| 增量更新 | 第二次运行 | 自动跳过 |
| 强制重处理 | `force=True` | 重新处理 |
| DocumentManager | `list/delete/get` | 操作正常 |

---

**文档版本**: v1.0
**最后更新**: 2026-04-07

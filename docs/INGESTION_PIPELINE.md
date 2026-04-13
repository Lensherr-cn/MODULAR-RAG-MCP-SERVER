# 数据摄取流水线文档

> 本文档详细描述 Modular RAG MCP Server 的数据摄取流水线架构与实现细节。
>
> 适用范围：仅 PDF 文档格式

---

## 目录

1. [架构概览](#架构概览)
2. [流水线阶段详解](#流水线阶段详解)
3. [核心组件说明](#核心组件说明)
4. [数据流图](#数据流图)
5. [配置说明](#配置说明)
6. [使用方式](#使用方式)
7. [可观测性](#可观测性)

---

## 架构概览

### 设计原则

| 原则 | 说明 |
|------|------|
| **Config-Driven** | 所有组件通过 `settings.yaml` 配置 |
| **Observable** | 全链路追踪，记录各阶段耗时与详情 |
| **Graceful Degradation** | LLM 失败不阻塞流水线 |
| **Idempotent** | 基于 SHA256 的增量更新，重复处理安全 |

### 6 阶段流水线

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Ingestion Pipeline                                   │
├─────────────┬─────────────┬─────────────┬─────────────┬─────────────┬───────┤
│   Stage 1   │   Stage 2   │   Stage 3   │   Stage 4   │   Stage 5   │Stage 6│
│  Integrity  │    Load     │   Chunking  │  Transform  │   Encode    │ Store │
│    Check    │   (PDF→MD)  │   (Split)   │  (Enhance)  │  (Vectors)  │(Index)│
├─────────────┼─────────────┼─────────────┼─────────────┼─────────────┼───────┤
│  SHA256     │  MarkItDown │  Recursive  │  Refiner    │   Dense     │Chroma │
│  哈希检查    │  PDF解析    │  分块策略    │  Enricher   │  + Sparse   │ BM25  │
│  增量跳过    │  图片提取    │  语义切分    │  Captioner  │  双路编码    │ Image │
└─────────────┴─────────────┴─────────────┴─────────────┴─────────────┴───────┘
```

### 核心数据类型

```python
# Document: Loader 输出
document = Document(
    id="doc_abc123...",
    text="# Markdown Content\n...",  # 规范化 Markdown
    metadata={
        "source_path": "/path/to/file.pdf",
        "doc_type": "pdf",
        "doc_hash": "abc123...",
        "title": "Document Title",
        "images": [...]  # 图片元数据列表
    }
)

# Chunk: Splitter 输出
chunk = Chunk(
    id="temp_chunk_0",
    text="chunk content...",
    metadata={
        "source_path": "/path/to/file.pdf",
        "chunk_index": 0,
        "start_offset": 0,
        "end_offset": 500,
        # Transform 阶段注入的增强字段
        "title": "Section Title",
        "summary": "Brief summary...",
        "tags": ["tag1", "tag2"],
        "refined_by": "llm",
        "enriched_by": "llm"
    }
)
```

---

## 流水线阶段详解

### Stage 1: File Integrity Check（文件完整性检查）

**目的**：避免重复处理未变更的文件，实现零成本增量更新。

**实现**：`src/libs/loader/file_integrity.py`

```python
# 流程
1. 计算文件 SHA256 哈希
   └── 使用 64KB 分块读取，支持大文件

2. 查询 SQLite 数据库
   └── SELECT status FROM ingestion_history WHERE file_hash = ?

3. 决策
   ├── status = 'success' → 跳过（零成本）
   └── status = 'failed' 或不存在 → 继续处理

4. 处理完成后更新记录
   └── INSERT/UPDATE ingestion_history
```

**数据库表结构**：

```sql
CREATE TABLE ingestion_history (
    file_hash TEXT PRIMARY KEY,      -- SHA256 哈希 (64字符)
    file_path TEXT NOT NULL,          -- 原始文件路径
    status TEXT NOT NULL,             -- 'success' | 'failed'
    collection TEXT,                  -- 所属集合
    error_msg TEXT,                   -- 失败时记录错误
    processed_at TEXT NOT NULL,       -- 首次处理时间
    updated_at TEXT NOT NULL          -- 最后更新时间
);
```

**关键特性**：
- WAL 模式支持并发读写
- `force=True` 参数可强制重新处理
- 失败文件可重试（不会被跳过）

---

### Stage 2: Document Loading（文档加载）

**目的**：将 PDF 解析为规范化 Markdown 格式，提取图片。

**实现**：`src/libs/loader/pdf_loader.py`

**技术栈**：
- **MarkItDown**: 微软开源的 PDF → Markdown 转换器
- **PyMuPDF (fitz)**: 图片提取

**处理流程**：

```
PDF File
    │
    ▼
┌─────────────────┐
│  MarkItDown     │ ──→ Markdown 文本
│  .convert()     │
└─────────────────┘
    │
    ▼
┌─────────────────┐
│  PyMuPDF        │ ──→ 提取图片保存到磁盘
│  遍历每页图片    │ ──→ 在文本中插入 [IMAGE: {id}] 占位符
└─────────────────┘
    │
    ▼
Document(text=markdown, metadata={images: [...]})
```

**图片存储结构**：

```
data/images/
└── {collection}/
    └── {doc_hash[:16]}/
        ├── {doc_hash[:8]}_1_1.png   # 第1页第1张图
        ├── {doc_hash[:8]}_1_2.png   # 第1页第2张图
        └── {doc_hash[:8]}_2_1.png   # 第2页第1张图
```

**图片元数据**：

```python
{
    "id": "abc123_1_1",
    "path": "data/images/default/abc123.../abc123_1_1.png",
    "page": 1,
    "text_offset": 1520,      # 占位符在文本中的位置
    "text_length": 20,        # 占位符长度
    "position": {
        "width": 800,
        "height": 600,
        "page": 1,
        "index": 0
    }
}
```

**优雅降级**：
- 图片提取失败 → 继续处理纯文本
- 记录警告日志，不中断流程

---

### Stage 3: Document Chunking（文档分块）

**目的**：将长文档切分为语义完整的片段（Chunks）。

**实现**：`src/ingestion/chunking/document_chunker.py`

**技术选型**：LangChain `RecursiveCharacterTextSplitter`

**为什么选择递归分块？**

```
传统定长分块的问题：
"...关于机器学习的应|用场景包括..."
            ↑
         语义断裂！

递归分块策略（按优先级尝试）：
1. 首先尝试按 Markdown 标题分割 (# ## ###)
2. 然后尝试按段落分割 (\n\n)
3. 然后尝试按句子分割 (.!?)
4. 最后按字符数硬性分割

结果：每个 Chunk 保持语义完整性
```

**配置参数**（`settings.yaml`）：

```yaml
ingestion:
  chunk_size: 500        # 目标块大小（字符数）
  chunk_overlap: 50      # 相邻块重叠字符数
```

**分块输出示例**：

```markdown
# 原文档
## 第一章 概述
机器学习是人工智能的一个分支...

## 第二章 算法
常见的机器学习算法包括...

# 分块结果
Chunk 0: "## 第一章 概述\n\n机器学习是人工智能的一个分支..."
Chunk 1: "## 第二章 算法\n\n常见的机器学习算法包括..."
```

**元数据继承**：
- `source_path`: 源文件路径
- `chunk_index`: 块序号（0-based）
- `start_offset`/`end_offset`: 在原文档中的字符位置

---

### Stage 4: Transform Pipeline（转换增强）

**目的**：通过 LLM 增强 Chunk 的语义质量和检索友好性。

**实现**：`src/ingestion/transform/`

包含三个子阶段，顺序执行：

#### 4a. Chunk Refiner（块精炼）

**文件**：`chunk_refiner.py`

**作用**：
- 合并被物理切断的逻辑相关段落
- 去除页眉页脚、乱码等噪声
- 确保每个 Chunk 是自包含的语义单元

**两种模式**：

| 模式 | 说明 | 触发条件 |
|------|------|----------|
| **LLM 精炼** | 使用 GPT-4o 等模型智能重组 | `use_llm: true` 且 API 可用 |
| **规则精炼** | 基于正则的启发式清理 | LLM 失败或 `use_llm: false` |

**LLM Prompt 示例**：

```
你是一个文档优化助手。请优化以下文本片段：
1. 合并在逻辑上紧密相关但被切断的段落
2. 删除页眉、页脚、页码等无关内容
3. 修正明显的 OCR 错误
4. 保持原始含义不变

原文：
{chunk_text}

优化后的文本：
```

#### 4b. Metadata Enricher（元数据增强）

**文件**：`metadata_enricher.py`

**作用**：为每个 Chunk 自动生成高维语义特征。

**生成字段**：

| 字段 | 说明 | 用途 |
|------|------|------|
| `title` | 精准小标题 | 检索时快速判断相关性 |
| `summary` | 内容摘要（1-2句） | 快速预览，不读全文 |
| `tags` | 主题标签列表 | 分类筛选、聚合 |
| `category` | 内容分类 | 权限控制、路由 |

**LLM Prompt 示例**：

```
分析以下文本片段，提取元数据：

文本：
{chunk_text}

请输出 JSON 格式：
{
  "title": "5-10字的精准标题",
  "summary": "20-50字的内容摘要",
  "tags": ["标签1", "标签2", "标签3"],
  "category": "所属分类"
}
```

#### 4c. Image Captioner（图片描述）

**文件**：`image_captioner.py`

**作用**：使用 Vision LLM 为图片生成文本描述。

**处理流程**：

```
Chunk 包含 [IMAGE: abc123_1_1]
    │
    ▼
查找对应图片文件
    │
    ▼
调用 Vision LLM (GPT-4o)
    │
    ▼
生成描述："该图展示了系统架构，包含三个主要模块..."
    │
    ▼
将描述追加到 Chunk.text
    │
    ▼
Chunk.metadata.image_captions = [{"image_id": "...", "caption": "..."}]
```

**优势**：
- 图片内容可被文本检索命中
- 无需多模态向量，复用现有架构

**优雅降级**：
- Vision LLM 不可用时，保留占位符
- 记录警告，继续处理

---

### Stage 5: Encoding（向量编码）

**目的**：将文本转换为向量表示，支持语义检索。

**实现**：`src/ingestion/embedding/`

**双路编码策略**（Hybrid Search 基础）：

```
┌─────────────────────────────────────────────────────────────┐
│                      Encoding Pipeline                       │
├──────────────────────────┬──────────────────────────────────┤
│     Dense Encoding       │        Sparse Encoding           │
│    (语义向量)             │         (关键词向量)              │
├──────────────────────────┼──────────────────────────────────┤
│  Embedding Model         │  BM25 Algorithm                  │
│  (text-embedding-ada-002)│                                  │
│                          │  - Tokenization                  │
│  输入: chunk.text        │  - Term Frequency                │
│  输出: 1536-dim vector   │  - IDF Calculation               │
│                          │  - Document Length               │
│  特点:                   │                                  │
│  - 捕捉语义相似性         │  输出:                           │
│  - "汽车" ≈ "车辆"        │  {term: weight, ...}             │
│                          │                                  │
│  适用: 同义词、语义理解   │  特点:                           │
│                          │  - 精确关键词匹配                 │
│                          │  - 专有名词查找                   │
│                          │                                  │
│                          │  适用: 产品名、ID、术语           │
└──────────────────────────┴──────────────────────────────────┘
```

#### Dense Encoder

**文件**：`dense_encoder.py`

```python
# 流程
chunks.text → Embedding API → List[List[float]]

# 批处理优化
batch_size = 100  # 可配置
for batch in chunks.batch(batch_size):
    vectors = embedding.embed(batch.texts)
```

#### Sparse Encoder

**文件**：`sparse_encoder.py`

```python
# 流程
chunks.text → BM25Encoder → List[Dict[str, float]]

# 输出示例
{
    "machine": 2.5,      # TF-IDF 权重
    "learning": 2.3,
    "algorithm": 1.8,
    ...
}
```

#### Batch Processor

**文件**：`batch_processor.py`

**作用**：协调 Dense + Sparse 编码，统一批处理。

```python
result = batch_processor.process(chunks)

result.dense_vectors  # List[List[float]]
result.sparse_stats   # List[Dict] 包含 term_frequencies, doc_length 等
```

---

### Stage 6: Storage（存储索引）

**目的**：将向量、元数据、索引持久化到存储系统。

**实现**：`src/ingestion/storage/`

三个存储后端同时写入：

```
                    ┌─────────────────┐
                    │   Chunks +      │
                    │   Dense Vectors │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌───────────────┐   ┌─────────────────┐   ┌─────────────────┐
│   ChromaDB    │   │   BM25 Index    │   │  ImageStorage   │
│  (向量数据库)  │   │  (稀疏索引)      │   │  (图片索引)      │
├───────────────┤   ├─────────────────┤   ├─────────────────┤
│ - Vector      │   │ - Inverted Index│   │ - SQLite Index  │
│ - Metadata    │   │ - IDF Stats     │   │ - File System   │
│ - Text        │   │ - Document Map  │   │                 │
└───────────────┘   └─────────────────┘   └─────────────────┘
```

#### 6a. Vector Upserter → ChromaDB

**文件**：`vector_upserter.py`

**Chunk ID 生成策略**（幂等保证）：

```python
chunk_id = f"{source_hash}_{chunk_index:04d}_{content_hash}"

# 示例: "a1b2c3d4_0000_e5f6g7h8"
# - a1b2c3d4: 源文件路径哈希（前8位）
# - 0000: 块序号（4位，补零）
# - e5f6g7h8: 内容哈希（前8位）
```

**存储记录结构**：

```python
{
    "id": "a1b2c3d4_0000_e5f6g7h8",
    "vector": [0.1, 0.2, 0.3, ...],  # 1536-dim
    "metadata": {
        # 原始元数据
        "source_path": "/path/to/file.pdf",
        "chunk_index": 0,
        "doc_hash": "abc123...",
        # Transform 注入
        "title": "Section Title",
        "summary": "Brief summary...",
        "tags": ["tag1", "tag2"],
        # 检索必需
        "text": "完整文本内容"
    }
}
```

#### 6b. BM25 Indexer

**文件**：`bm25_indexer.py`

**索引结构**：

```
data/db/bm25/{collection}/
├── index.pkl          # 倒排索引 {term: {doc_id: tf}}
├── idf.pkl            # IDF 统计 {term: idf_score}
├── doc_lengths.pkl    # 文档长度 {doc_id: length}
└── avgdl              # 平均文档长度（浮点数）
```

#### 6c. Image Storage

**文件**：`image_storage.py`

**SQLite 索引表**：

```sql
CREATE TABLE image_index (
    image_id TEXT PRIMARY KEY,
    file_path TEXT NOT NULL,
    collection TEXT,
    doc_hash TEXT,
    page_num INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 核心组件说明

### 类图

```
┌─────────────────────────────────────────────────────────────────┐
│                      IngestionPipeline                          │
├─────────────────────────────────────────────────────────────────┤
│ - settings: Settings                                            │
│ - collection: str                                               │
│ - force: bool                                                   │
├─────────────────────────────────────────────────────────────────┤
│ + run(file_path, trace, on_progress) -> PipelineResult          │
│ + close()                                                       │
├─────────────────────────────────────────────────────────────────┤
│ Components:                                                     │
│   integrity_checker: SQLiteIntegrityChecker                     │
│   loader: PdfLoader                                             │
│   chunker: DocumentChunker                                      │
│   chunk_refiner: ChunkRefiner                                   │
│   metadata_enricher: MetadataEnricher                           │
│   image_captioner: ImageCaptioner                               │
│   dense_encoder: DenseEncoder                                   │
│   sparse_encoder: SparseEncoder                                 │
│   batch_processor: BatchProcessor                               │
│   vector_upserter: VectorUpserter                               │
│   bm25_indexer: BM25Indexer                                     │
│   image_storage: ImageStorage                                   │
└─────────────────────────────────────────────────────────────────┘
```

### DocumentManager（文档生命周期管理）

**文件**：`src/ingestion/document_manager.py`

**职责**：跨存储的文档管理操作

```python
# 列出已摄取文档
docs = document_manager.list_documents(collection="default")
# [DocumentInfo(source_path=..., source_hash=..., chunk_count=10, ...), ...]

# 获取文档详情
detail = document_manager.get_document_detail(doc_id="abc123...")
# DocumentDetail(chunk_ids=[...], image_ids=[...], ...)

# 删除文档（级联删除所有存储）
result = document_manager.delete_document(
    source_path="/path/to/file.pdf",
    collection="default"
)
# DeleteResult(chunks_deleted=10, bm25_removed=True, images_deleted=5, ...)

# 集合统计
stats = document_manager.get_collection_stats(collection="default")
# CollectionStats(document_count=5, chunk_count=150, image_count=20)
```

---

## 数据流图

### 完整数据流

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  PDF File   │────▶│  SHA256     │────▶│  Check DB   │
│  (Input)    │     │   Hash      │     │  (Skip?)    │
└─────────────┘     └─────────────┘     └──────┬──────┘
                                               │
                              Already processed│
                              ─────────────────┘
                              Skip (Zero Cost)
                                               │
                              New/Changed      ▼
                                               │
                                               ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Document   │◀────│  MarkItDown │◀────│   PyMuPDF   │
│  (Markdown) │     │  Text Extraction    │  Images     │
└──────┬──────┘     └─────────────┘     └─────────────┘
       │
       ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Chunks    │────▶│  Refiner    │────▶│  Enricher   │
│  (Split)    │     │  (LLM/Rule) │     │ (Metadata)  │
└─────────────┘     └─────────────┘     └──────┬──────┘
                                                │
                                                ▼
                                       ┌─────────────┐
                                       │  Captioner  │
                                       │ (Vision)    │
                                       └──────┬──────┘
                                              │
       ┌──────────────────────────────────────┘
       │
       ▼
┌─────────────┐     ┌─────────────┐
│   Dense     │     │   Sparse    │
│  Embedding  │     │   BM25      │
└──────┬──────┘     └──────┬──────┘
       │                   │
       └─────────┬─────────┘
                 │
                 ▼
       ┌─────────────────┐
       │  Batch Processor │
       └────────┬────────┘
                │
    ┌───────────┼───────────┐
    │           │           │
    ▼           ▼           ▼
┌────────┐ ┌────────┐ ┌────────┐
│ Chroma │ │  BM25  │ │ Image  │
│  DB    │ │ Index  │ │ Store  │
└────────┘ └────────┘ └────────┘
    │           │           │
    └───────────┴───────────┘
                │
                ▼
       ┌─────────────────┐
       │  Mark Success   │
       │  (SQLite Record)│
       └─────────────────┘
```

---

## 配置说明

### 完整配置示例

```yaml
# config/settings.yaml

# LLM 配置（用于 Transform 阶段）
llm:
  provider: "azure"           # azure | openai | deepseek | ollama
  model: "gpt-4o"
  api_key: "${AZURE_API_KEY}"
  endpoint: "${AZURE_ENDPOINT}"
  deployment_name: "gpt-4o"
  temperature: 0.0
  max_tokens: 4096

# Vision LLM 配置（用于 Image Captioning）
vision_llm:
  enabled: true
  provider: "azure"
  model: "gpt-4o"
  api_key: "${AZURE_API_KEY}"
  endpoint: "${AZURE_ENDPOINT}"
  deployment_name: "gpt-4o"

# Embedding 配置（用于 Dense Encoding）
embedding:
  provider: "azure"
  model: "text-embedding-ada-002"
  api_key: "${AZURE_API_KEY}"
  endpoint: "${AZURE_ENDPOINT}"
  deployment_name: "text-embedding-ada-002"
  dimensions: 1536

# 向量存储配置
vector_store:
  provider: "chroma"
  persist_directory: "./data/db/chroma"
  collection_name: "default"

# 摄取流水线配置
ingestion:
  chunk_size: 500             # 分块大小（字符）
  chunk_overlap: 50           # 重叠大小
  batch_size: 100             # 批处理大小

  chunk_refiner:
    use_llm: true             # 是否使用 LLM 精炼
    model: "gpt-4o"           # 可选：指定不同模型
    temperature: 0.0

  metadata_enricher:
    use_llm: true             # 是否使用 LLM 增强元数据
    model: "gpt-4o"
    temperature: 0.0

  image_captioner:
    enabled: true             # 是否生成图片描述
    model: "gpt-4o"           # Vision 模型
```

---

## 使用方式

### 命令行工具

```bash
# 摄取单个文件
python scripts/ingest.py --path documents/report.pdf --collection contracts

# 摄取整个目录
python scripts/ingest.py --path documents/ --collection technical_docs

# 强制重新处理
python scripts/ingest.py --path documents/report.pdf --collection contracts --force

# 使用自定义配置
python scripts/ingest.py --path documents/ --config custom_settings.yaml

# 详细输出
python scripts/ingest.py --path documents/ --verbose

# 干运行（只列出会处理的文件）
python scripts/ingest.py --path documents/ --dry-run
```

### Python API

```python
from src.core.settings import load_settings
from src.ingestion.pipeline import IngestionPipeline

# 加载配置
settings = load_settings("config/settings.yaml")

# 创建流水线
pipeline = IngestionPipeline(
    settings=settings,
    collection="my_collection",
    force=False  # 增量模式
)

# 处理文件
try:
    result = pipeline.run("documents/report.pdf")

    if result.success:
        print(f"✅ 成功: {result.chunk_count} chunks, {result.image_count} images")
        print(f"   文档ID: {result.doc_id}")
        print(f"   向量ID: {result.vector_ids[:3]}...")
    else:
        print(f"❌ 失败: {result.error}")
finally:
    pipeline.close()
```

### 带进度回调

```python
def on_progress(stage_name: str, current: int, total: int):
    """阶段完成回调"""
    print(f"[{current}/{total}] {stage_name} 完成")

result = pipeline.run(
    "documents/report.pdf",
    on_progress=on_progress
)
# 输出:
# [1/6] integrity 完成
# [2/6] load 完成
# [3/6] split 完成
# ...
```

### 带追踪

```python
from src.core.trace import TraceContext

# 创建追踪上下文
trace = TraceContext(trace_type="ingestion")
trace.metadata["source_path"] = "documents/report.pdf"

# 处理
result = pipeline.run("documents/report.pdf", trace=trace)

# 查看追踪记录
print(trace.to_dict())
# {
#   "trace_id": "...",
#   "trace_type": "ingestion",
#   "stages": [
#     {"name": "load", "elapsed_ms": 1234, "input": {...}, "output": {...}},
#     {"name": "split", "elapsed_ms": 56, "input": {...}, "output": {...}},
#     ...
#   ]
# }
```

---

## 可观测性

### 日志输出示例

```
============================================================
Starting Ingestion Pipeline for: documents/report.pdf
Collection: default
============================================================

📋 Stage 1: File Integrity Check
  File hash: a1b2c3d4...
  ✓ File needs processing

📄 Stage 2: Document Loading
  Document ID: doc_a1b2c3d4...
  Text length: 15234 chars
  Images extracted: 5
  Preview: # 技术文档\n\n## 概述\n本文档描述...

✂️ Stage 3: Document Chunking
  Chunks generated: 32
  First chunk ID: temp_chunk_0
  First chunk preview: ## 概述\n本文档描述...

🔄 Stage 4: Transform Pipeline
  4a. Chunk Refinement...
      LLM refined: 30, Rule refined: 2
  4b. Metadata Enrichment...
      LLM enriched: 32, Rule enriched: 0
  4c. Image Captioning...
      Chunks with captions: 3

🔢 Stage 5: Encoding
  Dense vectors: 32 (dim=1536)
  Sparse stats: 32 documents

💾 Stage 6: Storage
  6a. Vector Storage (ChromaDB)...
      Stored 32 vectors
  6b. BM25 Index...
      Index built for 32 documents
  6c. Image Storage Index...
      Indexed 5 images

============================================================
✅ Pipeline completed successfully!
   Chunks: 32
   Vectors: 32
   Images: 5
============================================================
```

### PipelineResult 结构

```python
PipelineResult(
    success=True,
    file_path="documents/report.pdf",
    doc_id="a1b2c3d4...",           # SHA256 哈希
    chunk_count=32,
    image_count=5,
    vector_ids=["a1b2_0000_e5f6", ...],
    stages={
        "integrity": {
            "file_hash": "a1b2c3d4...",
            "skipped": False
        },
        "loading": {
            "doc_id": "doc_a1b2c3d4...",
            "text_length": 15234,
            "image_count": 5
        },
        "chunking": {
            "chunk_count": 32,
            "avg_chunk_size": 476
        },
        "transform": {
            "chunk_refiner": {"llm": 30, "rule": 2},
            "metadata_enricher": {"llm": 32, "rule": 0},
            "image_captioner": {"captioned_chunks": 3}
        },
        "encoding": {
            "dense_vector_count": 32,
            "dense_dimension": 1536,
            "sparse_doc_count": 32
        },
        "storage": {
            "vector_count": 32,
            "bm25_docs": 32,
            "images_indexed": 5
        }
    }
)
```

---

## 性能指标参考

| 阶段 | 典型耗时 | 主要影响因素 |
|------|----------|--------------|
| Integrity Check | < 100ms | 文件大小（哈希计算） |
| Document Loading | 1-5s | PDF 页数、图片数量 |
| Chunking | < 500ms | 文档长度 |
| Transform (LLM) | 5-30s | Chunk 数量、LLM 响应速度 |
| Transform (Rule) | < 1s | Chunk 数量 |
| Dense Encoding | 2-10s | Chunk 数量、Embedding API |
| Sparse Encoding | < 500ms | Chunk 数量 |
| Storage | 1-3s | 向量维度、索引大小 |

**总计**：单文档约 **10-50 秒**（取决于 LLM 和 Embedding API 速度）

---

## 错误处理

| 错误场景 | 处理方式 | 结果 |
|----------|----------|------|
| 文件不存在 | 抛出 FileNotFoundError | 处理失败 |
| 哈希计算失败 | 抛出 IOError | 处理失败 |
| PDF 解析失败 | 抛出 RuntimeError | 处理失败 |
| LLM 调用失败 | 降级到 Rule 模式 | 继续处理 |
| Vision LLM 失败 | 跳过图片描述 | 继续处理 |
| Embedding 失败 | 抛出 RuntimeError | 处理失败 |
| 存储失败 | 抛出 RuntimeError | 处理失败 |

---

## 文件清单

```
src/
├── ingestion/
│   ├── pipeline.py                 # 主流水线编排器
│   ├── document_manager.py         # 文档生命周期管理
│   ├── chunking/
│   │   └── document_chunker.py     # 文档分块
│   ├── transform/
│   │   ├── chunk_refiner.py        # Chunk 精炼
│   │   ├── metadata_enricher.py    # 元数据增强
│   │   └── image_captioner.py      # 图片描述
│   ├── embedding/
│   │   ├── dense_encoder.py        # Dense 编码
│   │   ├── sparse_encoder.py       # Sparse 编码
│   │   └── batch_processor.py      # 批处理协调
│   └── storage/
│       ├── vector_upserter.py      # 向量存储
│       ├── bm25_indexer.py         # BM25 索引
│       └── image_storage.py        # 图片存储
├── libs/
│   └── loader/
│       ├── base_loader.py          # Loader 基类
│       ├── pdf_loader.py           # PDF 加载器
│       └── file_integrity.py       # 文件完整性检查
└── core/
    └── types.py                    # Document, Chunk 类型定义

scripts/
└── ingest.py                       # 摄取脚本 CLI

tests/
├── integration/
│   └── test_ingestion_pipeline.py  # 集成测试
└── unit/
    ├── test_document_chunker.py
    ├── test_chunk_refiner.py
    └── test_metadata_enricher_contract.py
```

---

**文档版本**: v1.0
**最后更新**: 2026-04-07
**适用范围**: Modular RAG MCP Server v0.1+

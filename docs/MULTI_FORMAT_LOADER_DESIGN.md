# 多格式文档加载器设计文档

## 1. 背景

### 1.1 问题描述

原有的摄入管道 (`src/ingestion/pipeline.py`) 仅支持 PDF 文件，原因如下：

1. **硬编码的 PdfLoader**：`IngestionPipeline.__init__()` 中直接实例化 `PdfLoader`
2. **扩展名检查**：`PdfLoader.load()` 方法中硬编码检查 `.pdf` 扩展名
3. **缺少其他格式支持**：无法处理 `.md`、`.txt`、`.docx`、`.xlsx` 等常见文档格式

```python
# 原有代码 (pipeline.py 第 145-149 行)
self.loader = PdfLoader(
    extract_images=True,
    image_storage_dir=str(resolve_path(f"data/images/{collection}"))
)
```

### 1.2 需求

扩展摄入管道支持以下格式：
- `.md` / `.markdown` - Markdown 文档
- `.txt` - 纯文本文件
- `.docx` / `.doc` - Word 文档
- `.xlsx` / `.xls` - Excel 表格

---

## 2. 设计目标

1. **开闭原则**：新增格式无需修改现有代码，只需添加新的 Loader 类
2. **一致性**：所有 Loader 遵循相同的接口规范 (`BaseLoader`)
3. **可扩展**：通过工厂模式统一管理 Loader 的创建
4. **向后兼容**：不影响现有 PDF 处理功能
5. **优雅降级**：可选依赖缺失时给出明确警告，而非崩溃

---

## 3. 架构设计

### 3.1 整体架构

采用 **工厂模式 (Factory Pattern)** 设计，与项目中已有的 `EmbeddingFactory`、`VectorStoreFactory` 保持一致。

```
┌─────────────────────────────────────────────────────────────┐
│                    IngestionPipeline                        │
│                                                             │
│  run(file_path) ──────► LoaderFactory.create(file_path)    │
│                                    │                        │
│                                    ▼                        │
│                         ┌─────────────────┐                │
│                         │  BaseLoader     │                │
│                         │  (抽象基类)      │                │
│                         └────────┬────────┘                │
│                                  │                          │
│          ┌───────────┬───────────┼───────────┬──────────┐  │
│          ▼           ▼           ▼           ▼          ▼  │
│     PdfLoader  MarkdownLoader TextLoader WordLoader ExcelLoader
│                                                                  │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 文件结构

```
src/libs/loader/
├── __init__.py          # 模块导出 (更新)
├── base_loader.py       # 抽象基类 (无修改)
├── pdf_loader.py        # PDF 加载器 (无修改)
├── markdown_loader.py   # Markdown 加载器 (新增)
├── text_loader.py       # 纯文本加载器 (新增)
├── word_loader.py       # Word 加载器 (新增)
├── excel_loader.py      # Excel 加载器 (新增)
├── loader_factory.py    # 工厂类 (新增)
└── file_integrity.py    # 文件完整性检查 (无修改)
```

---

## 4. 详细设计

### 4.1 LoaderFactory (新增)

**文件**: `src/libs/loader/loader_factory.py`

**设计理由**:
- 集中管理 Loader 的创建逻辑
- 根据文件扩展名自动选择合适的 Loader
- 支持动态注册新的 Loader（开闭原则）
- 延迟导入（Lazy Import）避免循环依赖

**核心代码**:
```python
class LoaderFactory:
    # 扩展名到 Loader 名称的映射
    _EXTENSION_MAP: dict[str, str] = {
        ".pdf": "pdf",
        ".md": "markdown",
        ".markdown": "markdown",
        ".txt": "text",
        ".docx": "word",
        ".doc": "word",
        ".xlsx": "excel",
        ".xls": "excel",
    }

    @classmethod
    def create(cls, file_path: str | Path, **kwargs) -> BaseLoader:
        """根据文件扩展名创建对应的 Loader"""
        loader_name = cls.get_loader_name(file_path)
        # 延迟导入，避免循环依赖
        cls._register_loader(loader_name)
        loader_class = cls._LOADERS[loader_name]
        return loader_class(**kwargs)
```

**为什么使用延迟导入**:
- 避免 `word_loader.py` 导入失败时影响其他 Loader
- 减少启动时的加载时间
- 可选依赖缺失时只影响对应的 Loader

---

### 4.2 MarkdownLoader (新增)

**文件**: `src/libs/loader/markdown_loader.py`

**设计决策**:

| 决策 | 理由 |
|------|------|
| **保留 Markdown 格式** | Markdown 标记（如 `#`、`**`、`[]`）提供结构信息，对 RAG 检索有帮助 |
| **提取标题** | 从第一个 `# ` 标题提取文档标题，用于元数据 |
| **解析章节** | 按标题层级解析文档结构，记录在 `metadata.sections` 中 |
| **SHA256 哈希** | 使用文件内容哈希作为文档 ID，确保唯一性和幂等性 |

**为什么不剥离 Markdown 标记**:
- `backend/app/services/document_parser.py` 中的 `_parse_markdown()` 会剥离标记
- 但在 RAG 场景中，Markdown 标记提供有价值的结构信息
- 例如：`## 安装指南` 比 `安装指南` 更能表达"这是一个章节标题"

**构造函数设计**:
```python
def __init__(self, **kwargs):
    """接受 **kwargs 以兼容 LoaderFactory 传递的参数"""
    pass
```

---

### 4.3 TextLoader (新增)

**文件**: `src/libs/loader/text_loader.py`

**设计决策**:

| 决策 | 理由 |
|------|------|
| **多编码支持** | 尝试多种编码（UTF-8、GBK、GB2312 等），兼容不同来源的文本文件 |
| **编码检测** | 可选使用 `chardet` 库进行编码检测（优雅降级） |
| **标题提取** | 从第一个非空行提取标题 |

**编码尝试顺序**:
```python
FALLBACK_ENCODINGS = [
    "utf-8",        # 最常见
    "utf-8-sig",    # UTF-8 with BOM
    "gbk",          # 中文（大陆）
    "gb2312",       # 中文（简体）
    "big5",         # 中文（繁体）
    "shift_jis",    # 日文
    "euc-kr",       # 韩文
    "latin-1",      # 西欧
    "cp1252",       # Windows 西欧
]
```

---

### 4.4 WordLoader (新增)

**文件**: `src/libs/loader/word_loader.py`

**设计决策**:

| 决策 | 理由 |
|------|------|
| **转换为 Markdown** | 统一输出格式，便于后续处理和 RAG 检索 |
| **标题识别** | 通过 Word 样式（Heading 1-6）识别标题层级 |
| **表格转换** | 将 Word 表格转换为 Markdown 表格格式 |
| **可选图像提取** | 保留图像提取接口，但默认关闭（Word 图像较少） |

**Word 到 Markdown 转换规则**:
```
Word 样式          →    Markdown 格式
─────────────────────────────────────
Heading 1          →    # 标题
Heading 2          →    ## 标题
Heading 3-6        →    ### 标题
Normal 段落        →    纯文本
表格               →    | 列1 | 列2 |
```

**依赖处理**:
```python
try:
    from docx import Document as DocxDocument
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    logger.warning("python-docx is not installed...")
```

**为什么只导入 `Document`**:
- 原代码还导入了 `WD_PARAGRAPH_FORMAT`，但在新版本 `python-docx` 中该常量不存在
- 实际解析时通过 `paragraph.style.name` 判断标题级别，无需该常量

---

### 4.5 ExcelLoader (新增)

**文件**: `src/libs/loader/excel_loader.py`

**设计决策**:

| 决策 | 理由 |
|------|------|
| **多 Sheet 支持** | 每个 Sheet 转为一个 `## Sheet: {name}` 章节 |
| **表格转 Markdown** | Excel 表格转换为 Markdown 表格格式，保留结构 |
| **行数限制** | 默认每 Sheet 最多 100 行，避免超大文件导致内存问题 |
| **公式值获取** | 使用 `data_only=True` 获取计算后的值，而非公式 |

**Excel 到 Markdown 转换示例**:
```markdown
# 销售报表.xlsx

## Sheet: 一月销售

| 产品 | 数量 | 金额 |
|------|------|------|
| A    | 100  | 1000 |
| B    | 200  | 2000 |

*... showing 100 of 1500 rows*
```

**为什么限制行数**:
- Excel 文件可能包含数万行数据
- 全部转换会导致文本过长，影响 Embedding 质量和 Token 消耗
- 100 行足够展示数据结构和典型值

---

### 4.6 IngestionPipeline 修改

**文件**: `src/ingestion/pipeline.py`

**修改内容**:

1. **导入修改**:
```python
# 原来
from src.libs.loader.pdf_loader import PdfLoader

# 修改后
from src.libs.loader.loader_factory import LoaderFactory
```

2. **`__init__` 修改**:
```python
# 原来：在初始化时创建 Loader
self.loader = PdfLoader(
    extract_images=True,
    image_storage_dir=str(resolve_path(f"data/images/{collection}"))
)

# 修改后：保存配置，在 run() 时动态创建
self._image_storage_dir = str(resolve_path(f"data/images/{collection}"))
```

**为什么在 run() 中创建 Loader**:
- Loader 的选择取决于文件扩展名
- `__init__` 时还不知道要处理的文件类型
- 每次处理不同类型文件时需要不同的 Loader

3. **`run()` 方法修改**:
```python
# 在 Stage 2: Document Loading 中
loader = LoaderFactory.create(
    file_path,
    extract_images=True,
    image_storage_dir=self._image_storage_dir
)
loader_name = LoaderFactory.get_loader_name(file_path)
logger.info(f"  Using loader: {loader_name}")

document = loader.load(str(file_path))
```

---

### 4.7 模块导出更新

**文件**: `src/libs/loader/__init__.py`

```python
from src.libs.loader.base_loader import BaseLoader
from src.libs.loader.pdf_loader import PdfLoader
from src.libs.loader.markdown_loader import MarkdownLoader  # 新增
from src.libs.loader.text_loader import TextLoader          # 新增
from src.libs.loader.word_loader import WordLoader          # 新增
from src.libs.loader.excel_loader import ExcelLoader        # 新增
from src.libs.loader.loader_factory import LoaderFactory    # 新增
from src.libs.loader.file_integrity import FileIntegrityChecker, SQLiteIntegrityChecker

__all__ = [
    "BaseLoader",
    "PdfLoader",
    "MarkdownLoader",
    "TextLoader",
    "WordLoader",
    "ExcelLoader",
    "LoaderFactory",
    "FileIntegrityChecker",
    "SQLiteIntegrityChecker",
]
```

---

### 4.8 依赖更新

**文件**: `pyproject.toml`

```toml
dependencies = [
    # ... 原有依赖 ...
    "python-docx>=1.1.0",   # Word 文档解析
    "openpyxl>=3.1.0",      # Excel 解析
]
```

**为什么选择这些库**:
| 库 | 理由 |
|---|------|
| `python-docx` | 纯 Python 实现，跨平台，社区活跃 |
| `openpyxl` | 支持 `.xlsx` 读写，支持 `data_only` 模式获取公式值 |

---

## 5. 关键设计决策总结

### 5.1 为什么使用工厂模式

| 优点 | 说明 |
|------|------|
| **解耦** | Pipeline 不需要知道具体 Loader 的实现细节 |
| **可扩展** | 新增格式只需添加 Loader 类和注册到 Factory |
| **一致性** | 与项目现有 Factory（EmbeddingFactory、VectorStoreFactory）保持一致 |
| **可测试** | 可以轻松 Mock Factory 进行单元测试 |

### 5.2 为什么保留 Markdown 格式

在 RAG 场景中，Markdown 标记提供有价值的结构信息：
- `# 标题` 表明这是章节标题
- `**粗体**` 表明这是重点内容
- `> 引用` 表明这是引用内容

这些信息有助于：
1. **更好的分块**：按标题分块时保留上下文
2. **更好的检索**：结构标记提高检索相关性
3. **更好的生成**：LLM 可以理解文档结构

### 5.3 为什么使用 `**kwargs` 参数

所有 Loader 的 `__init__` 都接受 `**kwargs` 参数：

```python
def __init__(self, **kwargs):
    pass
```

**理由**:
- `LoaderFactory.create()` 统一传递 `extract_images` 和 `image_storage_dir` 参数
- 不是所有 Loader 都需要这些参数
- 使用 `**kwargs` 可以忽略不需要的参数，避免报错
- 保持接口一致性

### 5.4 为什么 Excel 限制行数

| 问题 | 解决方案 |
|------|----------|
| 内存占用 | 大型 Excel 文件可能包含数万行 |
| Token 消耗 | 全部转换会消耗大量 Token |
| Embedding 质量 | 过长文本影响 Embedding 效果 |
| 检索效率 | 用户通常只需要数据概览 |

**默认 100 行**足够展示：
- 数据结构（列名、数据类型）
- 典型数据值
- 数据分布概览

---

## 6. 使用示例

### 6.1 基本使用

```python
from src.libs.loader import LoaderFactory

# 自动识别文件类型
loader = LoaderFactory.create("document.pdf")
doc = loader.load("document.pdf")

# 支持的格式
print(LoaderFactory.supported_extensions())
# ['.doc', '.docx', '.markdown', '.md', '.pdf', '.txt', '.xls', '.xlsx']
```

### 6.2 摄入管道使用

```python
from src.ingestion.pipeline import IngestionPipeline
from src.core.settings import load_settings

settings = load_settings("config/settings.yaml")
pipeline = IngestionPipeline(settings, collection="my_docs")

# 自动识别文件类型并处理
result = pipeline.run("data/report.md")
result = pipeline.run("data/contract.docx")
result = pipeline.run("data/sales.xlsx")
```

---

## 7. 扩展指南

### 7.1 添加新格式支持

1. 创建新的 Loader 类：
```python
# src/libs/loader/csv_loader.py
class CsvLoader(BaseLoader):
    SUPPORTED_EXTENSIONS = {".csv"}

    def __init__(self, **kwargs):
        pass

    def load(self, file_path: str | Path) -> Document:
        # 实现加载逻辑
        pass
```

2. 在 `LoaderFactory` 中注册：
```python
_EXTENSION_MAP: dict[str, str] = {
    # ... 现有映射 ...
    ".csv": "csv",
}

def _register_loader(cls, name: str):
    # ... 现有代码 ...
    elif name == "csv":
        from src.libs.loader.csv_loader import CsvLoader
        cls._LOADERS[name] = CsvLoader
```

3. 更新 `__init__.py` 导出

---

## 8. 文件修改清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `src/libs/loader/loader_factory.py` | 新增 | 工厂类，根据扩展名创建 Loader |
| `src/libs/loader/markdown_loader.py` | 新增 | Markdown 文档加载器 |
| `src/libs/loader/text_loader.py` | 新增 | 纯文本加载器 |
| `src/libs/loader/word_loader.py` | 新增 | Word 文档加载器 |
| `src/libs/loader/excel_loader.py` | 新增 | Excel 表格加载器 |
| `src/libs/loader/__init__.py` | 修改 | 导出所有新 Loader |
| `src/ingestion/pipeline.py` | 修改 | 使用 LoaderFactory 替代硬编码 PdfLoader |
| `scripts/ingestion.py` | 修改 | 支持多格式文档摄入 |
| `pyproject.toml` | 修改 | 添加 python-docx、openpyxl 依赖 |

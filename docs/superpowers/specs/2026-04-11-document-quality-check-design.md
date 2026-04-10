# 文档质量检测前处理设计文档

## 1. 背景与问题

### 1.1 问题描述

当前摄入管道直接解析文档，未对文档质量进行预检。低质量文档（如扫描版PDF、编码损坏文件）会产生以下问题：

1. **垃圾数据污染知识库**：乱码chunk被向量化后，检索质量严重下降
2. **资源浪费**：已消耗解析、分块、向量化等计算资源
3. **用户困惑**：入库成功但检索无结果，用户不知道原因

### 1.2 需求

在Pipeline入口增加文档质量检测前处理：

- 提取前几页文本，计算有效字符占比
- 有效字符率低于阈值（默认80%）时拒绝入库
- 在Dashboard上给用户明确的错误提示

---

## 2. 设计目标

1. **入口拦截**：在资源消耗前拒绝低质量文档
2. **职责单一**：质量检测逻辑独立，易于测试和维护
3. **可配置**：阈值、采样参数可通过配置文件调整
4. **友好反馈**：返回详细的质量报告，便于用户理解问题
5. **多格式支持**：支持PDF、TXT、MD、DOCX等所有格式

---

## 3. 架构设计

### 3.1 整体架构

```
Pipeline流程（修改后）：
┌─────────────────────────────────────────────────────────────┐
│ Stage 1: File Integrity Check (SHA256)                      │
├─────────────────────────────────────────────────────────────┤
│ Stage 1.5: Quality Check (新增) ← 检测不通过直接返回错误     │
├─────────────────────────────────────────────────────────────┤
│ Stage 2: Document Loading                                   │
├─────────────────────────────────────────────────────────────┤
│ Stage 3-6: Chunking → Transform → Encoding → Storage        │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 组件结构

```
src/ingestion/
├── quality/                           # 新增目录
│   ├── __init__.py
│   ├── document_quality_checker.py    # 核心检测器
│   └── validators/                    # 各格式验证器
│       ├── __init__.py
│       ├── base_validator.py          # 抽象基类
│       ├── pdf_validator.py           # PDF验证器
│       ├── text_validator.py          # TXT验证器
│       ├── word_validator.py          # Word验证器
│       └── markdown_validator.py      # Markdown验证器
├── pipeline.py                        # 修改：集成质量检测
└── ...
```

---

## 4. 详细设计

### 4.1 核心数据结构

**文件**: `src/ingestion/quality/document_quality_checker.py`

```python
@dataclass
class QualityCheckResult:
    """质量检测结果"""
    passed: bool                    # 是否通过
    score: float                    # 有效字符率 (0-1)
    total_chars: int                # 总字符数
    valid_chars: int                # 有效字符数
    invalid_patterns: List[str]     # 检测到的无效字符模式
    message: str                    # 用户友好提示
    details: Dict[str, Any]         # 详细信息（用于调试）
```

### 4.2 DocumentQualityChecker

**文件**: `src/ingestion/quality/document_quality_checker.py`

```python
class DocumentQualityChecker:
    """文档质量检测器

    在文档进入摄入管道前进行质量预检，拒绝低质量文档入库。

    检测逻辑：
    1. 根据文件扩展名选择对应的验证器
    2. 提取前N页/前N字符的文本样本
    3. 计算有效字符率 = 有效字符数 / 总字符数
    4. 有效字符定义：中文、英文、数字、常见标点
    5. 无效字符：控制字符、乱码、替换字符(�)
    """

    def __init__(
        self,
        min_valid_ratio: float = 0.8,
        sample_pages: int = 3,
        sample_chars: int = 5000
    ):
        """初始化质量检测器

        Args:
            min_valid_ratio: 最低有效字符率阈值
            sample_pages: PDF采样页数
            sample_chars: 每页/每文件最大采样字符数
        """
        self.min_valid_ratio = min_valid_ratio
        self.sample_pages = sample_pages
        self.sample_chars = sample_chars

        # 初始化各格式验证器
        self._validators: Dict[str, BaseValidator] = {
            ".pdf": PdfValidator(sample_pages, sample_chars),
            ".txt": TextValidator(sample_chars),
            ".md": MarkdownValidator(sample_chars),
            ".markdown": MarkdownValidator(sample_chars),
            ".docx": WordValidator(sample_pages, sample_chars),
            ".doc": WordValidator(sample_pages, sample_chars),
        }

    def check(self, file_path: Path) -> QualityCheckResult:
        """执行质量检测

        Args:
            file_path: 文件路径

        Returns:
            QualityCheckResult: 检测结果
        """
        ext = file_path.suffix.lower()
        validator = self._validators.get(ext)

        if not validator:
            # 不支持的格式，跳过检测
            return QualityCheckResult(
                passed=True,
                score=1.0,
                total_chars=0,
                valid_chars=0,
                invalid_patterns=[],
                message="格式不支持质量检测，跳过",
                details={"skipped": True, "reason": "unsupported_format"}
            )

        # 执行验证
        result = validator.validate(file_path)

        # 判断是否通过
        result.passed = result.score >= self.min_valid_ratio

        # 生成用户友好消息
        if not result.passed:
            result.message = self._generate_failure_message(result)

        return result

    def _generate_failure_message(self, result: QualityCheckResult) -> str:
        """生成失败消息"""
        return (
            f"文档质量不达标：有效字符率 {result.score:.1%}，"
            f"低于阈值 {self.min_valid_ratio:.0%}。"
            f"可能原因：扫描版PDF缺少文字层、文档编码损坏。"
            f"建议：检查文档是否为图片扫描件，或尝试重新生成文档。"
        )
```

### 4.3 BaseValidator 抽象基类

**文件**: `src/ingestion/quality/validators/base_validator.py`

```python
class BaseValidator(ABC):
    """文档验证器抽象基类"""

    # 有效字符的正则模式
    # 中文、英文、数字、常见标点
    VALID_CHAR_PATTERN = re.compile(
        r'[\u4e00-\u9fff]'      # 中文
        r'|[a-zA-Z]'            # 英文
        r'|\d'                  # 数字
        r'|[，。！？、；：""''（）【】《》]'  # 中文标点
        r'|[,.!?;:\'"()\[\]{}<>]'            # 英文标点
        r'|[\s]'                # 空白字符
    )

    def __init__(self, sample_chars: int = 5000):
        self.sample_chars = sample_chars

    @abstractmethod
    def validate(self, file_path: Path) -> QualityCheckResult:
        """验证文档质量"""
        pass

    def calculate_valid_ratio(self, text: str) -> Tuple[int, int, float]:
        """计算有效字符率

        Args:
            text: 待检测文本

        Returns:
            (总字符数, 有效字符数, 有效字符率)
        """
        if not text:
            return 0, 0, 0.0

        total_chars = len(text)
        valid_chars = len(self.VALID_CHAR_PATTERN.findall(text))
        ratio = valid_chars / total_chars if total_chars > 0 else 0.0

        return total_chars, valid_chars, ratio

    def detect_invalid_patterns(self, text: str) -> List[str]:
        """检测无效字符模式

        Returns:
            检测到的无效字符模式列表（用于调试）
        """
        patterns = []

        # 检测替换字符
        if '\ufffd' in text:
            patterns.append('\ufffd (替换字符)')

        # 检测控制字符
        control_chars = [c for c in text if ord(c) < 32 and c not in '\n\r\t']
        if control_chars:
            patterns.append(f'控制字符: {set(control_chars)}')

        # 检测连续乱码（连续的非ASCII非中文字符）
        # 简化实现：检测高频出现的非正常字符
        return patterns
```

### 4.4 PdfValidator

**文件**: `src/ingestion/quality/validators/pdf_validator.py`

```python
class PdfValidator(BaseValidator):
    """PDF文档验证器

    使用PyMuPDF快速提取前N页文本进行质量检测。
    """

    def __init__(self, sample_pages: int = 3, sample_chars: int = 5000):
        super().__init__(sample_chars)
        self.sample_pages = sample_pages

    def validate(self, file_path: Path) -> QualityCheckResult:
        """验证PDF质量

        检测逻辑：
        1. 用PyMuPDF打开PDF（快速，不解码图像）
        2. 提取前N页的文本
        3. 计算有效字符率
        4. 检测是否为扫描版PDF（无文字层）
        """
        try:
            import fitz  # PyMuPDF
        except ImportError:
            return QualityCheckResult(
                passed=True,  # PyMuPDF不可用时跳过
                score=1.0,
                total_chars=0,
                valid_chars=0,
                invalid_patterns=[],
                message="PyMuPDF不可用，跳过PDF质量检测",
                details={"skipped": True}
            )

        try:
            doc = fitz.open(file_path)
            text_samples = []

            # 提取前N页文本
            pages_to_check = min(self.sample_pages, len(doc))
            for page_num in range(pages_to_check):
                page = doc[page_num]
                text = page.get_text()
                text_samples.append(text[:self.sample_chars])

            doc.close()

            # 合并文本样本
            combined_text = '\n'.join(text_samples)

            # 检测是否为扫描版PDF
            if len(combined_text.strip()) == 0:
                return QualityCheckResult(
                    passed=False,
                    score=0.0,
                    total_chars=0,
                    valid_chars=0,
                    invalid_patterns=[],
                    message="扫描版PDF：未检测到文字层，请使用OCR处理后上传",
                    details={"is_scanned": True}
                )

            # 计算有效字符率
            total, valid, ratio = self.calculate_valid_ratio(combined_text)
            invalid_patterns = self.detect_invalid_patterns(combined_text)

            return QualityCheckResult(
                passed=True,  # 由调用方根据阈值判断
                score=ratio,
                total_chars=total,
                valid_chars=valid,
                invalid_patterns=invalid_patterns,
                message="",
                details={
                    "sample_pages": pages_to_check,
                    "is_scanned": False
                }
            )

        except Exception as e:
            return QualityCheckResult(
                passed=False,
                score=0.0,
                total_chars=0,
                valid_chars=0,
                invalid_patterns=[],
                message=f"PDF解析失败: {str(e)}",
                details={"error": str(e)}
            )
```

### 4.5 TextValidator / MarkdownValidator / WordValidator

类似实现，核心差异：

| 验证器 | 文本提取方式 | 特殊处理 |
|--------|-------------|----------|
| TextValidator | 直接读取文件，多编码尝试 | 使用chardet检测编码 |
| MarkdownValidator | 直接读取文件 | 忽略Markdown标记（可选） |
| WordValidator | python-docx提取段落 | 检测空文档 |

### 4.6 配置扩展

**文件**: `config/settings.yaml`

```yaml
ingestion:
  # 现有配置...
  batch_size: 100

  # 质量检测配置（新增）
  quality_check:
    enabled: true              # 是否启用质量检测
    min_valid_ratio: 0.8       # 最低有效字符率阈值
    sample_pages: 3            # PDF采样页数
    sample_chars: 5000         # 每页/每文件最大采样字符数
```

**文件**: `src/core/settings.py`

```python
@dataclass
class QualityCheckSettings:
    """质量检测配置"""
    enabled: bool = True
    min_valid_ratio: float = 0.8
    sample_pages: int = 3
    sample_chars: int = 5000

@dataclass
class IngestionSettings:
    # 现有字段...
    batch_size: int = 100
    quality_check: Optional[QualityCheckSettings] = None
```

### 4.7 Pipeline集成

**文件**: `src/ingestion/pipeline.py`

```python
class IngestionPipeline:
    def __init__(self, settings: Settings, collection: str = "default", force: bool = False):
        # ... 现有初始化代码 ...

        # Stage 1.5: Quality Checker (新增)
        quality_config = settings.ingestion.quality_check if settings.ingestion else None
        if quality_config and quality_config.enabled:
            self.quality_checker = DocumentQualityChecker(
                min_valid_ratio=quality_config.min_valid_ratio,
                sample_pages=quality_config.sample_pages,
                sample_chars=quality_config.sample_chars
            )
            logger.info(f"  ✓ DocumentQualityChecker initialized (threshold={quality_config.min_valid_ratio})")
        else:
            self.quality_checker = None
            logger.info("  ⏭️  Quality check disabled")

    def run(self, file_path: str, ...) -> PipelineResult:
        # ... Stage 1: File Integrity Check ...

        # ─────────────────────────────────────────────────────────────
        # Stage 1.5: Quality Check (新增)
        # ─────────────────────────────────────────────────────────────
        if self.quality_checker:
            logger.info("\n🔍 Stage 1.5: Document Quality Check")
            quality_result = self.quality_checker.check(file_path)

            stages["quality_check"] = {
                "passed": quality_result.passed,
                "score": quality_result.score,
                "total_chars": quality_result.total_chars,
                "valid_chars": quality_result.valid_chars,
            }

            if not quality_result.passed:
                logger.warning(f"  ❌ Quality check failed: {quality_result.message}")
                return PipelineResult(
                    success=False,
                    file_path=str(file_path),
                    error=quality_result.message,
                    stages=stages
                )

            logger.info(f"  ✓ Quality check passed (score: {quality_result.score:.1%})")

        # ... Stage 2: Document Loading ...
```

---

## 5. API响应格式

### 5.1 成功响应

```json
{
  "success": true,
  "file_path": "/uploads/document.pdf",
  "doc_id": "abc123",
  "chunk_count": 42,
  "stages": {
    "quality_check": {
      "passed": true,
      "score": 0.95,
      "total_chars": 3420,
      "valid_chars": 3249
    }
  }
}
```

### 5.2 失败响应

```json
{
  "success": false,
  "file_path": "/uploads/scanned.pdf",
  "error": "文档质量不达标：有效字符率 45.2%，低于阈值 80%。可能原因：扫描版PDF缺少文字层、文档编码损坏。建议：检查文档是否为图片扫描件，或尝试重新生成文档。",
  "stages": {
    "quality_check": {
      "passed": false,
      "score": 0.452,
      "total_chars": 3420,
      "valid_chars": 1546
    }
  }
}
```

---

## 6. 测试策略

### 6.1 单元测试

| 测试项 | 描述 |
|--------|------|
| `test_valid_pdf_passes` | 正常PDF应通过检测 |
| `test_scanned_pdf_fails` | 扫描版PDF应被拒绝 |
| `test_corrupted_encoding_fails` | 编码损坏文件应被拒绝 |
| `test_threshold_boundary` | 阈值边界测试（79.9% vs 80.1%） |
| `test_unsupported_format_skips` | 不支持的格式应跳过检测 |

### 6.2 集成测试

| 测试项 | 描述 |
|--------|------|
| `test_pipeline_rejects_low_quality` | Pipeline应拒绝低质量文档 |
| `test_quality_check_configurable` | 配置应能调整检测参数 |

---

## 7. 文件修改清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `src/ingestion/quality/__init__.py` | 新增 | 模块导出 |
| `src/ingestion/quality/document_quality_checker.py` | 新增 | 核心检测器 |
| `src/ingestion/quality/validators/__init__.py` | 新增 | 验证器模块导出 |
| `src/ingestion/quality/validators/base_validator.py` | 新增 | 验证器基类 |
| `src/ingestion/quality/validators/pdf_validator.py` | 新增 | PDF验证器 |
| `src/ingestion/quality/validators/text_validator.py` | 新增 | TXT验证器 |
| `src/ingestion/quality/validators/markdown_validator.py` | 新增 | Markdown验证器 |
| `src/ingestion/quality/validators/word_validator.py` | 新增 | Word验证器 |
| `src/ingestion/pipeline.py` | 修改 | 集成质量检测 |
| `src/core/settings.py` | 修改 | 添加质量检测配置 |
| `config/settings.yaml` | 修改 | 添加质量检测配置项 |
| `tests/unit/test_quality_checker.py` | 新增 | 单元测试 |

---

## 8. 后续扩展

1. **OCR建议**：检测到扫描版PDF时，提示用户使用OCR工具处理
2. **质量报告**：在Dashboard展示文档质量评分历史
3. **自动修复**：对编码问题尝试自动修复（如转码）
4. **多语言支持**：扩展有效字符模式支持更多语言

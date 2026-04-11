"""Unit tests for document quality checker."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.ingestion.quality.document_quality_checker import (
    DocumentQualityChecker,
)
from src.ingestion.quality.validators.base_validator import (
    BaseValidator,
    QualityCheckResult,
)


class TestQualityCheckResult:
    """Tests for QualityCheckResult dataclass."""

    def test_default_values(self):
        """Test default values are set correctly."""
        result = QualityCheckResult()
        assert result.passed is False
        assert result.score == 0.0
        assert result.total_chars == 0
        assert result.valid_chars == 0
        assert result.invalid_patterns == []
        assert result.message == ""
        assert result.details == {}

    def test_custom_values(self):
        """Test custom values are set correctly."""
        result = QualityCheckResult(
            passed=True,
            score=0.95,
            total_chars=1000,
            valid_chars=950,
            invalid_patterns=["test"],
            message="Test message",
            details={"key": "value"}
        )
        assert result.passed is True
        assert result.score == 0.95
        assert result.total_chars == 1000
        assert result.valid_chars == 950
        assert result.invalid_patterns == ["test"]
        assert result.message == "Test message"
        assert result.details == {"key": "value"}


class TestBaseValidator:
    """Tests for BaseValidator."""

    def _create_validator(self):
        """Create a concrete validator for testing."""
        class ConcreteValidator(BaseValidator):
            def validate(self, file_path):
                return QualityCheckResult()
        return ConcreteValidator()

    def test_calculate_valid_ratio_empty_text(self):
        """Test calculation with empty text."""
        validator = self._create_validator()
        total, valid, ratio = validator.calculate_valid_ratio("")
        assert total == 0
        assert valid == 0
        assert ratio == 0.0

    def test_calculate_valid_ratio_chinese_text(self):
        """Test calculation with Chinese text."""
        validator = self._create_validator()
        text = "这是一个测试文档，包含中文内容。"
        total, valid, ratio = validator.calculate_valid_ratio(text)
        assert total == len(text)
        assert valid == len(text)  # All characters should be valid
        assert ratio == 1.0

    def test_calculate_valid_ratio_mixed_text(self):
        """Test calculation with mixed Chinese/English text."""
        validator = self._create_validator()
        text = "这是中文English混合123文本。"
        total, valid, ratio = validator.calculate_valid_ratio(text)
        assert total == len(text)
        assert valid == len(text)  # All should be valid
        assert ratio == 1.0

    def test_calculate_valid_ratio_with_garbage(self):
        """Test calculation with garbage characters."""
        validator = self._create_validator()
        # Mix of valid and invalid characters
        text = "正常文本\ufffd\uffff乱码"
        total, valid, ratio = validator.calculate_valid_ratio(text)
        assert total == len(text)
        # \ufffd (replacement char) and \uffff are not in valid pattern
        assert valid < total
        assert ratio < 1.0

    def test_detect_invalid_patterns_replacement_char(self):
        """Test detection of replacement character."""
        validator = self._create_validator()
        text = "正常文本\ufffd乱码"
        patterns = validator.detect_invalid_patterns(text)
        assert len(patterns) > 0
        assert any("替换字符" in p for p in patterns)

    def test_detect_invalid_patterns_control_chars(self):
        """Test detection of control characters."""
        validator = self._create_validator()
        text = "正常文本\x00\x01控制字符"
        patterns = validator.detect_invalid_patterns(text)
        assert len(patterns) > 0
        assert any("控制字符" in p for p in patterns)


class TestDocumentQualityChecker:
    """Tests for DocumentQualityChecker."""

    def test_init_default_values(self):
        """Test initialization with default values."""
        checker = DocumentQualityChecker()
        assert checker.min_valid_ratio == 0.8
        assert checker.sample_pages == 3
        assert checker.sample_chars == 5000

    def test_init_custom_values(self):
        """Test initialization with custom values."""
        checker = DocumentQualityChecker(
            min_valid_ratio=0.9,
            sample_pages=5,
            sample_chars=3000
        )
        assert checker.min_valid_ratio == 0.9
        assert checker.sample_pages == 5
        assert checker.sample_chars == 3000

    def test_supported_extensions(self):
        """Test supported extensions property."""
        checker = DocumentQualityChecker()
        extensions = checker.supported_extensions
        assert ".pdf" in extensions
        assert ".txt" in extensions
        assert ".md" in extensions
        assert ".docx" in extensions

    def test_check_unsupported_format(self):
        """Test check with unsupported format returns passed=True."""
        checker = DocumentQualityChecker()

        with tempfile.NamedTemporaryFile(suffix=".xyz", delete=False) as f:
            f.write(b"test content")
            temp_path = Path(f.name)

        try:
            result = checker.check(temp_path)
            assert result.passed is True  # Unsupported formats pass by default
            assert result.details.get("skipped") is True
        finally:
            temp_path.unlink()

    def test_check_txt_file_high_quality(self):
        """Test check with high quality text file."""
        checker = DocumentQualityChecker(min_valid_ratio=0.8)

        with tempfile.NamedTemporaryFile(mode='w', suffix=".txt", delete=False, encoding='utf-8') as f:
            f.write("这是一个高质量的文本文件，包含正常的中文内容。\n")
            f.write("This is also valid English text.\n")
            f.write("数字123和标点符号，。！？都是有效的。\n")
            temp_path = Path(f.name)

        try:
            result = checker.check(temp_path)
            assert result.passed is True
            assert result.score >= 0.8
        finally:
            temp_path.unlink()

    def test_check_txt_file_low_quality(self):
        """Test check with low quality text file (lots of garbage)."""
        checker = DocumentQualityChecker(min_valid_ratio=0.8)

        # Create a file with mostly garbage characters
        with tempfile.NamedTemporaryFile(mode='w', suffix=".txt", delete=False, encoding='utf-8') as f:
            # Mix of valid and invalid - more than 20% garbage
            f.write("正常文本" + "\ufffd" * 50 + "\x00\x01\x02" * 10)
            temp_path = Path(f.name)

        try:
            result = checker.check(temp_path)
            assert result.passed is False
            assert result.score < 0.8
            assert "质量不达标" in result.message
        finally:
            temp_path.unlink()

    def test_check_empty_txt_file(self):
        """Test check with empty text file."""
        checker = DocumentQualityChecker()

        with tempfile.NamedTemporaryFile(mode='w', suffix=".txt", delete=False, encoding='utf-8') as f:
            f.write("")
            temp_path = Path(f.name)

        try:
            result = checker.check(temp_path)
            assert result.passed is False
            assert result.score == 0.0
        finally:
            temp_path.unlink()

    def test_check_markdown_file(self):
        """Test check with markdown file."""
        checker = DocumentQualityChecker(min_valid_ratio=0.8)

        with tempfile.NamedTemporaryFile(mode='w', suffix=".md", delete=False, encoding='utf-8') as f:
            f.write("# 标题\n\n")
            f.write("这是一个Markdown文档。\n\n")
            f.write("## 二级标题\n\n")
            f.write("- 列表项1\n")
            f.write("- 列表项2\n")
            temp_path = Path(f.name)

        try:
            result = checker.check(temp_path)
            assert result.passed is True
            assert result.score >= 0.8
        finally:
            temp_path.unlink()

    def test_generate_failure_message_scanned_pdf(self):
        """Test failure message for scanned PDF."""
        checker = DocumentQualityChecker()
        result = QualityCheckResult(
            passed=False,
            score=0.0,
            details={"is_scanned": True}
        )
        message = checker._generate_failure_message(result)
        assert "扫描版" in message
        assert "OCR" in message

    def test_generate_failure_message_low_quality(self):
        """Test failure message for low quality document."""
        checker = DocumentQualityChecker(min_valid_ratio=0.8)
        result = QualityCheckResult(
            passed=False,
            score=0.45,
            total_chars=1000,
            valid_chars=450,
            invalid_patterns=["替换字符(�): 50个"],
            details={}
        )
        message = checker._generate_failure_message(result)
        assert "45.0%" in message
        assert "80%" in message


class TestPdfValidator:
    """Tests for PdfValidator."""

    def test_validate_scanned_pdf(self):
        """Test validation of scanned PDF (no text layer)."""
        from src.ingestion.quality.validators.pdf_validator import PdfValidator

        validator = PdfValidator()

        # Mock PyMuPDF to return empty text
        with patch('src.ingestion.quality.validators.pdf_validator.PYMUPDF_AVAILABLE', True):
            mock_fitz = MagicMock()
            mock_doc = MagicMock()
            mock_doc.__len__ = MagicMock(return_value=5)
            mock_page = MagicMock()
            mock_page.get_text.return_value = ""
            mock_doc.__getitem__ = MagicMock(return_value=mock_page)
            mock_fitz.open.return_value = mock_doc

            with patch.dict('sys.modules', {'fitz': mock_fitz}):
                with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
                    f.write(b"%PDF-1.4 fake pdf")
                    temp_path = Path(f.name)

                try:
                    # Re-import to get the mocked version
                    from importlib import reload
                    import src.ingestion.quality.validators.pdf_validator as pdf_mod
                    reload(pdf_mod)
                    validator = pdf_mod.PdfValidator()
                    validator._PYMUPDF_AVAILABLE = True

                    result = validator.validate(temp_path)
                    assert result.passed is False
                    assert result.details.get("is_scanned") is True
                finally:
                    temp_path.unlink()


class TestTextValidator:
    """Tests for TextValidator."""

    def test_validate_utf8_file(self):
        """Test validation of UTF-8 encoded file."""
        from src.ingestion.quality.validators.text_validator import TextValidator

        validator = TextValidator()

        with tempfile.NamedTemporaryFile(mode='w', suffix=".txt", delete=False, encoding='utf-8') as f:
            f.write("这是UTF-8编码的文本文件。\n")
            f.write("包含中文和English内容。\n")
            temp_path = Path(f.name)

        try:
            result = validator.validate(temp_path)
            assert result.score > 0.8
            assert result.details.get("encoding") == "utf-8"
        finally:
            temp_path.unlink()

    def test_validate_gbk_file(self):
        """Test validation of GBK encoded file."""
        from src.ingestion.quality.validators.text_validator import TextValidator

        validator = TextValidator()

        with tempfile.NamedTemporaryFile(mode='wb', suffix=".txt", delete=False) as f:
            f.write("这是GBK编码的文本文件。\n".encode('gbk'))
            temp_path = Path(f.name)

        try:
            result = validator.validate(temp_path)
            assert result.score > 0.8
            assert "gbk" in result.details.get("encoding", "").lower()
        finally:
            temp_path.unlink()


class TestMarkdownValidator:
    """Tests for MarkdownValidator."""

    def test_validate_markdown_file(self):
        """Test validation of markdown file."""
        from src.ingestion.quality.validators.markdown_validator import MarkdownValidator

        validator = MarkdownValidator()

        with tempfile.NamedTemporaryFile(mode='w', suffix=".md", delete=False, encoding='utf-8') as f:
            f.write("# 标题\n\n正文内容\n\n```python\nprint('hello')\n```\n")
            temp_path = Path(f.name)

        try:
            result = validator.validate(temp_path)
            assert result.score > 0.8
            assert result.details.get("doc_type") == "markdown"
        finally:
            temp_path.unlink()


class TestWordValidator:
    """Tests for WordValidator."""

    def test_validate_pymupdf_not_available(self):
        """Test validation when python-docx is not available."""
        from src.ingestion.quality.validators.word_validator import WordValidator

        with patch('src.ingestion.quality.validators.word_validator.DOCX_AVAILABLE', False):
            validator = WordValidator()

            with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
                f.write(b"fake docx")
                temp_path = Path(f.name)

            try:
                result = validator.validate(temp_path)
                assert result.passed is True  # Skipped when not available
                assert result.details.get("skipped") is True
            finally:
                temp_path.unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

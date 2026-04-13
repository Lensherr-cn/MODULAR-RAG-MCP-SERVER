"""Document Quality Checker for pre-ingestion validation.

This module provides the main quality checker that orchestrates
format-specific validators to detect low-quality documents before
they enter the ingestion pipeline.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, Optional

from src.ingestion.quality.validators.base_validator import (
    BaseValidator,
    QualityCheckResult,
)
from src.ingestion.quality.validators.pdf_validator import PdfValidator
from src.ingestion.quality.validators.text_validator import TextValidator
from src.ingestion.quality.validators.markdown_validator import MarkdownValidator
from src.ingestion.quality.validators.word_validator import WordValidator

logger = logging.getLogger(__name__)


class DocumentQualityChecker:
    """Document quality checker for pre-ingestion validation.

    This class performs quality checks on documents before they enter
    the ingestion pipeline. Low-quality documents (e.g., scanned PDFs
    without text layer, corrupted files) are rejected to prevent
    garbage data from polluting the knowledge base.

    Quality Check Process:
    1. Select validator based on file extension
    2. Extract text sample from first N pages/characters
    3. Calculate valid character ratio
    4. Compare against threshold (default 80%)
    5. Return detailed result with pass/fail status

    Example:
        >>> checker = DocumentQualityChecker(min_valid_ratio=0.8)
        >>> result = checker.check(Path("document.pdf"))
        >>> if not result.passed:
        ...     print(f"Rejected: {result.message}")
    """

    def __init__(
        self,
        min_valid_ratio: float = 0.8,
        sample_pages: int = 3,
        sample_chars: int = 5000
    ):
        """Initialize document quality checker.

        Args:
            min_valid_ratio: Minimum valid character ratio threshold (0-1)
            sample_pages: Number of pages to sample for PDFs
            sample_chars: Maximum characters to sample per page/file
        """
        self.min_valid_ratio = min_valid_ratio
        self.sample_pages = sample_pages
        self.sample_chars = sample_chars

        # Initialize format-specific validators
        self._validators: Dict[str, BaseValidator] = {
            ".pdf": PdfValidator(sample_pages, sample_chars),
            ".txt": TextValidator(sample_chars),
            ".md": MarkdownValidator(sample_chars),
            ".markdown": MarkdownValidator(sample_chars),
            ".docx": WordValidator(sample_pages, sample_chars),
            ".doc": WordValidator(sample_pages, sample_chars),
        }

        logger.info(
            f"DocumentQualityChecker initialized: "
            f"threshold={min_valid_ratio:.0%}, "
            f"sample_pages={sample_pages}, "
            f"sample_chars={sample_chars}"
        )

    def check(self, file_path: Path) -> QualityCheckResult:
        """Perform quality check on a document.

        Args:
            file_path: Path to the document file

        Returns:
            QualityCheckResult with pass/fail status and details
        """
        # Ensure Path object
        if isinstance(file_path, str):
            file_path = Path(file_path)

        # Get file extension
        ext = file_path.suffix.lower()

        # Check if format is supported
        if ext not in self._validators:
            logger.debug(f"Unsupported format {ext}, skipping quality check")
            return QualityCheckResult(
                passed=True,
                score=1.0,
                total_chars=0,
                valid_chars=0,
                invalid_patterns=[],
                message="格式不支持质量检测，跳过检测",
                details={"skipped": True, "reason": "unsupported_format", "ext": ext}
            )

        # Get validator
        validator = self._validators[ext]

        # Perform validation
        logger.debug(f"Running quality check for {file_path.name} (format: {ext})")
        result = validator.validate(file_path)

        # Determine pass/fail based on threshold
        result.passed = result.score >= self.min_valid_ratio

        # Generate user-friendly message if failed
        if not result.passed:
            result.message = self._generate_failure_message(result)
            logger.warning(
                f"Quality check failed for {file_path.name}: "
                f"score={result.score:.1%}, threshold={self.min_valid_ratio:.0%}"
            )
        else:
            logger.info(
                f"Quality check passed for {file_path.name}: "
                f"score={result.score:.1%}"
            )

        return result

    def _generate_failure_message(self, result: QualityCheckResult) -> str:
        """Generate user-friendly failure message.

        Args:
            result: Quality check result

        Returns:
            User-friendly message string
        """
        # Check for specific failure reasons
        details = result.details

        # Scanned PDF (no text layer)
        if details.get("is_scanned"):
            return (
                "扫描版文档：未检测到文字层。"
                "该文档可能是图片扫描件，无法提取文本内容。"
                "建议：使用OCR工具处理后重新上传。"
            )

        # Encoding issues
        if result.invalid_patterns:
            patterns_str = "、".join(result.invalid_patterns[:3])
            return (
                f"文档质量不达标：有效字符率 {result.score:.1%}，"
                f"低于阈值 {self.min_valid_ratio:.0%}。"
                f"检测到问题：{patterns_str}。"
                f"建议：检查文档编码是否正确，或尝试重新生成文档。"
            )

        # Generic low quality
        return (
            f"文档质量不达标：有效字符率 {result.score:.1%}，"
            f"低于阈值 {self.min_valid_ratio:.0%}。"
            f"可能原因：扫描版文档缺少文字层、文档编码损坏。"
            f"建议：检查文档是否为图片扫描件，或尝试重新生成文档。"
        )

    @property
    def supported_extensions(self) -> list:
        """Get list of supported file extensions."""
        return list(self._validators.keys())

"""Word document validator for quality checking.

This module provides Word document (DOCX) quality validation using
python-docx for text extraction.
"""

from __future__ import annotations

import logging
from pathlib import Path

from src.ingestion.quality.validators.base_validator import (
    BaseValidator,
    QualityCheckResult,
)

logger = logging.getLogger(__name__)

# Check if python-docx is available
try:
    from docx import Document as DocxDocument
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    logger.warning("python-docx not available, Word quality check will be skipped")


class WordValidator(BaseValidator):
    """Word document validator.

    Uses python-docx for text extraction from DOCX files.
    Detects:
    - Empty documents
    - Corrupted documents
    - Low text quality
    """

    def __init__(self, sample_pages: int = 3, sample_chars: int = 5000):
        """Initialize Word validator.

        Args:
            sample_pages: Number of paragraphs to sample (treated as "pages")
            sample_chars: Maximum characters to sample
        """
        super().__init__(sample_chars)
        self.sample_pages = sample_pages

    def validate(self, file_path: Path) -> QualityCheckResult:
        """Validate Word document quality.

        Args:
            file_path: Path to the Word file

        Returns:
            QualityCheckResult with validation results
        """
        # Check if python-docx is available
        if not DOCX_AVAILABLE:
            logger.warning("python-docx not available, skipping Word quality check")
            return QualityCheckResult(
                passed=True,
                score=1.0,
                total_chars=0,
                valid_chars=0,
                invalid_patterns=[],
                message="python-docx不可用，跳过Word质量检测",
                details={"skipped": True, "reason": "python-docx_not_available"}
            )

        try:
            # Open Word document
            doc = DocxDocument(file_path)

            # Extract text from paragraphs
            paragraphs = []
            for i, para in enumerate(doc.paragraphs):
                if i >= self.sample_pages * 10:  # Approximate 10 paragraphs per "page"
                    break
                paragraphs.append(para.text)

            combined_text = '\n'.join(paragraphs)

            # Check for empty document
            if len(combined_text.strip()) == 0:
                logger.warning(f"Empty Word document: {file_path.name}")
                return QualityCheckResult(
                    passed=False,
                    score=0.0,
                    total_chars=0,
                    valid_chars=0,
                    invalid_patterns=[],
                    message="Word文档为空，未检测到文本内容",
                    details={"is_empty": True}
                )

            # Limit to sample_chars
            sample_text = combined_text[:self.sample_chars]

            # Calculate valid character ratio
            total_chars, valid_chars, ratio = self.calculate_valid_ratio(sample_text)

            # Detect invalid patterns
            invalid_patterns = self.detect_invalid_patterns(sample_text)

            logger.debug(
                f"Word quality check: {file_path.name}, "
                f"paragraphs={len(paragraphs)}, "
                f"chars={total_chars}, "
                f"valid_ratio={ratio:.1%}"
            )

            return QualityCheckResult(
                passed=True,  # Will be set by caller based on threshold
                score=ratio,
                total_chars=total_chars,
                valid_chars=valid_chars,
                invalid_patterns=invalid_patterns,
                message="",
                details={
                    "paragraph_count": len(doc.paragraphs),
                    "sample_paragraphs": len(paragraphs)
                }
            )

        except Exception as e:
            logger.error(f"Word validation failed for {file_path.name}: {e}")
            return QualityCheckResult(
                passed=False,
                score=0.0,
                total_chars=0,
                valid_chars=0,
                invalid_patterns=[],
                message=f"Word文档解析失败: {str(e)}",
                details={"error": str(e), "error_type": type(e).__name__}
            )

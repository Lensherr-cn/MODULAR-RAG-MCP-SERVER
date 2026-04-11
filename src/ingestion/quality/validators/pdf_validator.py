"""PDF document validator for quality checking.

This module provides PDF-specific quality validation using PyMuPDF
for fast text extraction without full decoding.
"""

from __future__ import annotations

import logging
from pathlib import Path

from src.ingestion.quality.validators.base_validator import (
    BaseValidator,
    QualityCheckResult,
)

logger = logging.getLogger(__name__)

# Check if PyMuPDF is available
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    logger.warning("PyMuPDF not available, PDF quality check will be skipped")


class PdfValidator(BaseValidator):
    """PDF document validator.

    Uses PyMuPDF for fast text extraction from the first N pages.
    Detects:
    - Scanned PDFs (no text layer)
    - Corrupted PDFs
    - Low text quality (encoding issues, garbled text)
    """

    def __init__(self, sample_pages: int = 3, sample_chars: int = 5000):
        """Initialize PDF validator.

        Args:
            sample_pages: Number of pages to sample
            sample_chars: Maximum characters to sample per page
        """
        super().__init__(sample_chars)
        self.sample_pages = sample_pages

    def validate(self, file_path: Path) -> QualityCheckResult:
        """Validate PDF document quality.

        Args:
            file_path: Path to the PDF file

        Returns:
            QualityCheckResult with validation results
        """
        # Check if PyMuPDF is available
        if not PYMUPDF_AVAILABLE:
            logger.warning("PyMuPDF not available, skipping PDF quality check")
            return QualityCheckResult(
                passed=True,
                score=1.0,
                total_chars=0,
                valid_chars=0,
                invalid_patterns=[],
                message="PyMuPDF不可用，跳过PDF质量检测",
                details={"skipped": True, "reason": "pymupdf_not_available"}
            )

        try:
            # Open PDF with PyMuPDF (fast, doesn't decode images)
            doc = fitz.open(file_path)
            text_samples = []
            pages_to_check = min(self.sample_pages, len(doc))

            # Extract text from first N pages
            for page_num in range(pages_to_check):
                page = doc[page_num]
                text = page.get_text()
                # Limit to sample_chars per page
                text_samples.append(text[:self.sample_chars])

            doc.close()

            # Combine text samples
            combined_text = '\n'.join(text_samples)

            # Check for scanned PDF (no text layer)
            if len(combined_text.strip()) == 0:
                logger.warning(f"Scanned PDF detected (no text layer): {file_path.name}")
                return QualityCheckResult(
                    passed=False,
                    score=0.0,
                    total_chars=0,
                    valid_chars=0,
                    invalid_patterns=[],
                    message="",
                    details={
                        "is_scanned": True,
                        "sample_pages": pages_to_check,
                        "total_pages": len(doc) if 'doc' in dir() else 0
                    }
                )

            # Calculate valid character ratio
            total_chars, valid_chars, ratio = self.calculate_valid_ratio(combined_text)

            # Detect invalid patterns
            invalid_patterns = self.detect_invalid_patterns(combined_text)

            logger.debug(
                f"PDF quality check: {file_path.name}, "
                f"pages={pages_to_check}, "
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
                    "sample_pages": pages_to_check,
                    "is_scanned": False
                }
            )

        except Exception as e:
            logger.error(f"PDF validation failed for {file_path.name}: {e}")
            return QualityCheckResult(
                passed=False,
                score=0.0,
                total_chars=0,
                valid_chars=0,
                invalid_patterns=[],
                message=f"PDF解析失败: {str(e)}",
                details={"error": str(e), "error_type": type(e).__name__}
            )

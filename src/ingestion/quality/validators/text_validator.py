"""Plain text document validator for quality checking.

This module provides text file validation with encoding detection
for robust file reading.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from src.ingestion.quality.validators.base_validator import (
    BaseValidator,
    QualityCheckResult,
)

logger = logging.getLogger(__name__)


class TextValidator(BaseValidator):
    """Plain text document validator.

    Supports multiple encodings with automatic detection.
    Detects:
    - Encoding issues
    - Corrupted text files
    - Low text quality
    """

    # Common encodings to try in order
    FALLBACK_ENCODINGS = [
        "utf-8",
        "utf-8-sig",  # UTF-8 with BOM
        "gbk",        # Chinese (Mainland)
        "gb2312",     # Chinese (Simplified)
        "big5",       # Chinese (Traditional)
        "shift_jis",  # Japanese
        "euc-kr",     # Korean
        "latin-1",    # Western European
        "cp1252",     # Windows Western European
    ]

    def __init__(self, sample_chars: int = 5000):
        """Initialize text validator.

        Args:
            sample_chars: Maximum characters to sample
        """
        super().__init__(sample_chars)

    def validate(self, file_path: Path) -> QualityCheckResult:
        """Validate text document quality.

        Args:
            file_path: Path to the text file

        Returns:
            QualityCheckResult with validation results
        """
        try:
            # Read file with encoding detection
            text, used_encoding = self._read_with_encoding_detection(file_path)

            if not text:
                return QualityCheckResult(
                    passed=False,
                    score=0.0,
                    total_chars=0,
                    valid_chars=0,
                    invalid_patterns=[],
                    message="文本文件为空",
                    details={"is_empty": True}
                )

            # Limit to sample_chars
            sample_text = text[:self.sample_chars]

            # Calculate valid character ratio
            total_chars, valid_chars, ratio = self.calculate_valid_ratio(sample_text)

            # Detect invalid patterns
            invalid_patterns = self.detect_invalid_patterns(sample_text)

            logger.debug(
                f"Text quality check: {file_path.name}, "
                f"encoding={used_encoding}, "
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
                    "encoding": used_encoding,
                    "file_size": file_path.stat().st_size
                }
            )

        except Exception as e:
            logger.error(f"Text validation failed for {file_path.name}: {e}")
            return QualityCheckResult(
                passed=False,
                score=0.0,
                total_chars=0,
                valid_chars=0,
                invalid_patterns=[],
                message=f"文本文件读取失败: {str(e)}",
                details={"error": str(e), "error_type": type(e).__name__}
            )

    def _read_with_encoding_detection(self, path: Path) -> tuple[str, str]:
        """Read file with automatic encoding detection.

        Tries multiple encodings in order until one succeeds.

        Args:
            path: Path to the file

        Returns:
            Tuple of (decoded text, encoding used)
        """
        # First, try to detect encoding using chardet if available
        detected_encoding = self._detect_encoding(path)
        if detected_encoding:
            try:
                text = path.read_text(encoding=detected_encoding)
                return text, detected_encoding
            except (UnicodeDecodeError, LookupError):
                pass

        # Try fallback encodings
        for encoding in self.FALLBACK_ENCODINGS:
            try:
                text = path.read_text(encoding=encoding)
                return text, encoding
            except (UnicodeDecodeError, LookupError):
                continue

        # Last resort: read with errors ignored
        text = path.read_text(encoding="utf-8", errors="ignore")
        return text, "utf-8 (errors ignored)"

    def _detect_encoding(self, path: Path) -> Optional[str]:
        """Detect file encoding using chardet if available.

        Args:
            path: Path to the file

        Returns:
            Detected encoding or None if detection fails
        """
        try:
            import chardet

            raw_data = path.read_bytes()
            result = chardet.detect(raw_data)
            encoding = result.get("encoding")

            if encoding and result.get("confidence", 0) > 0.7:
                return encoding

        except ImportError:
            logger.debug("chardet not available, using fallback encodings")
        except Exception as e:
            logger.debug(f"Encoding detection failed: {e}")

        return None

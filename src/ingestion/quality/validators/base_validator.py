"""Base validator for document quality checking.

This module provides the abstract base class for all format-specific validators.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Tuple


@dataclass
class QualityCheckResult:
    """Quality check result dataclass.

    Attributes:
        passed: Whether the document passed quality check
        score: Valid character ratio (0-1)
        total_chars: Total characters sampled
        valid_chars: Valid characters count
        invalid_patterns: Detected invalid character patterns
        message: User-friendly message
        details: Additional details for debugging
    """
    passed: bool = False
    score: float = 0.0
    total_chars: int = 0
    valid_chars: int = 0
    invalid_patterns: List[str] = field(default_factory=list)
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)


class BaseValidator(ABC):
    """Abstract base class for document validators.

    Each format-specific validator inherits from this class and implements
    the validate() method.

    Valid character definition:
    - Chinese characters: \u4e00-\u9fff
    - English letters: a-zA-Z
    - Digits: 0-9
    - Common punctuation (Chinese and English)
    - Whitespace characters
    """

    # Valid character regex pattern
    # Chinese, English, digits, common punctuation, whitespace
    VALID_CHAR_PATTERN = re.compile(
        r'[\u4e00-\u9fff]'                          # Chinese characters
        r'|[a-zA-Z]'                                # English letters
        r'|\d'                                      # Digits
        r'|[，。！？、；：""''（）【】《》]'        # Chinese punctuation
        r'|[,.!?;:\'"()\[\]{}<>]'                   # English punctuation
        r'|[\s]'                                    # Whitespace
    )

    def __init__(self, sample_chars: int = 5000):
        """Initialize base validator.

        Args:
            sample_chars: Maximum characters to sample per page/file
        """
        self.sample_chars = sample_chars

    @abstractmethod
    def validate(self, file_path: Path) -> QualityCheckResult:
        """Validate document quality.

        Args:
            file_path: Path to the document file

        Returns:
            QualityCheckResult with validation results
        """
        pass

    def calculate_valid_ratio(self, text: str) -> Tuple[int, int, float]:
        """Calculate valid character ratio.

        Args:
            text: Text to analyze

        Returns:
            Tuple of (total_chars, valid_chars, ratio)
        """
        if not text:
            return 0, 0, 0.0

        total_chars = len(text)
        valid_chars = len(self.VALID_CHAR_PATTERN.findall(text))
        ratio = valid_chars / total_chars if total_chars > 0 else 0.0

        return total_chars, valid_chars, ratio

    def detect_invalid_patterns(self, text: str) -> List[str]:
        """Detect invalid character patterns in text.

        Args:
            text: Text to analyze

        Returns:
            List of detected invalid patterns (for debugging)
        """
        patterns = []

        # Check for replacement character (indicates encoding issues)
        if '\ufffd' in text:
            count = text.count('\ufffd')
            patterns.append(f'替换字符(�): {count}个')

        # Check for control characters (excluding newline, carriage return, tab)
        control_chars = [c for c in text if ord(c) < 32 and c not in '\n\r\t']
        if control_chars:
            unique_controls = set(c for c in control_chars[:10])  # Limit to first 10 unique
            patterns.append(f'控制字符: {[repr(c) for c in unique_controls]}')

        # Check for high-byte non-CJK characters (potential encoding issues)
        # Characters in 0x80-0xFF range that are not valid in any common encoding
        high_byte_garbage = [c for c in text if 0x80 <= ord(c) <= 0xFF and not self.VALID_CHAR_PATTERN.match(c)]
        if high_byte_garbage:
            unique_garbage = set(high_byte_garbage[:10])
            patterns.append(f'高位乱码字符: {[repr(c) for c in unique_garbage]}')

        return patterns

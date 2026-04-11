"""Markdown document validator for quality checking.

This module provides Markdown-specific quality validation.
Markdown files are treated similarly to text files but with
optional handling of Markdown syntax.
"""

from __future__ import annotations

import logging
from pathlib import Path

from src.ingestion.quality.validators.base_validator import (
    BaseValidator,
    QualityCheckResult,
)
from src.ingestion.quality.validators.text_validator import TextValidator

logger = logging.getLogger(__name__)


class MarkdownValidator(TextValidator):
    """Markdown document validator.

    Inherits from TextValidator and adds Markdown-specific handling.
    Markdown syntax characters are considered valid.
    """

    # Additional valid characters for Markdown syntax
    MARKDOWN_CHARS = set('#*_`[]()!>-~|=')

    def validate(self, file_path: Path) -> QualityCheckResult:
        """Validate Markdown document quality.

        Args:
            file_path: Path to the Markdown file

        Returns:
            QualityCheckResult with validation results
        """
        # Use parent class validation (same as text files)
        result = super().validate(file_path)

        # Add Markdown-specific details
        if result.details:
            result.details["doc_type"] = "markdown"

        return result

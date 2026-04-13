"""Document quality checking module.

This module provides document quality pre-check functionality
to reject low-quality documents before ingestion.

Components:
- DocumentQualityChecker: Main quality checker class
- QualityCheckResult: Result dataclass
- validators: Format-specific validators (PDF, TXT, MD, DOCX)
"""

from src.ingestion.quality.document_quality_checker import (
    DocumentQualityChecker,
    QualityCheckResult,
)

__all__ = [
    "DocumentQualityChecker",
    "QualityCheckResult",
]

"""Plain text document loader.

This module implements loading and parsing of plain text files,
with encoding detection for robust file reading.

Features:
- Encoding detection with fallback
- Line count metadata
- SHA256-based document ID
- Title extraction from first non-empty line
"""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from src.core.types import Document
from src.libs.loader.base_loader import BaseLoader

logger = logging.getLogger(__name__)


class TextLoader(BaseLoader):
    """Plain text document loader.

    This loader reads plain text files with automatic encoding detection,
    making it robust for files with different encodings.

    The loader:
    1. Reads the file with encoding detection
    2. Extracts title from first non-empty line
    3. Computes SHA256 hash for document ID
    4. Records line and character counts

    Example:
        >>> loader = TextLoader()
        >>> doc = loader.load("data/notes.txt")
        >>> print(doc.metadata["line_count"])
    """

    SUPPORTED_EXTENSIONS = {".txt"}

    # Common encodings to try in order
    FALLBACK_ENCODINGS = [
        "utf-8",
        "utf-8-sig",  # UTF-8 with BOM
        "gbk",        # Chinese
        "gb2312",     # Chinese simplified
        "big5",       # Chinese traditional
        "shift_jis",  # Japanese
        "euc-kr",     # Korean
        "latin-1",    # Western European
        "cp1252",     # Windows Western European
    ]

    def __init__(self, **kwargs):
        """Initialize Text Loader.

        Args:
            **kwargs: Ignored (for compatibility with LoaderFactory).
        """
        # Ignore extra kwargs for compatibility with LoaderFactory
        pass

    def load(self, file_path: str | Path) -> Document:
        """Load and parse a plain text file.

        Args:
            file_path: Path to the text file.

        Returns:
            Document with text content and metadata.

        Raises:
            FileNotFoundError: If the file doesn't exist.
            ValueError: If the file is not a text file.
        """
        # Validate file
        path = self._validate_file(file_path)

        if path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"File is not a text file: {path}. "
                f"Supported extensions: {self.SUPPORTED_EXTENSIONS}"
            )

        # Read file content with encoding detection
        text, used_encoding = self._read_with_encoding_detection(path)

        # Compute document hash for unique ID
        doc_hash = self._compute_hash(text)
        doc_id = f"doc_{doc_hash[:16]}"

        # Extract title from first non-empty line
        title = self._extract_title(text)

        # Build metadata
        metadata: Dict[str, Any] = {
            "source_path": str(path),
            "doc_type": "text",
            "doc_hash": doc_hash,
            "char_count": len(text),
            "line_count": text.count("\n") + 1,
            "encoding": used_encoding,
        }

        if title:
            metadata["title"] = title

        logger.debug(
            f"Loaded text file: {path.name}, "
            f"{len(text)} chars, encoding: {used_encoding}"
        )

        return Document(
            id=doc_id,
            text=text,
            metadata=metadata
        )

    def _compute_hash(self, text: str) -> str:
        """Compute SHA256 hash of text content.

        Args:
            text: Text content to hash.

        Returns:
            Hex string of SHA256 hash.
        """
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def _read_with_encoding_detection(self, path: Path) -> tuple[str, str]:
        """Read file with automatic encoding detection.

        Tries multiple encodings in order until one succeeds.

        Args:
            path: Path to the file.

        Returns:
            Tuple of (decoded text, encoding used).
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
        return text, "utf-8 (with errors ignored)"

    def _detect_encoding(self, path: Path) -> Optional[str]:
        """Detect file encoding using chardet if available.

        Args:
            path: Path to the file.

        Returns:
            Detected encoding or None if detection fails.
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

    def _extract_title(self, text: str) -> Optional[str]:
        """Extract title from first non-empty line.

        Args:
            text: Text content.

        Returns:
            Title string if found, None otherwise.
        """
        lines = text.split("\n")

        for line in lines[:10]:  # Check first 10 lines
            line = line.strip()
            if line and len(line) > 0:
                # Limit title length
                return line[:100] if len(line) > 100 else line

        return None

"""Markdown document loader.

This module implements loading and parsing of Markdown files,
preserving the original formatting for optimal RAG context.

Features:
- Preserves Markdown formatting (not stripped)
- Extracts title from first H1 heading
- Records section structure in metadata
- SHA256-based document ID
"""

from __future__ import annotations

import hashlib
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.core.types import Document
from src.libs.loader.base_loader import BaseLoader

logger = logging.getLogger(__name__)


class MarkdownLoader(BaseLoader):
    """Markdown document loader.

    This loader reads Markdown files and preserves the original formatting,
    which is beneficial for RAG systems as the structure provides context.

    The loader:
    1. Reads the file as UTF-8 text
    2. Extracts title from first H1 heading
    3. Parses section structure by headings
    4. Computes SHA256 hash for document ID

    Example:
        >>> loader = MarkdownLoader()
        >>> doc = loader.load("docs/readme.md")
        >>> print(doc.metadata["title"])
        >>> print(doc.metadata["sections"])
    """

    SUPPORTED_EXTENSIONS = {".md", ".markdown"}

    def __init__(self, **kwargs):
        """Initialize Markdown Loader.

        Args:
            **kwargs: Ignored (for compatibility with LoaderFactory).
        """
        # Ignore extra kwargs for compatibility with LoaderFactory
        pass

    def load(self, file_path: str | Path) -> Document:
        """Load and parse a Markdown file.

        Args:
            file_path: Path to the Markdown file.

        Returns:
            Document with preserved Markdown text and metadata.

        Raises:
            FileNotFoundError: If the file doesn't exist.
            ValueError: If the file is not a Markdown file.
        """
        # Validate file
        path = self._validate_file(file_path)

        if path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"File is not a Markdown file: {path}. "
                f"Supported extensions: {self.SUPPORTED_EXTENSIONS}"
            )

        # Read file content
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            # Try with other common encodings
            text = self._read_with_fallback_encoding(path)

        # Compute document hash for unique ID
        doc_hash = self._compute_hash(text)
        doc_id = f"doc_{doc_hash[:16]}"

        # Extract title
        title = self._extract_title(text)

        # Parse sections
        sections = self._parse_sections(text)

        # Build metadata
        metadata: Dict[str, Any] = {
            "source_path": str(path),
            "doc_type": "markdown",
            "doc_hash": doc_hash,
            "char_count": len(text),
            "line_count": text.count("\n") + 1,
        }

        if title:
            metadata["title"] = title

        if sections:
            metadata["sections"] = sections
            metadata["section_count"] = len(sections)

        logger.debug(
            f"Loaded Markdown: {path.name}, "
            f"{len(text)} chars, {len(sections)} sections"
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

    def _read_with_fallback_encoding(self, path: Path) -> str:
        """Read file with fallback encodings.

        Args:
            path: Path to the file.

        Returns:
            Decoded text content.
        """
        encodings = ["utf-8-sig", "gbk", "gb2312", "latin-1"]

        for encoding in encodings:
            try:
                return path.read_text(encoding=encoding)
            except (UnicodeDecodeError, LookupError):
                continue

        # Last resort: read with errors ignored
        return path.read_text(encoding="utf-8", errors="ignore")

    def _extract_title(self, text: str) -> Optional[str]:
        """Extract title from first H1 heading.

        Args:
            text: Markdown text content.

        Returns:
            Title string if found, None otherwise.
        """
        lines = text.split("\n")

        for line in lines[:20]:  # Check first 20 lines
            line = line.strip()

            # Match H1 heading: # Title
            if line.startswith("# "):
                return line[2:].strip()

            # Match underline-style H1:
            # Title
            # =====
            # (check next line for underline)

        # Fallback: use first non-empty line
        for line in lines[:10]:
            line = line.strip()
            if line and not line.startswith("#"):
                # Clean up any markdown formatting
                clean_line = re.sub(r"[#*_`~\[\]]", "", line).strip()
                if clean_line:
                    return clean_line[:100]  # Limit title length

        return None

    def _parse_sections(self, text: str) -> List[Dict[str, Any]]:
        """Parse document sections by headings.

        Args:
            text: Markdown text content.

        Returns:
            List of section info dicts with title, level, and line number.
        """
        sections = []
        lines = text.split("\n")

        for i, line in enumerate(lines):
            # Match ATX-style headings: ## Title
            match = re.match(r"^(#{1,6})\s+(.+)$", line)
            if match:
                level = len(match.group(1))
                title = match.group(2).strip()
                sections.append({
                    "level": level,
                    "title": title,
                    "line": i + 1,
                })

        return sections

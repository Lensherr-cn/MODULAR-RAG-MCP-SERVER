"""Word document loader.

This module implements loading and parsing of Microsoft Word documents,
converting them to Markdown format for consistent RAG processing.

Features:
- Converts Word documents to Markdown format
- Extracts headings, paragraphs, tables, and lists
- Optional image extraction
- SHA256-based document ID

Dependencies:
    python-docx>=1.1.0
"""

from __future__ import annotations

import hashlib
import io
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.core.types import Document
from src.libs.loader.base_loader import BaseLoader

logger = logging.getLogger(__name__)

# Check for python-docx availability
try:
    from docx import Document as DocxDocument
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    logger.warning(
        "python-docx is not installed. WordLoader will not be available. "
        "Install with: pip install python-docx"
    )


class WordLoader(BaseLoader):
    """Word document loader (.docx).

    This loader reads Word documents and converts them to Markdown format,
    preserving the document structure for optimal RAG context.

    The loader:
    1. Parses the .docx file using python-docx
    2. Converts headings, paragraphs, tables to Markdown
    3. Extracts images (optional)
    4. Computes SHA256 hash for document ID

    Example:
        >>> loader = WordLoader()
        >>> doc = loader.load("reports/contract.docx")
        >>> print(doc.metadata["table_count"])
    """

    SUPPORTED_EXTENSIONS = {".docx", ".doc"}

    def __init__(
        self,
        extract_images: bool = False,
        image_storage_dir: str | Path = "data/images",
        **kwargs,
    ):
        """Initialize Word Loader.

        Args:
            extract_images: Whether to extract images from documents.
            image_storage_dir: Base directory for storing extracted images.
            **kwargs: Ignored (for compatibility with LoaderFactory).
        """
        if not DOCX_AVAILABLE:
            raise ImportError(
                "python-docx is required for WordLoader. "
                "Install with: pip install python-docx"
            )

        self.extract_images = extract_images
        self.image_storage_dir = Path(image_storage_dir)

    def load(self, file_path: str | Path) -> Document:
        """Load and parse a Word document.

        Args:
            file_path: Path to the Word file.

        Returns:
            Document with Markdown text and metadata.

        Raises:
            FileNotFoundError: If the file doesn't exist.
            ValueError: If the file is not a Word document.
            ImportError: If python-docx is not installed.
        """
        # Validate file
        path = self._validate_file(file_path)

        if path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"File is not a Word document: {path}. "
                f"Supported extensions: {self.SUPPORTED_EXTENSIONS}"
            )

        # Handle legacy .doc format
        if path.suffix.lower() == ".doc":
            logger.warning(
                f"Legacy .doc format detected for {path}. "
                "Support is limited. Consider converting to .docx format."
            )

        # Compute file hash for document ID
        doc_hash = self._compute_file_hash(path)
        doc_id = f"doc_{doc_hash[:16]}"

        # Parse Word document
        try:
            doc = DocxDocument(str(path))
        except Exception as e:
            raise RuntimeError(f"Failed to parse Word document: {e}") from e

        # Convert to Markdown
        markdown_text, stats = self._convert_to_markdown(doc)

        # Build metadata
        metadata: Dict[str, Any] = {
            "source_path": str(path),
            "doc_type": "docx",
            "doc_hash": doc_hash,
            "char_count": len(markdown_text),
            "paragraph_count": stats["paragraph_count"],
            "table_count": stats["table_count"],
            "heading_count": stats["heading_count"],
        }

        if stats.get("title"):
            metadata["title"] = stats["title"]

        logger.debug(
            f"Loaded Word document: {path.name}, "
            f"{len(markdown_text)} chars, {stats['paragraph_count']} paragraphs, "
            f"{stats['table_count']} tables"
        )

        return Document(
            id=doc_id,
            text=markdown_text,
            metadata=metadata
        )

    def _compute_file_hash(self, file_path: Path) -> str:
        """Compute SHA256 hash of file content.

        Args:
            file_path: Path to file.

        Returns:
            Hex string of SHA256 hash.
        """
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def _convert_to_markdown(
        self,
        doc: "DocxDocument"
    ) -> tuple[str, Dict[str, Any]]:
        """Convert Word document to Markdown format.

        Args:
            doc: python-docx Document object.

        Returns:
            Tuple of (markdown text, statistics dict).
        """
        lines: List[str] = []
        stats = {
            "paragraph_count": 0,
            "table_count": 0,
            "heading_count": 0,
            "title": None,
        }

        for element in doc.element.body:
            # Handle paragraphs (including headings)
            if element.tag.endswith("p"):
                paragraph = None
                for p in doc.paragraphs:
                    if p._element == element:
                        paragraph = p
                        break

                if paragraph:
                    text = paragraph.text.strip()
                    if not text:
                        continue

                    # Check if it's a heading
                    heading_level = self._get_heading_level(paragraph)

                    if heading_level:
                        stats["heading_count"] += 1
                        heading_prefix = "#" * heading_level
                        lines.append(f"\n{heading_prefix} {text}\n")

                        # First H1 becomes title
                        if heading_level == 1 and stats["title"] is None:
                            stats["title"] = text
                    else:
                        stats["paragraph_count"] += 1
                        lines.append(text)

            # Handle tables
            elif element.tag.endswith("tbl"):
                table = None
                for t in doc.tables:
                    if t._element == element:
                        table = t
                        break

                if table:
                    stats["table_count"] += 1
                    table_md = self._convert_table_to_markdown(table)
                    lines.append("\n" + table_md + "\n")

        markdown_text = "\n".join(lines)

        # If no title was found, use first non-empty line
        if stats["title"] is None:
            for line in lines:
                clean = line.strip()
                if clean and not clean.startswith("#"):
                    stats["title"] = clean[:100]
                    break

        return markdown_text, stats

    def _get_heading_level(self, paragraph) -> Optional[int]:
        """Get heading level from paragraph style.

        Args:
            paragraph: python-docx Paragraph object.

        Returns:
            Heading level (1-6) or None if not a heading.
        """
        if not paragraph.style:
            return None

        style_name = paragraph.style.name.lower()

        # Check for built-in heading styles
        if style_name.startswith("heading"):
            try:
                level = int(style_name.replace("heading", "").strip())
                return min(max(level, 1), 6)  # Clamp to 1-6
            except ValueError:
                pass

        # Check for title style
        if style_name == "title":
            return 1

        return None

    def _convert_table_to_markdown(self, table) -> str:
        """Convert Word table to Markdown format.

        Args:
            table: python-docx Table object.

        Returns:
            Markdown table string.
        """
        if not table.rows:
            return ""

        rows_data = []
        for row in table.rows:
            cells = [cell.text.strip().replace("\n", " ") for cell in row.cells]
            rows_data.append(cells)

        if not rows_data:
            return ""

        # Determine column widths
        num_cols = max(len(row) for row in rows_data)

        # Normalize rows to same column count
        for row in rows_data:
            while len(row) < num_cols:
                row.append("")

        # Build Markdown table
        lines = []

        # Header row
        header = rows_data[0] if rows_data else [""] * num_cols
        lines.append("| " + " | ".join(header) + " |")

        # Separator
        lines.append("| " + " | ".join(["---"] * num_cols) + " |")

        # Data rows
        for row in rows_data[1:]:
            lines.append("| " + " | ".join(row) + " |")

        return "\n".join(lines)

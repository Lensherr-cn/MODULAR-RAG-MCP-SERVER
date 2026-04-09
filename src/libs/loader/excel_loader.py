"""Excel spreadsheet loader.

This module implements loading and parsing of Excel spreadsheets,
converting them to Markdown format for consistent RAG processing.

Features:
- Multi-sheet support
- Smart table-to-text conversion
- Configurable row limit per sheet
- SHA256-based document ID

Dependencies:
    openpyxl>=3.1.0
"""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.core.types import Document
from src.libs.loader.base_loader import BaseLoader

logger = logging.getLogger(__name__)

# Check for openpyxl availability
try:
    from openpyxl import load_workbook
    from openpyxl.worksheet.worksheet import Worksheet
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False
    logger.warning(
        "openpyxl is not installed. ExcelLoader will not be available. "
        "Install with: pip install openpyxl"
    )


class ExcelLoader(BaseLoader):
    """Excel spreadsheet loader (.xlsx, .xls).

    This loader reads Excel files and converts them to Markdown format,
    with each sheet becoming a separate section.

    The loader:
    1. Parses the Excel file using openpyxl
    2. Converts each sheet to a Markdown section
    3. Converts tables to Markdown table format
    4. Computes SHA256 hash for document ID

    Example:
        >>> loader = ExcelLoader(max_rows_per_sheet=100)
        >>> doc = loader.load("data/sales.xlsx")
        >>> print(doc.metadata["sheet_count"])
    """

    SUPPORTED_EXTENSIONS = {".xlsx", ".xls"}

    def __init__(
        self,
        max_rows_per_sheet: int = 100,
        include_empty_sheets: bool = False,
        include_hidden_sheets: bool = False,
        **kwargs,
    ):
        """Initialize Excel Loader.

        Args:
            max_rows_per_sheet: Maximum rows to include per sheet.
                Set to 0 or negative for unlimited.
            include_empty_sheets: Whether to include sheets with no data.
            include_hidden_sheets: Whether to include hidden sheets.
            **kwargs: Ignored (for compatibility with LoaderFactory).
        """
        if not OPENPYXL_AVAILABLE:
            raise ImportError(
                "openpyxl is required for ExcelLoader. "
                "Install with: pip install openpyxl"
            )

        self.max_rows_per_sheet = max(0, max_rows_per_sheet) if max_rows_per_sheet > 0 else 0
        self.include_empty_sheets = include_empty_sheets
        self.include_hidden_sheets = include_hidden_sheets

    def load(self, file_path: str | Path) -> Document:
        """Load and parse an Excel spreadsheet.

        Args:
            file_path: Path to the Excel file.

        Returns:
            Document with Markdown text and metadata.

        Raises:
            FileNotFoundError: If the file doesn't exist.
            ValueError: If the file is not an Excel file.
            ImportError: If openpyxl is not installed.
        """
        # Validate file
        path = self._validate_file(file_path)

        if path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"File is not an Excel file: {path}. "
                f"Supported extensions: {self.SUPPORTED_EXTENSIONS}"
            )

        # Compute file hash for document ID
        doc_hash = self._compute_file_hash(path)
        doc_id = f"doc_{doc_hash[:16]}"

        # Parse Excel file
        try:
            # data_only=True to get computed values, not formulas
            workbook = load_workbook(str(path), read_only=True, data_only=True)
        except Exception as e:
            raise RuntimeError(f"Failed to parse Excel file: {e}") from e

        # Convert to Markdown
        markdown_text, stats = self._convert_to_markdown(workbook, path)

        workbook.close()

        # Build metadata
        metadata: Dict[str, Any] = {
            "source_path": str(path),
            "doc_type": "excel",
            "doc_hash": doc_hash,
            "char_count": len(markdown_text),
            "sheet_count": stats["sheet_count"],
            "total_rows": stats["total_rows"],
            "sheets": stats["sheets"],
        }

        # Use filename as title if no better title found
        title = stats.get("title") or path.stem
        metadata["title"] = title

        logger.debug(
            f"Loaded Excel file: {path.name}, "
            f"{stats['sheet_count']} sheets, {stats['total_rows']} total rows"
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
        workbook,
        file_path: Path
    ) -> tuple[str, Dict[str, Any]]:
        """Convert Excel workbook to Markdown format.

        Args:
            workbook: openpyxl Workbook object.
            file_path: Original file path for metadata.

        Returns:
            Tuple of (markdown text, statistics dict).
        """
        sections: List[str] = []
        stats = {
            "sheet_count": 0,
            "total_rows": 0,
            "sheets": [],
            "title": None,
        }

        # Add document title
        title = file_path.stem
        sections.append(f"# {title}\n")

        for sheet_name in workbook.sheetnames:
            sheet = workbook[sheet_name]

            # Skip hidden sheets if configured
            if not self.include_hidden_sheets and sheet.sheet_state != "visible":
                continue

            # Convert sheet to Markdown section
            sheet_md, sheet_stats = self._convert_sheet_to_markdown(
                sheet, sheet_name
            )

            # Skip empty sheets if configured
            if not self.include_empty_sheets and sheet_stats["row_count"] == 0:
                continue

            sections.append(sheet_md)
            stats["sheet_count"] += 1
            stats["total_rows"] += sheet_stats["row_count"]
            stats["sheets"].append({
                "name": sheet_name,
                "rows": sheet_stats["row_count"],
                "columns": sheet_stats["column_count"],
            })

        markdown_text = "\n\n".join(sections)

        # Use first sheet name as subtitle if available
        if stats["sheets"]:
            stats["title"] = f"{title} - {stats['sheets'][0]['name']}"

        return markdown_text, stats

    def _convert_sheet_to_markdown(
        self,
        sheet: "Worksheet",
        sheet_name: str
    ) -> tuple[str, Dict[str, Any]]:
        """Convert a single sheet to Markdown format.

        Args:
            sheet: openpyxl Worksheet object.
            sheet_name: Name of the sheet.

        Returns:
            Tuple of (markdown section, sheet statistics).
        """
        stats = {
            "row_count": 0,
            "column_count": 0,
        }

        # Get dimensions
        max_row = sheet.max_row or 0
        max_col = sheet.max_column or 0

        if max_row == 0 or max_col == 0:
            return f"## Sheet: {sheet_name}\n\n*(Empty sheet)*\n", stats

        # Apply row limit
        if self.max_rows_per_sheet > 0 and max_row > self.max_rows_per_sheet:
            max_row = self.max_rows_per_sheet

        # Read all rows
        rows_data: List[List[str]] = []
        for row_idx in range(1, max_row + 1):
            row_values = []
            for col_idx in range(1, max_col + 1):
                cell = sheet.cell(row=row_idx, column=col_idx)
                value = cell.value
                # Convert to string, handle None
                if value is None:
                    row_values.append("")
                else:
                    row_values.append(str(value).strip())
            rows_data.append(row_values)

        stats["row_count"] = len(rows_data)
        stats["column_count"] = max_col

        if not rows_data:
            return f"## Sheet: {sheet_name}\n\n*(No data)*\n", stats

        # Build Markdown table
        lines = [f"## Sheet: {sheet_name}\n"]

        # Check if first row looks like a header
        has_header = self._is_header_row(rows_data[0]) if rows_data else False

        # Header row
        header = rows_data[0] if rows_data else [""] * max_col
        lines.append("| " + " | ".join(header) + " |")
        lines.append("| " + " | ".join(["---"] * max_col) + " |")

        # Data rows
        data_start = 1 if has_header else 0
        for row in rows_data[data_start:]:
            lines.append("| " + " | ".join(row) + " |")

        # Add summary if data was truncated
        total_rows = sheet.max_row or 0
        if self.max_rows_per_sheet > 0 and total_rows > self.max_rows_per_sheet:
            lines.append(f"\n*... showing {self.max_rows_per_sheet} of {total_rows} rows*")

        return "\n".join(lines), stats

    def _is_header_row(self, row: List[str]) -> bool:
        """Check if a row looks like a header row.

        Headers typically have:
        - Non-empty values
        - Short text (column names)
        - No numeric values

        Args:
            row: List of cell values.

        Returns:
            True if row looks like a header.
        """
        if not row:
            return False

        non_empty = [v for v in row if v]
        if not non_empty:
            return False

        # Check if most values are short and non-numeric
        short_count = sum(1 for v in non_empty if len(v) <= 30)
        numeric_count = sum(1 for v in non_empty if self._is_numeric(v))

        # If most values are short and not numeric, likely a header
        return short_count >= len(non_empty) * 0.7 and numeric_count < len(non_empty) * 0.5

    def _is_numeric(self, value: str) -> bool:
        """Check if a string value is numeric.

        Args:
            value: String to check.

        Returns:
            True if value appears to be numeric.
        """
        try:
            float(value.replace(",", "").replace("%", ""))
            return True
        except (ValueError, AttributeError):
            return False

"""Factory for creating Loader instances based on file type.

This module implements the Factory Pattern for document loaders,
providing a centralized mechanism to select and instantiate
the appropriate loader based on file extension.

Design Principles:
- Factory Pattern: Centralizes loader selection logic
- Config-Driven: Selection based on file extension
- Fail-Fast: Clear errors for unsupported formats
- Extensible: New loaders can be registered dynamically
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from src.libs.loader.base_loader import BaseLoader

logger = logging.getLogger(__name__)


class LoaderFactory:
    """Factory for creating Loader instances based on file extension.

    This factory maintains a registry of loaders mapped to file extensions
    and provides methods to create the appropriate loader for a given file.

    Example:
        >>> loader = LoaderFactory.create("document.pdf")
        >>> doc = loader.load("document.pdf")

        >>> # Check supported formats
        >>> extensions = LoaderFactory.supported_extensions()
        >>> print(extensions)
        ['.pdf', '.md', '.txt', '.docx', '.xlsx']
    """

    # Registry mapping loader name to loader class
    _LOADERS: dict[str, type[BaseLoader]] = {}

    # Mapping from file extension to loader name
    _EXTENSION_MAP: dict[str, str] = {
        # PDF
        ".pdf": "pdf",
        # Markdown
        ".md": "markdown",
        ".markdown": "markdown",
        # Text
        ".txt": "text",
        # Word
        ".docx": "word",
        ".doc": "word",
        # Excel
        ".xlsx": "excel",
        ".xls": "excel",
    }

    @classmethod
    def create(
        cls,
        file_path: str | Path,
        **kwargs: Any
    ) -> BaseLoader:
        """Create appropriate loader based on file extension.

        Args:
            file_path: Path to the file (used to determine extension).
            **kwargs: Additional arguments passed to the loader constructor.

        Returns:
            Instance of the appropriate loader for the file type.

        Raises:
            ValueError: If the file extension is not supported.

        Example:
            >>> loader = LoaderFactory.create("report.pdf", extract_images=True)
            >>> doc = loader.load("report.pdf")
        """
        loader_name = cls.get_loader_name(file_path)

        if loader_name not in cls._LOADERS:
            # Lazy import and register loaders
            cls._register_loader(loader_name)

        if loader_name not in cls._LOADERS:
            raise ValueError(
                f"No loader registered for '{loader_name}'. "
                f"Supported formats: {cls.supported_extensions()}"
            )

        loader_class = cls._LOADERS[loader_name]
        return loader_class(**kwargs)

    @classmethod
    def get_loader_name(cls, file_path: str | Path) -> str:
        """Get the loader name for a file path.

        Args:
            file_path: Path to the file.

        Returns:
            Loader name (e.g., 'pdf', 'markdown', 'word').

        Raises:
            ValueError: If the file extension is not supported.
        """
        path = Path(file_path)
        ext = path.suffix.lower()

        if ext not in cls._EXTENSION_MAP:
            raise ValueError(
                f"Unsupported file extension: '{ext}'. "
                f"Supported extensions: {cls.supported_extensions()}"
            )

        return cls._EXTENSION_MAP[ext]

    @classmethod
    def register_loader(
        cls,
        name: str,
        loader_class: type[BaseLoader],
        extensions: list[str]
    ) -> None:
        """Register a new loader with its supported extensions.

        Args:
            name: Unique name for the loader (e.g., 'pdf', 'markdown').
            loader_class: The loader class to register.
            extensions: List of file extensions this loader supports.

        Example:
            >>> class MyLoader(BaseLoader):
            ...     def load(self, file_path): ...
            >>> LoaderFactory.register_loader('myformat', MyLoader, ['.myf'])
        """
        cls._LOADERS[name] = loader_class

        for ext in extensions:
            ext_lower = ext.lower()
            if not ext_lower.startswith('.'):
                ext_lower = f'.{ext_lower}'
            cls._EXTENSION_MAP[ext_lower] = name

        logger.debug(f"Registered loader '{name}' for extensions: {extensions}")

    @classmethod
    def supported_extensions(cls) -> list[str]:
        """List all supported file extensions.

        Returns:
            Sorted list of supported file extensions.
        """
        return sorted(cls._EXTENSION_MAP.keys())

    @classmethod
    def _register_loader(cls, name: str) -> None:
        """Lazy import and register a loader by name.

        This method handles the actual import of loader modules
        to avoid circular imports and reduce initial load time.

        Args:
            name: Loader name to register.
        """
        if name in cls._LOADERS:
            return

        try:
            if name == "pdf":
                from src.libs.loader.pdf_loader import PdfLoader
                cls._LOADERS[name] = PdfLoader
            elif name == "markdown":
                from src.libs.loader.markdown_loader import MarkdownLoader
                cls._LOADERS[name] = MarkdownLoader
            elif name == "text":
                from src.libs.loader.text_loader import TextLoader
                cls._LOADERS[name] = TextLoader
            elif name == "word":
                from src.libs.loader.word_loader import WordLoader
                cls._LOADERS[name] = WordLoader
            elif name == "excel":
                from src.libs.loader.excel_loader import ExcelLoader
                cls._LOADERS[name] = ExcelLoader
            else:
                logger.warning(f"Unknown loader name: {name}")
        except ImportError as e:
            logger.error(f"Failed to import loader '{name}': {e}")

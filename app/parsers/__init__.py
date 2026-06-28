"""
Document parsers package.

Provides a factory function to get the appropriate parser based on file type.
"""

from pathlib import Path

from .base import BaseParser, Document
from .pdf_parser import PDFParser
from .word_parser import WordParser
from .excel_parser import ExcelParser
from .image_parser import ImageParser
from .text_parser import TextParser

# Registry of all available parsers
_PARSERS: list[type[BaseParser]] = [
    PDFParser,
    WordParser,
    ExcelParser,
    ImageParser,
    TextParser,
]

# Mapping from extension to parser class
_EXT_MAP: dict[str, type[BaseParser]] = {}
for _parser_cls in _PARSERS:
    for _ext in _parser_cls.SUPPORTED_EXTENSIONS:
        _EXT_MAP[_ext] = _parser_cls


def get_parser(file_path: str | Path) -> BaseParser:
    """
    Get the appropriate parser for the given file.

    Args:
        file_path: Path to the file.

    Returns:
        An instance of the appropriate parser.

    Raises:
        ValueError: If no parser is available for the file type.
    """
    ext = Path(file_path).suffix.lower()
    parser_cls = _EXT_MAP.get(ext)
    if parser_cls is None:
        supported = ", ".join(sorted(_EXT_MAP.keys()))
        raise ValueError(
            f"Unsupported file type: '{ext}'. Supported types: {supported}"
        )
    return parser_cls()


def get_supported_extensions() -> list[str]:
    """Return list of all supported file extensions."""
    return sorted(_EXT_MAP.keys())


__all__ = [
    "BaseParser",
    "Document",
    "PDFParser",
    "WordParser",
    "ExcelParser",
    "ImageParser",
    "TextParser",
    "get_parser",
    "get_supported_extensions",
]

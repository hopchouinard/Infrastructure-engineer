"""
PDF to Markdown converter.

Extracts text content from PDF files and converts to Markdown.
Features:
- Text extraction with layout preservation
- Table detection and formatting
- Image placeholder insertion
- Metadata extraction

TODO: Implement in task F1.6
"""

from pathlib import Path
from typing import Any, Protocol

__all__ = ["PDFConverter"]


class PDFConverter(Protocol):
    """Protocol for PDF to Markdown conversion."""

    def convert(self, pdf_content: bytes) -> str:
        """Convert PDF content to Markdown.

        Args:
            pdf_content: Raw PDF file bytes.

        Returns:
            Markdown representation of the PDF content.
        """
        ...

    def convert_file(self, path: Path) -> str:
        """Convert a PDF file to Markdown.

        Args:
            path: Path to the PDF file.

        Returns:
            Markdown representation of the PDF content.
        """
        ...

    def extract_metadata(self, pdf_content: bytes) -> dict[str, Any]:
        """Extract metadata from PDF content.

        Args:
            pdf_content: Raw PDF file bytes.

        Returns:
            Dictionary of metadata (title, author, creation date, etc.).
        """
        ...

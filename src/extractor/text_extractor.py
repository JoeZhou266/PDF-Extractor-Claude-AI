"""Extract text from text-based (selectable-text) PDF files using pdfplumber."""

from __future__ import annotations

import logging
from pathlib import Path

import pdfplumber

_logger = logging.getLogger(__name__)


def extract_text_from_pdf(pdf_path: str | Path) -> str:
    """Extract all text from a selectable-text PDF.

    Args:
        pdf_path: Path to the PDF file.

    Returns:
        Concatenated text from all pages, separated by newlines.

    Raises:
        FileNotFoundError: If *pdf_path* does not exist.
        ValueError: If no text could be extracted (likely an image-based PDF).
    """
    _logger.debug("extract_text_from_pdf: start pdf_path=%s", pdf_path)
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {path}")

    pages: list[str] = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            pages.append(text)

    full_text = "\n".join(pages).strip()
    if not full_text:
        raise ValueError(f"No selectable text found in {path}. Consider OCR extraction.")

    _logger.debug("extract_text_from_pdf: complete pdf_path=%s pages=%d chars=%d", pdf_path, len(pages), len(full_text))
    return full_text

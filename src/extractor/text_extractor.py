"""Extract text from text-based (selectable-text) PDF files using pdfplumber."""

from __future__ import annotations

from pathlib import Path

import pdfplumber


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

    return full_text

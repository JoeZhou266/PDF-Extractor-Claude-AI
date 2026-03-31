"""Dispatch PDF text extraction to text-based or OCR/ICR extractor based on filename patterns."""

from __future__ import annotations

import fnmatch
from pathlib import Path

from .ocr_extractor import extract_text_via_ocr
from .text_extractor import extract_text_from_pdf


def is_ocr_pdf(filename: str, ocr_patterns: list[str]) -> bool:
    """Return True if *filename* matches any pattern in *ocr_patterns*.

    Args:
        filename: Base name of the PDF file (no directory component).
        ocr_patterns: List of glob-style patterns, e.g. ``["scanned_*.pdf"]``.

    Returns:
        ``True`` if the file should be processed with OCR.
    """
    for pattern in ocr_patterns:
        if fnmatch.fnmatch(filename.lower(), pattern.strip().lower()):
            return True
    return False


def extract_text(
    pdf_path: str | Path,
    ocr_patterns: list[str] | None = None,
    ocr_dpi: int = 300,
    ocr_lang: str = "eng",
) -> str:
    """Extract text from *pdf_path*, choosing text or OCR strategy automatically.

    First checks filename against *ocr_patterns*. If no pattern matches, attempts
    direct text extraction. Falls back to OCR if direct extraction yields nothing.

    Args:
        pdf_path: Path to the PDF file.
        ocr_patterns: Glob patterns that force OCR (from config ``[extractor] ocr_filename_patterns``).
        ocr_dpi: DPI passed to :func:`extract_text_via_ocr`.
        ocr_lang: Language(s) passed to Tesseract.

    Returns:
        Extracted text string.
    """
    path = Path(pdf_path)
    patterns = ocr_patterns or []

    if is_ocr_pdf(path.name, patterns):
        return extract_text_via_ocr(path, dpi=ocr_dpi, lang=ocr_lang)

    try:
        text = extract_text_from_pdf(path)
        return text
    except ValueError:
        # No selectable text — fall back to OCR
        return extract_text_via_ocr(path, dpi=ocr_dpi, lang=ocr_lang)

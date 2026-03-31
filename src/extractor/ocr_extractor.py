"""Extract text from image-based PDF files using pdf2image + Tesseract OCR."""

from __future__ import annotations

from pathlib import Path

import pytesseract
from pdf2image import convert_from_path
from PIL.Image import Image


def extract_text_via_ocr(pdf_path: str | Path, dpi: int = 300, lang: str = "eng") -> str:
    """Render each PDF page to an image and run Tesseract OCR on it.

    Args:
        pdf_path: Path to the PDF file.
        dpi: Rendering resolution. Higher values improve accuracy but increase memory use.
        lang: Tesseract language code(s), e.g. ``"eng"`` or ``"eng+fra"``.

    Returns:
        Concatenated OCR text from all pages.

    Raises:
        FileNotFoundError: If *pdf_path* does not exist.
        RuntimeError: If Tesseract is not installed or not on PATH.
    """
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {path}")

    try:
        images: list[Image] = convert_from_path(str(path), dpi=dpi)
    except Exception as exc:
        raise RuntimeError(f"pdf2image failed to render {path}: {exc}") from exc

    pages: list[str] = []
    for image in images:
        try:
            text: str = pytesseract.image_to_string(image, lang=lang)
        except pytesseract.TesseractNotFoundError as exc:
            raise RuntimeError(
                "Tesseract OCR is not installed or not found on PATH. "
                "Install it from https://github.com/UB-Mannheim/tesseract/wiki"
            ) from exc
        pages.append(text)

    return "\n".join(pages).strip()

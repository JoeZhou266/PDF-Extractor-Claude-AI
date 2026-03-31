"""Tests for src/extractor."""

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

from src.extractor.extractor import is_ocr_pdf, extract_text


class TestIsOcrPdf:
    def test_matches_exact_pattern(self):
        assert is_ocr_pdf("scanned_invoice.pdf", ["scanned_*.pdf"])

    def test_no_match_returns_false(self):
        assert not is_ocr_pdf("invoice_2024.pdf", ["scanned_*.pdf"])

    def test_case_insensitive(self):
        assert is_ocr_pdf("SCANNED_doc.PDF", ["scanned_*.pdf"])

    def test_multiple_patterns(self):
        assert is_ocr_pdf("scan_001.pdf", ["scanned_*.pdf", "scan_*.pdf"])

    def test_empty_patterns(self):
        assert not is_ocr_pdf("anything.pdf", [])


class TestExtractText:
    def test_text_based_pdf_success(self, tmp_path):
        pdf = tmp_path / "doc.pdf"
        pdf.write_bytes(b"%PDF dummy")

        with patch("src.extractor.extractor.extract_text_from_pdf", return_value="hello world") as mock_text:
            result = extract_text(pdf, ocr_patterns=[])

        mock_text.assert_called_once_with(pdf)
        assert result == "hello world"

    def test_falls_back_to_ocr_when_no_text(self, tmp_path):
        pdf = tmp_path / "image_doc.pdf"
        pdf.write_bytes(b"%PDF dummy")

        with patch("src.extractor.extractor.extract_text_from_pdf", side_effect=ValueError("no text")):
            with patch("src.extractor.extractor.extract_text_via_ocr", return_value="ocr result") as mock_ocr:
                result = extract_text(pdf, ocr_patterns=[])

        mock_ocr.assert_called_once()
        assert result == "ocr result"

    def test_ocr_pattern_skips_text_extraction(self, tmp_path):
        pdf = tmp_path / "scanned_invoice.pdf"
        pdf.write_bytes(b"%PDF dummy")

        with patch("src.extractor.extractor.extract_text_via_ocr", return_value="ocr text") as mock_ocr:
            with patch("src.extractor.extractor.extract_text_from_pdf") as mock_text:
                result = extract_text(pdf, ocr_patterns=["scanned_*.pdf"])

        mock_text.assert_not_called()
        mock_ocr.assert_called_once()
        assert result == "ocr text"

    def test_missing_file_raises(self, tmp_path):
        with patch("src.extractor.extractor.extract_text_from_pdf", side_effect=FileNotFoundError):
            with pytest.raises(FileNotFoundError):
                extract_text(tmp_path / "missing.pdf")

"""Tests for src/config."""

import configparser
from pathlib import Path

import pytest

from src.config import load_config


def write_config(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


class TestLoadConfig:
    def test_loads_defaults_when_file_missing(self, tmp_path):
        cfg = load_config(tmp_path / "nonexistent.ini")
        assert cfg.input_dir == "pdfs/input"
        assert cfg.thread_pool_size == 4
        assert cfg.model == "claude-sonnet-4-6"

    def test_overrides_from_file(self, tmp_path):
        ini = tmp_path / "config.ini"
        write_config(ini, """
[worker]
thread_pool_size = 8

[transformer]
model = claude-opus-4-6
max_tokens = 2048
""")
        cfg = load_config(ini)
        assert cfg.thread_pool_size == 8
        assert cfg.model == "claude-opus-4-6"
        assert cfg.max_tokens == 2048

    def test_ocr_patterns_parsed_as_list(self, tmp_path):
        ini = tmp_path / "config.ini"
        write_config(ini, """
[extractor]
ocr_filename_patterns = scanned_*.pdf, scan_*.pdf, fax_*.pdf
""")
        cfg = load_config(ini)
        assert cfg.ocr_filename_patterns == ["scanned_*.pdf", "scan_*.pdf", "fax_*.pdf"]

    def test_empty_ocr_patterns(self, tmp_path):
        ini = tmp_path / "config.ini"
        write_config(ini, "[extractor]\nocr_filename_patterns =\n")
        cfg = load_config(ini)
        assert cfg.ocr_filename_patterns == []

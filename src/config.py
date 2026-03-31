"""Load and expose application configuration from config.ini and environment variables."""

from __future__ import annotations

import configparser
import logging
import os
from dataclasses import dataclass
from pathlib import Path

_logger = logging.getLogger(__name__)


@dataclass
class AppConfig:
    """All runtime configuration values."""

    # Paths
    input_dir: str
    output_dir: str
    processed_dir: str
    error_dir: str
    training_dir: str
    log_dir: str

    # Worker
    thread_pool_size: int

    # Extractor
    ocr_filename_patterns: list[str]
    ocr_dpi: int
    ocr_lang: str

    # Transformer
    model: str
    max_tokens: int

    # Logging
    log_level: str
    log_file_prefix: str


def load_config(config_path: str | Path = "config.ini") -> AppConfig:
    """Parse *config_path* and return an :class:`AppConfig`.

    Command-line overrides are not applied here; see ``main.py`` for that layer.

    Args:
        config_path: Path to the INI configuration file.

    Returns:
        Populated :class:`AppConfig` instance.
    """
    _logger.debug("load_config: start config_path=%s", config_path)
    parser = configparser.ConfigParser()
    parser.read(str(config_path), encoding="utf-8")

    def get(section: str, key: str, fallback: str) -> str:
        return parser.get(section, key, fallback=fallback)

    ocr_raw = get("extractor", "ocr_filename_patterns", "")
    ocr_patterns = [p.strip() for p in ocr_raw.split(",") if p.strip()]

    _logger.debug("load_config: complete config_path=%s", config_path)
    return AppConfig(
        input_dir=get("paths", "input_dir", "pdfs/input"),
        output_dir=get("paths", "output_dir", "pdfs/output"),
        processed_dir=get("paths", "processed_dir", "pdfs/processed"),
        error_dir=get("paths", "error_dir", "pdfs/error"),
        training_dir=get("paths", "training_dir", "pdfs/training"),
        log_dir=get("paths", "log_dir", "log"),
        thread_pool_size=int(get("worker", "thread_pool_size", "4")),
        ocr_filename_patterns=ocr_patterns,
        ocr_dpi=int(get("extractor", "ocr_dpi", "300")),
        ocr_lang=get("extractor", "ocr_lang", "eng"),
        model=get("transformer", "model", "claude-sonnet-4-6"),
        max_tokens=int(get("transformer", "max_tokens", "4096")),
        log_level=get("logging", "log_level", "INFO"),
        log_file_prefix=get("logging", "log_file_prefix", "app"),
    )

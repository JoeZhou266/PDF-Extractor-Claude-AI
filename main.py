"""Entry point for the PDF Extractor application.
# Python 3.9 compatibility: defer annotation evaluation
from __future__ import annotations


Usage examples::

    # Watch pdfs/input continuously (default config)
    python main.py

    # Override number of threads and log level
    python main.py --threads 8 --log-level DEBUG

    # Use a custom config file and input directory
    python main.py --config my_config.ini --input-dir /data/pdfs

    # Process a single PDF file without starting the watcher
    python main.py --file invoice.pdf
"""

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from src.config import load_config
from src.gateway import FileWatcherGateway
from src.logger import get_logger
from src.transformer.transformer import Transformer, save_output
from src.extractor import extract_text
from src.worker import ProcessingWorker


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="PDF Extractor — convert PDFs to structured JSON via Claude AI"
    )
    parser.add_argument("--config", default="config.ini", help="Path to config.ini (default: config.ini)")
    parser.add_argument("--input-dir", help="Override [paths] input_dir from config")
    parser.add_argument("--output-dir", help="Override [paths] output_dir from config")
    parser.add_argument("--threads", type=int, help="Override [worker] thread_pool_size from config")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                        help="Override [logging] log_level from config")
    parser.add_argument("--file", help="Process a single PDF file then exit (no watcher)")
    return parser.parse_args()


def main() -> None:
    load_dotenv()

    args = parse_args()
    cfg = load_config(args.config)

    # Apply CLI overrides
    if args.input_dir:
        cfg.input_dir = args.input_dir
    if args.output_dir:
        cfg.output_dir = args.output_dir
    if args.threads:
        cfg.thread_pool_size = args.threads
    if args.log_level:
        cfg.log_level = args.log_level

    log = get_logger(
        "main",
        log_dir=cfg.log_dir,
        log_level=cfg.log_level,
        log_file_prefix=cfg.log_file_prefix,
    )

    log.info("Starting PDF Extractor (model=%s, threads=%d)", cfg.model, cfg.thread_pool_size)

    try:
        transformer = Transformer(model=cfg.model, max_tokens=cfg.max_tokens)
    except EnvironmentError as exc:
        log.error("%s", exc)
        sys.exit(1)

    if args.file:
        # ── Single-file mode ──────────────────────────────────────────────
        pdf_path = Path(args.file)
        if not pdf_path.exists():
            log.error("File not found: %s", pdf_path)
            sys.exit(1)

        log.info("Single-file mode: %s", pdf_path)
        text = extract_text(
            pdf_path,
            ocr_patterns=cfg.ocr_filename_patterns,
            ocr_dpi=cfg.ocr_dpi,
            ocr_lang=cfg.ocr_lang,
        )
        output = transformer.transform(text)
        json_path = Path(cfg.output_dir) / (pdf_path.stem + ".json")
        save_output(output, json_path)
        log.info("Output written to: %s", json_path)
        return

    # ── Continuous watch mode ─────────────────────────────────────────────
    worker = ProcessingWorker(
        thread_pool_size=cfg.thread_pool_size,
        output_dir=cfg.output_dir,
        processed_dir=cfg.processed_dir,
        error_dir=cfg.error_dir,
        transformer=transformer,
        ocr_patterns=cfg.ocr_filename_patterns,
        ocr_dpi=cfg.ocr_dpi,
        ocr_lang=cfg.ocr_lang,
        log_dir=cfg.log_dir,
        log_level=cfg.log_level,
        log_file_prefix=cfg.log_file_prefix,
    )

    gateway = FileWatcherGateway(
        input_dir=cfg.input_dir,
        worker=worker,
        log_dir=cfg.log_dir,
        log_level=cfg.log_level,
        log_file_prefix=cfg.log_file_prefix,
    )

    gateway.run_forever()


if __name__ == "__main__":
    main()

"""Thread-pool worker that processes PDFs submitted by the file-watcher gateway."""

from __future__ import annotations

import shutil
from concurrent.futures import ThreadPoolExecutor, Future
from pathlib import Path
from typing import Callable

from src.extractor import extract_text
from src.logger import get_logger
from src.transformer.transformer import Transformer, save_output


class ProcessingWorker:
    """Manages a fixed thread pool that converts PDFs to JSON.

    Each submitted PDF is processed independently:
    1. Text is extracted (text-based or OCR).
    2. Claude AI transforms the text to structured JSON.
    3. The JSON is written to *output_dir*.
    4. The source PDF is moved to *processed_dir* on success or *error_dir* on failure.

    Args:
        thread_pool_size: Maximum concurrent worker threads.
        output_dir: Directory where output JSON files are written.
        processed_dir: PDFs are moved here after successful processing.
        error_dir: PDFs are moved here when processing fails.
        transformer: :class:`~src.transformer.Transformer` instance to reuse.
        ocr_patterns: Filename glob patterns that force OCR extraction.
        ocr_dpi: DPI for pdf2image rendering.
        ocr_lang: Tesseract language code(s).
        log_dir: Directory for log files.
        log_level: Logging verbosity.
        log_file_prefix: Log filename prefix.
        on_complete: Optional callback invoked with the PDF path after each job finishes.
    """

    def __init__(
        self,
        thread_pool_size: int = 4,
        output_dir: str = "pdfs/output",
        processed_dir: str = "pdfs/processed",
        error_dir: str = "pdfs/error",
        transformer: Transformer | None = None,
        ocr_patterns: list[str] | None = None,
        ocr_dpi: int = 300,
        ocr_lang: str = "eng",
        log_dir: str = "log",
        log_level: str = "INFO",
        log_file_prefix: str = "app",
        on_complete: Callable[[Path], None] | None = None,
    ) -> None:
        self._output_dir = Path(output_dir)
        self._processed_dir = Path(processed_dir)
        self._error_dir = Path(error_dir)
        self._transformer = transformer or Transformer()
        self._ocr_patterns = ocr_patterns or []
        self._ocr_dpi = ocr_dpi
        self._ocr_lang = ocr_lang
        self._on_complete = on_complete
        self._log = get_logger(__name__, log_dir=log_dir, log_level=log_level, log_file_prefix=log_file_prefix)
        self._executor = ThreadPoolExecutor(max_workers=thread_pool_size)

        for d in (self._output_dir, self._processed_dir, self._error_dir):
            d.mkdir(parents=True, exist_ok=True)

    def submit(self, pdf_path: str | Path) -> Future:
        """Submit a PDF file for asynchronous processing.

        Args:
            pdf_path: Path to the PDF file to process.

        Returns:
            A :class:`~concurrent.futures.Future` for the processing job.
        """
        return self._executor.submit(self._process, Path(pdf_path))

    def shutdown(self, wait: bool = True) -> None:
        """Shut down the thread pool.

        Args:
            wait: If True, block until all pending jobs complete.
        """
        self._executor.shutdown(wait=wait)

    # ── Private ───────────────────────────────────────────────────────────

    def _process(self, pdf_path: Path) -> None:
        """Worker task: extract → transform → save → move PDF."""
        self._log.info("Processing started: %s", pdf_path.name)
        try:
            text = extract_text(
                pdf_path,
                ocr_patterns=self._ocr_patterns,
                ocr_dpi=self._ocr_dpi,
                ocr_lang=self._ocr_lang,
            )
            output = self._transformer.transform(text)

            json_name = pdf_path.stem + ".json"
            save_output(output, self._output_dir / json_name)

            dest = self._processed_dir / pdf_path.name
            shutil.move(str(pdf_path), dest)
            self._log.info("Processing complete: %s → %s", pdf_path.name, json_name)

        except Exception:
            self._log.exception("Processing failed: %s", pdf_path.name)
            try:
                dest = self._error_dir / pdf_path.name
                shutil.move(str(pdf_path), dest)
            except Exception:
                self._log.exception("Could not move failed PDF to error dir: %s", pdf_path.name)

        finally:
            if self._on_complete:
                self._on_complete(pdf_path)

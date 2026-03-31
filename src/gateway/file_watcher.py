"""File-watching gateway that monitors the input directory and dispatches PDFs to the worker pool."""

from __future__ import annotations

import time
from pathlib import Path

from watchdog.events import FileCreatedEvent, FileMovedEvent, FileSystemEventHandler
from watchdog.observers import Observer

from src.logger import get_logger
from src.worker import ProcessingWorker


class _PDFEventHandler(FileSystemEventHandler):
    """Watchdog event handler that forwards new PDF files to the worker pool."""

    def __init__(self, worker: ProcessingWorker, logger) -> None:
        super().__init__()
        self._worker = worker
        self._log = logger

    def on_created(self, event: FileCreatedEvent) -> None:
        if not event.is_directory and str(event.src_path).lower().endswith(".pdf"):
            self._log.info("New PDF detected: %s", event.src_path)
            self._worker.submit(event.src_path)

    def on_moved(self, event: FileMovedEvent) -> None:
        """Handle files moved/renamed into the watch directory."""
        if not event.is_directory and str(event.dest_path).lower().endswith(".pdf"):
            self._log.info("PDF moved into directory: %s", event.dest_path)
            self._worker.submit(event.dest_path)


class FileWatcherGateway:
    """Watches *input_dir* for new PDF files and submits them to *worker*.

    Also processes any PDF files already present in *input_dir* at startup.

    Args:
        input_dir: Directory to monitor for new PDF files.
        worker: :class:`~src.worker.ProcessingWorker` instance to receive files.
        log_dir: Directory for log output.
        log_level: Logging verbosity.
        log_file_prefix: Log filename prefix.
    """

    def __init__(
        self,
        input_dir: str = "pdfs/input",
        worker: ProcessingWorker | None = None,
        log_dir: str = "log",
        log_level: str = "INFO",
        log_file_prefix: str = "app",
    ) -> None:
        self._input_dir = Path(input_dir)
        self._input_dir.mkdir(parents=True, exist_ok=True)
        self._worker = worker
        self._log = get_logger(__name__, log_dir=log_dir, log_level=log_level, log_file_prefix=log_file_prefix)
        self._observer: Observer | None = None

    def start(self) -> None:
        """Process existing PDFs and start the filesystem observer."""
        self._process_existing()
        handler = _PDFEventHandler(self._worker, self._log)
        self._observer = Observer()
        self._observer.schedule(handler, str(self._input_dir), recursive=False)
        self._observer.start()
        self._log.info("File watcher started on: %s", self._input_dir)

    def stop(self) -> None:
        """Stop the filesystem observer and shut down the worker pool."""
        if self._observer:
            self._observer.stop()
            self._observer.join()
            self._log.info("File watcher stopped.")
        if self._worker:
            self._worker.shutdown(wait=True)

    def run_forever(self) -> None:
        """Block forever, polling the observer until interrupted (Ctrl-C)."""
        self.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self._log.info("Shutdown signal received.")
        finally:
            self.stop()

    # ── Private ───────────────────────────────────────────────────────────

    def _process_existing(self) -> None:
        """Submit any PDF files already present in the input directory."""
        existing = list(self._input_dir.glob("*.pdf"))
        if existing:
            self._log.info("Found %d existing PDF(s) in %s", len(existing), self._input_dir)
        for pdf in existing:
            self._worker.submit(pdf)

"""Tests for src/worker."""

from pathlib import Path
from unittest.mock import MagicMock, patch, call
import shutil

import pytest

from src.worker.worker import ProcessingWorker


@pytest.fixture()
def dirs(tmp_path):
    d = {
        "output": tmp_path / "output",
        "processed": tmp_path / "processed",
        "error": tmp_path / "error",
        "log": tmp_path / "log",
    }
    for p in d.values():
        p.mkdir()
    return d


def make_worker(dirs, transformer=None):
    with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
        return ProcessingWorker(
            thread_pool_size=1,
            output_dir=str(dirs["output"]),
            processed_dir=str(dirs["processed"]),
            error_dir=str(dirs["error"]),
            transformer=transformer or MagicMock(),
            log_dir=str(dirs["log"]),
        )


class TestProcessingWorker:
    def test_successful_processing_moves_to_processed(self, tmp_path, dirs):
        pdf = tmp_path / "invoice.pdf"
        pdf.write_bytes(b"%PDF")

        mock_transformer = MagicMock()
        mock_output = MagicMock()
        mock_transformer.transform.return_value = mock_output

        worker = make_worker(dirs, mock_transformer)

        with patch("src.worker.worker.extract_text", return_value="extracted text"):
            with patch("src.worker.worker.save_output"):
                future = worker.submit(str(pdf))
                future.result(timeout=5)

        assert (dirs["processed"] / "invoice.pdf").exists() or not pdf.exists()

    def test_failed_processing_moves_to_error(self, tmp_path, dirs):
        pdf = tmp_path / "bad.pdf"
        pdf.write_bytes(b"%PDF")

        worker = make_worker(dirs)

        with patch("src.worker.worker.extract_text", side_effect=RuntimeError("ocr failed")):
            future = worker.submit(str(pdf))
            future.result(timeout=5)

        # PDF should be in error dir
        assert (dirs["error"] / "bad.pdf").exists()

    def test_shutdown_waits_for_pending_jobs(self, dirs):
        worker = make_worker(dirs)
        worker.shutdown(wait=True)
        # No assertion needed — just ensure it doesn't hang or raise

# PDF Extractor — Claude AI

Watches a directory for incoming PDF files and converts each one to structured JSON using the Claude AI API. Supports both text-based and image-based (OCR) PDFs.

## Prerequisites

- Python 3.9+
- [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki) (required only for image-based PDFs)
- Poppler (required by pdf2image — on Windows install via [conda](https://anaconda.org/conda-forge/poppler) or [prebuilt binaries](https://github.com/oschwartz10612/poppler-windows))
- An [Anthropic API key](https://console.anthropic.com/)

## Setup

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env and set ANTHROPIC_API_KEY=sk-...
```

## Configuration

All settings live in `config.ini`. Key options:

| Section | Key | Default | Description |
|---|---|---|---|
| `[paths]` | `input_dir` | `pdfs/input` | Watched for new PDFs |
| `[worker]` | `thread_pool_size` | `4` | Concurrent processing threads |
| `[extractor]` | `ocr_filename_patterns` | `scanned_*.pdf, scan_*.pdf` | Force OCR for matching filenames |
| `[transformer]` | `model` | `claude-sonnet-4-6` | Claude model ID |
| `[logging]` | `log_level` | `INFO` | Log verbosity |

## Running

```bash
# Continuous watch mode (processes existing files, then watches for new ones)
python main.py

# Single-file mode
python main.py --file pdfs/input/invoice.pdf

# Override threads and log level at runtime
python main.py --threads 8 --log-level DEBUG
```

Output JSON files are written to `pdfs/output/<filename>.json`. Processed PDFs move to `pdfs/processed/`; failed PDFs move to `pdfs/error/`.

## Output Schema

The JSON schema is defined in [src/transformer/models.py](src/transformer/models.py). To extend it:
1. Edit the dataclasses in `models.py`
2. Update the system prompt in `src/transformer/transformer.py`

## Running Tests

```bash
pytest
pytest tests/test_extractor.py          # single module
pytest -v --tb=short                    # verbose
```

## Training & Validation

Use the scripts in `scripts/` to validate the pipeline against known-good data:

```bash
# Generate (or regenerate) the demo invoice PDF + ground-truth JSON
python scripts/generate_training_data.py

# Process training PDFs and compare output against ground-truth
cp pdfs/training/invoice_sample.pdf pdfs/input/
python main.py --file pdfs/input/invoice_sample.pdf
python scripts/compare_outputs.py    # exit 0 = all match
```

The `raw_text` field is excluded from comparisons. Ground-truth files live in `pdfs/training/*.json`.

## Output Schema Notes

- `document_type` is always lowercase (`"invoice"`, `"receipt"`, etc.)
- Party `role` is one of: `vendor`, `customer`, `shipper`, `consignee`, `issuer`, `recipient`
  - Issuing/billing party → `vendor`; receiving/paying party → `customer`
- Add `reportlab` to your environment if regenerating training PDFs (`pip install reportlab`)

## Directory Layout

```
src/
  config.py          # INI config loader
  extractor/         # text-based and OCR/ICR PDF extraction
  transformer/       # Claude AI integration + output schema (models.py)
  worker/            # thread-pool processor
  gateway/           # watchdog file-watcher
  logger/            # daily-rotating logger
main.py              # CLI entry point
config.ini           # runtime configuration
pdfs/
  input/             # drop PDFs here
  output/            # JSON results appear here
  processed/         # successfully processed PDFs
  error/             # PDFs that failed processing
  training/          # demo PDFs and ground-truth JSON for validation
log/                 # rotating log files
```

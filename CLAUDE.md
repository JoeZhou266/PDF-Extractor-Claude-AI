# CLAUDE.md
This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# Project: [PDF Extractor to JSON - Claude AI]

## Tech Stack
* **Language:** Python [3.9.13]
* **Environment Management:** [venv]
* **Testing:** [pytest]

## Project Purpose
Python project to extract content from PDF files and output structured JSON using Claude AI.

## Code Style & Standards
* Adhere to PEP 8 style guidelines.
* Use type hinting for function signatures.
* Write clear, concise docstrings for all functions and classes.
* Prioritize readability and maintainability.

## Project Structure
* `src/`: Main source code directory.
* `tests/`: Unit and integration tests.
* `pdfs/trainning`: Agent trainning PDF files.
* `pdfs/input`: Transforming PDF files.
* `pdfs/output`: Transforming output JSON file.
* `pdfs/processed`: Move PDF files from input folder once it processes successfully.
* `pdfs/error`: Move PDF files from input folder once it processes with error or exception.
* `log/`: Print the log file in this folder.
* `requirements.txt`: Project dependencies file.
* `README.md`: General project information for humans.
* `CLAUDE.md`: This file (instructions for AI).

## Specific Instructions for Claude
* **Testing:** When writing new features, ensure corresponding tests are created in the `tests/` directory using `pytest`.
* **Dependencies:** Manage dependencies exclusively using `requirements.txt`.
* **Output:** Focus on writing idiomatic Python code. Do not include verbose explanations in the code itself unless necessary for complex logic.
* **Security:** Follow best practices for security, especially concerning data handling and input validation.

## Key Design Decisions
- Implement the file watching gateway to monitor any new files in the pdfs/input, also past PDF file to transform working thread pool below. after processing, move PDF file from input to pdfs/processed folder. If any files is processed with error or exception, move PDF file from input to pdfs/error folder.
- Implement multiple working thread pool to accept file from watch gateway then transform PDF concurrently, the working thread pool number could be set in properties file.
- Implement the log feature to save log error, exception, info, debug, trace information in Python code. Support log switch occurs at least once a day.
- Implement the properties file to set the configuration of the application, such as the path to the PDF files, the number of working thread pool, the log level, etc.
- Implement the command line arguments to set the configuration of the application, such as the path to the PDF files, the number of working thread pool, the log level, etc.
- Implement the extractor support read text from PDF file using OCR/ICR if the PDF file is image-based.  
- Implement the extractor support read text from PDF file the PDF file is able to read text from it.  
- Implement the properties file to set the PDF file name pattern with text or image-based PDF file. That will be used to determine whether to use OCR/ICR to read text from PDF file.
- Implement the transformer to transform the extracted text to JSON format using Claude AI API.
- JSON output schema is defined in `src/transformer/models.py`; change the schema there first before touching transformer logic.
- Use `os.getenv("ANTHROPIC_API_KEY")` to get the API key in project python source code.


## Workflow

When the source code, README.me is ready:

1. **Generate** the demo PDF and ground-truth JSON training files in pdfs/training folder.
2. **Start** file watching gateway.
3. **Compare** Start watching for new PDFs:
   - Copy PDF files from pdfs/training folder to pdfs/input folder.
   - Call transformer to transform PDF to JSON file by Claude AI API.
   - Transform JSON file is completion in pdfs/output folder.
   - Compare the JSON files in pdfs/output with training JSON files, except raw_text field.
   - Stop file watching gateway.
4. **Fix** every mismatch found. Edit the source code as required.
5. **Repeat** steps 1–4 until the output JSON file is matched.
6. **Update** README.md for the latest project details.

Do NOT stop after one pass. Always do at least 3 comparison rounds. Only stop when the user says so or when no JSON file differences remain.
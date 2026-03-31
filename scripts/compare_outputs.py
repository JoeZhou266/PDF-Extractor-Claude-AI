"""Compare JSON files in pdfs/output against ground-truth files in pdfs/training.

Fields excluded from comparison: raw_text

Usage:
    python scripts/compare_outputs.py
"""

import json
import sys
from pathlib import Path

TRAINING_DIR = Path("pdfs/training")
OUTPUT_DIR = Path("pdfs/output")

EXCLUDED_FIELDS = {"raw_text"}


def flatten(obj, prefix=""):
    """Recursively flatten a nested dict/list into dot-notation key-value pairs."""
    items = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            full_key = f"{prefix}.{k}" if prefix else k
            if k in EXCLUDED_FIELDS:
                continue
            items.update(flatten(v, full_key))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            items.update(flatten(v, f"{prefix}[{i}]"))
    else:
        items[prefix] = obj
    return items


def compare_json(truth_path: Path, output_path: Path) -> list[str]:
    """Return list of difference strings between truth and output (excluding raw_text)."""
    truth = json.loads(truth_path.read_text(encoding="utf-8"))
    output = json.loads(output_path.read_text(encoding="utf-8"))

    truth_flat = flatten(truth)
    output_flat = flatten(output)

    all_keys = set(truth_flat) | set(output_flat)
    diffs = []

    for key in sorted(all_keys):
        tv = truth_flat.get(key, "<MISSING>")
        ov = output_flat.get(key, "<MISSING>")
        if str(tv) != str(ov):
            diffs.append(f"  DIFF  {key}")
            diffs.append(f"        expected : {tv!r}")
            diffs.append(f"        got      : {ov!r}")

    return diffs


def main() -> int:
    ground_truth_files = list(TRAINING_DIR.glob("*.json"))
    if not ground_truth_files:
        print("No ground-truth JSON files found in", TRAINING_DIR)
        return 1

    total_diffs = 0
    any_missing = False

    for truth_path in sorted(ground_truth_files):
        output_path = OUTPUT_DIR / truth_path.name
        print(f"\n{'=' * 60}")
        print(f"File: {truth_path.name}")

        if not output_path.exists():
            print(f"  MISSING output file: {output_path}")
            any_missing = True
            continue

        diffs = compare_json(truth_path, output_path)
        if diffs:
            print(f"  {len(diffs) // 3} difference(s) found:")
            print("\n".join(diffs))
            total_diffs += len(diffs) // 3
        else:
            print("  MATCH — no differences found.")

    print(f"\n{'=' * 60}")
    if any_missing:
        print("RESULT: Some output files are missing.")
        return 2
    if total_diffs:
        print(f"RESULT: {total_diffs} difference(s) found across all files.")
        return 1
    print("RESULT: All output files match their ground-truth counterparts.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

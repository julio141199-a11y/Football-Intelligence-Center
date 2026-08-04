#!/usr/bin/env python3
"""Validate the generated vacancy database without network access."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from vacancy_manager import FIELDS, STATUSES, valid_url  # noqa: E402


def main() -> int:
    records = json.loads((ROOT / "data/vacancies.json").read_text(encoding="utf-8"))
    errors, ids = [], set()
    for index, item in enumerate(records):
        missing = [field for field in FIELDS if field not in item]
        if missing:
            errors.append(f"record {index}: missing fields {missing}")
        if item.get("id") in ids:
            errors.append(f"record {index}: duplicate id {item.get('id')}")
        ids.add(item.get("id"))
        if item.get("role") not in {"Head Coach", "Assistant Coach"}:
            errors.append(f"record {index}: invalid role")
        if item.get("status") not in STATUSES:
            errors.append(f"record {index}: invalid status")
        if not valid_url(item.get("official_source_url", "")):
            errors.append(f"record {index}: invalid official source")
        if not item.get("source_hash"):
            errors.append(f"record {index}: missing source hash")
    if errors:
        print("\n".join(errors))
        return 1
    print(f"Vacancy validation passed: {len(records)} record(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

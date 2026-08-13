#!/usr/bin/env python3
"""Validate FIC JSON data and operating rules."""

from __future__ import annotations
import json
import re
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
ALLOWED_STATUSES = {"Verified Open", "Closing Soon", "To Verify", "Closed", "Filled"}
ALLOWED_ROLES = {"Head Coach", "Assistant Coach", "Fitness Coach"}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ValueError(f"Missing file: {path.relative_to(ROOT)}")
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path.relative_to(ROOT)}: {exc}")


def valid_url(value: str) -> bool:
    if value in {"", "To verify", "Not Public"}:
        return True
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def validate_jobs(errors: list[str]) -> None:
    jobs = load_json(ROOT / "jobs.json")
    if not isinstance(jobs, list):
        errors.append("jobs.json must contain a JSON array.")
        return

    seen_ids: set[str] = set()
    duplicate_keys: set[tuple[str, str, str, str]] = set()

    for index, job in enumerate(jobs):
        label = f"jobs.json[{index}]"
        if not isinstance(job, dict):
            errors.append(f"{label} must be an object.")
            continue

        required = ["id", "status", "roleType", "organization", "position", "country"]
        for key in required:
            if not job.get(key):
                errors.append(f"{label}.{key} is required.")

        job_id = str(job.get("id", ""))
        if job_id in seen_ids:
            errors.append(f"Duplicate job id: {job_id}")
        seen_ids.add(job_id)

        role = job.get("roleType")
        if role not in ALLOWED_ROLES:
            errors.append(f"{label}.roleType is outside scope: {role}")

        status = job.get("status")
        if status not in ALLOWED_STATUSES:
            errors.append(f"{label}.status is invalid: {status}")

        for field in ["dateAdded", "lastChecked", "deadline"]:
            value = job.get(field)
            if value and value not in {"To verify", "Not Public"}:
                if not isinstance(value, str) or not DATE_RE.match(value):
                    errors.append(f"{label}.{field} must use YYYY-MM-DD.")
                else:
                    try:
                        date.fromisoformat(value)
                    except ValueError:
                        errors.append(f"{label}.{field} is not a real date: {value}")

        for field in ["sourceUrl", "applicationLink"]:
            value = job.get(field)
            if isinstance(value, str) and not valid_url(value):
                errors.append(f"{label}.{field} is not a valid URL: {value}")

        duplicate_key = (
            str(job.get("organization", "")).strip().lower(),
            str(job.get("teamType", "")).strip().lower(),
            str(job.get("roleType", "")).strip().lower(),
            str(job.get("deadline", "")).strip().lower(),
        )
        if duplicate_key in duplicate_keys:
            errors.append(f"Probable duplicate vacancy at {label}: {duplicate_key}")
        duplicate_keys.add(duplicate_key)

        deadline = job.get("deadline")
        if isinstance(deadline, str) and DATE_RE.match(deadline):
            deadline_date = date.fromisoformat(deadline)
            if deadline_date < date.today() and status in {"Verified Open", "Closing Soon"}:
                errors.append(f"{label} is past deadline but still marked {status}.")


def validate_all_json(errors: list[str]) -> None:
    for path in ROOT.glob("*.json"):
        try:
            load_json(path)
        except ValueError as exc:
            errors.append(str(exc))
    for path in (ROOT / "config").glob("*.json"):
        try:
            load_json(path)
        except ValueError as exc:
            errors.append(str(exc))


def main() -> int:
    errors: list[str] = []
    validate_all_json(errors)
    validate_jobs(errors)

    if errors:
        print("FIC validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("FIC validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

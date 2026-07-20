#!/usr/bin/env python3
"""Update deadline-based status fields without inventing new vacancies."""

from __future__ import annotations
import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JOBS_PATH = ROOT / "jobs.json"
CLOSING_SOON_DAYS = 3


def main() -> int:
    jobs = json.loads(JOBS_PATH.read_text(encoding="utf-8"))
    today = date.today()
    changed = False

    for job in jobs:
        deadline_text = job.get("deadline")
        if not isinstance(deadline_text, str):
            continue
        try:
            deadline = date.fromisoformat(deadline_text)
        except ValueError:
            continue

        days = (deadline - today).days
        if job.get("daysUntilDeadline") != days:
            job["daysUntilDeadline"] = days
            changed = True

        current = job.get("status")
        new_status = current
        if current in {"Verified Open", "Closing Soon"}:
            if days < 0:
                new_status = "Closed"
            elif days <= CLOSING_SOON_DAYS:
                new_status = "Closing Soon"
            else:
                new_status = "Verified Open"

        if new_status != current:
            job["status"] = new_status
            changed = True

    if changed:
        JOBS_PATH.write_text(
            json.dumps(jobs, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print("Deadline-derived fields updated.")
    else:
        print("No deadline-derived changes.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

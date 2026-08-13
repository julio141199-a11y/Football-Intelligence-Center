#!/usr/bin/env python3
"""Import reviewed Work vacancies into FIC and rebuild the standard vacancy DB."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from vacancy_manager import (
    CHAT_PATH,
    ERROR_LOG_PATH,
    INBOX_PATH,
    VacancyError,
    normalise,
    now_iso,
    read_json,
    run,
    today_seoul,
    write_json,
)


def as_records(payload) -> list[dict]:
    records = payload if isinstance(payload, list) else [payload]
    if not records or not all(isinstance(item, dict) for item in records):
        raise VacancyError("Reviewed vacancy input must be a JSON object or a non-empty array of objects.")
    return records


def reviewed_record(raw: dict, *, today: str | None = None) -> dict:
    """Return a validated, stable reviewed-feed record using the standard schema."""
    return normalise(raw, today=today_seoul(today), origin="chat")


def upsert_feed(records: list[dict], *, feed_path: Path = CHAT_PATH, today: str | None = None) -> dict:
    feed = read_json(feed_path, [])
    validated = [reviewed_record(raw, today=today) for raw in records]
    by_id = {item.get("id"): item for item in feed}
    by_hash = {item.get("source_hash"): item for item in feed if item.get("source_hash")}
    created = updated = unchanged = 0
    for item in validated:
        current = by_id.get(item["id"]) or by_hash.get(item["source_hash"])
        if current is None:
            key = (item["official_source_url"].rstrip("/").casefold(), item["role"].casefold(), item["organization"].casefold())
            current = next((saved for saved in feed if (
                str(saved.get("official_source_url", "")).rstrip("/").casefold(),
                str(saved.get("role", "")).casefold(),
                str(saved.get("organization", "")).casefold(),
            ) == key), None)
        if current is None:
            feed.append(item)
            by_id[item["id"]] = item
            by_hash[item["source_hash"]] = item
            created += 1
        elif current.get("source_hash") == item["source_hash"]:
            unchanged += 1
        else:
            item["created_at"] = current.get("created_at") or item["created_at"]
            current.clear()
            current.update(item)
            updated += 1
    feed.sort(key=lambda item: (str(item.get("posted_date", "")), str(item.get("updated_at", ""))), reverse=True)
    write_json(feed_path, feed)
    return {"created": created, "updated": updated, "unchanged": unchanged, "rejected": 0}


def log_error(message: str) -> None:
    errors = read_json(ERROR_LOG_PATH, [])
    errors.insert(0, {"run_at": now_iso(), "errors": [message]})
    write_json(ERROR_LOG_PATH, errors[:100])


def processed_target(path: Path, inbox_path: Path = INBOX_PATH) -> Path:
    target_dir = inbox_path / "processed"
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / path.name
    if not target.exists():
        return target
    counter = 2
    while (target_dir / f"{path.stem}_{counter}{path.suffix}").exists():
        counter += 1
    return target_dir / f"{path.stem}_{counter}{path.suffix}"


def import_inbox(*, inbox_path: Path = INBOX_PATH, feed_path: Path = CHAT_PATH, today: str | None = None) -> dict:
    files = sorted(path for path in inbox_path.glob("*.json") if path.is_file())
    records: list[dict] = []
    for path in files:
        records.extend(as_records(json.loads(path.read_text(encoding="utf-8"))))
    summary = upsert_feed(records, feed_path=feed_path, today=today) if records else {
        "created": 0, "updated": 0, "unchanged": 0, "rejected": 0,
    }
    for path in files:
        shutil.move(str(path), str(processed_target(path, inbox_path)))
    return {**summary, "processed_files": len(files)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--file", type=Path, help="Reviewed JSON object or array.")
    group.add_argument("--json", dest="json_text", help="One reviewed vacancy as inline JSON.")
    group.add_argument("--inbox", action="store_true", help="Process data/inbox/*.json and move successes to processed/.")
    parser.add_argument("--today", help="Testing override in YYYY-MM-DD format.")
    args = parser.parse_args()

    files: list[Path] = []
    try:
        if args.inbox:
            inbox_summary = import_inbox(today=args.today)
            records = []
            feed_summary = inbox_summary
        elif args.json_text:
            records = as_records(json.loads(args.json_text))
        else:
            records = as_records(json.loads(args.file.read_text(encoding="utf-8")))

        if args.inbox:
            pass
        elif args.file and args.file.resolve() == CHAT_PATH.resolve():
            feed_summary = {"created": 0, "updated": 0, "unchanged": len(records), "rejected": 0}
            for raw in records:
                reviewed_record(raw, today=args.today)
        else:
            feed_summary = upsert_feed(records, today=args.today)

        vacancy_summary = run(files=[], include_pipeline=False, include_chat=True, today_value=args.today)
        if vacancy_summary["rejected"]:
            raise VacancyError("; ".join(vacancy_summary["errors"]))
        summary = {
            "created": vacancy_summary["created"],
            "updated": vacancy_summary["updated"],
            "unchanged": vacancy_summary["unchanged"],
            "rejected": 0,
            "feed": feed_summary,
            "processed_files": feed_summary.get("processed_files", 0),
        }
        print(f"Created: {summary['created']}")
        print(f"Updated: {summary['updated']}")
        print(f"Unchanged: {summary['unchanged']}")
        print("Rejected: 0")
        return 0
    except (OSError, json.JSONDecodeError, VacancyError, TypeError, ValueError) as exc:
        message = str(exc)
        log_error(message)
        print("Created: 0")
        print("Updated: 0")
        print("Unchanged: 0")
        print("Rejected: 1")
        print(f"Error: {message}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

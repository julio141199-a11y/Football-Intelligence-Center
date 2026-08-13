#!/usr/bin/env python3
"""Import reviewed Work/ChatGPT vacancies into the FIC chat feed and vacancy store."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from vacancy_manager import CHAT_PATH, normalise, read_json, run, today_seoul, write_json


def feed_record(raw: dict, *, today: str | None = None) -> dict:
    """Validate a reviewed record and retain the compact public feed schema."""
    item = normalise(raw, today=today_seoul(today), origin="chat")
    status = {
        "NEW": "Verified Open",
        "UPDATED": "Verified Open",
        "CLOSING_SOON": "Verified Open",
        "CLOSED": "Closed",
        "EXPIRED": "Closed",
        "UNVERIFIED": "To Verify",
    }[item["status"]]
    return {
        "id": item["id"].replace("vacancy-", "chat-", 1),
        "status": status,
        "role": item["role"],
        "eventType": "Vacancy",
        "country": item["country"],
        "region": item["region"],
        "organisation": item["organization"],
        "title": raw.get("title") or f'{item["organization"]} {item["role"]}',
        "teamType": item["team_level"],
        "team_gender": item["team_gender"],
        "league": item["league"],
        "sourceUrl": item["official_source_url"],
        "sourceType": item["source_type"],
        "official": bool(raw.get("official", True)),
        "deadline": item["deadline"],
        "posted_date": item["posted_date"],
        "licenceRequirement": item["licence_requirement"],
        "applicationLink": item["application_url"],
        "contactEmail": item["contact_email"],
        "contactPhone": item["contact_phone"],
        "careerPriority": raw.get("careerPriority", "Monitor"),
        "licenceNote": item["fit_assessment"],
        "fitScore": item["fit_score"],
        "fitReason": item["fit_assessment"],
        "accuracyLevel": item["accuracy_level"],
        "detectedAt": raw.get("detectedAt") or item["created_at"],
        "lastVerified": item["last_checked"],
        "notes": raw.get("notes", "Reviewed in Work/ChatGPT and verified against the supplied public source."),
    }


def import_records(records: list[dict], *, feed_path: Path = CHAT_PATH, today: str | None = None) -> dict:
    feed = read_json(feed_path, [])
    by_id = {item.get("id"): item for item in feed}
    created = updated = unchanged = 0
    for raw in records:
        item = feed_record(raw, today=today)
        current = by_id.get(item["id"])
        if current is None:
            feed.append(item)
            by_id[item["id"]] = item
            created += 1
        elif current == item:
            unchanged += 1
        else:
            current.clear()
            current.update(item)
            updated += 1
    feed.sort(key=lambda item: (str(item.get("detectedAt", "")), str(item.get("id", ""))), reverse=True)
    write_json(feed_path, feed)
    return {"created": created, "updated": updated, "unchanged": unchanged}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", required=True, type=Path, help="Reviewed vacancy JSON object or array.")
    parser.add_argument("--today", help="Testing override in YYYY-MM-DD format.")
    parser.add_argument("--feed-only", action="store_true", help="Update chat feed without rebuilding vacancies.json.")
    args = parser.parse_args()
    payload = json.loads(args.file.read_text(encoding="utf-8"))
    records = payload if isinstance(payload, list) else [payload]
    feed_summary = import_records(records, today=args.today)
    vacancy_summary = None if args.feed_only else run(files=[], include_pipeline=True, include_chat=True, today_value=args.today)
    print(json.dumps({"chat_feed": feed_summary, "vacancies": vacancy_summary}, ensure_ascii=False))
    return 1 if vacancy_summary and vacancy_summary.get("rejected") else 0


if __name__ == "__main__":
    raise SystemExit(main())

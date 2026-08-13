#!/usr/bin/env python3
"""Standardise, deduplicate, update, and archive FIC vacancies."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
VACANCIES_PATH = ROOT / "data" / "vacancies.json"
HISTORY_PATH = ROOT / "data" / "vacancies_history.json"
ARCHIVE_PATH = ROOT / "data" / "archive" / "closed_vacancies.json"
UPDATE_LOG_PATH = ROOT / "data" / "logs" / "update_log.json"
ERROR_LOG_PATH = ROOT / "data" / "logs" / "error_log.json"
INBOX_PATH = ROOT / "data" / "inbox"
PIPELINE_PATH = ROOT / "data" / "opportunities.json"
CHAT_PATH = ROOT / "data" / "chat_opportunities.json"

ALLOWED_ROLES = {"Head Coach", "Assistant Coach", "Fitness Coach"}

STATUSES = {"NEW", "UPDATED", "CLOSING_SOON", "CLOSED", "EXPIRED", "UNVERIFIED"}
FIELDS = [
    "id", "role", "organization", "country", "region", "team_gender", "team_level",
    "league", "source_type", "official_source_url", "application_url", "contact_email",
    "contact_phone", "posted_date", "deadline", "licence_requirement",
    "language_requirement", "contract_type", "salary", "housing", "visa", "flights",
    "status", "accuracy_level", "fit_score", "fit_assessment", "last_checked",
    "created_at", "updated_at", "source_hash",
]
MEANINGFUL_FIELDS = [
    "role", "organization", "country", "region", "team_gender", "team_level", "league",
    "source_type", "official_source_url", "application_url", "contact_email", "contact_phone",
    "posted_date", "deadline", "licence_requirement", "language_requirement", "contract_type",
    "salary", "housing", "visa", "flights", "accuracy_level", "fit_score", "fit_assessment",
]


class VacancyError(ValueError):
    pass


def read_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def today_seoul(value: str | None = None) -> date:
    return date.fromisoformat(value) if value else datetime.now(ZoneInfo("Asia/Seoul")).date()


def clean(value) -> str:
    return "" if value is None else str(value).strip()


def valid_url(value: str) -> bool:
    if not value or "PLACEHOLDER" in value.upper():
        return False
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def canonical_role(value: str) -> str:
    lowered = value.casefold()
    if "fitness coach" in lowered or "physical coach" in lowered or "preparador físico" in lowered:
        return "Fitness Coach"
    if "assistant" in lowered or "adjunto" in lowered or "asistente" in lowered:
        return "Assistant Coach"
    if "head coach" in lowered or "manager" in lowered or "treinador principal" in lowered:
        return "Head Coach"
    raise VacancyError("Only Head Coach, Assistant Coach, and Fitness Coach vacancies are allowed.")


def validate_scope(raw: dict, role: str) -> None:
    combined = " ".join(clean(raw.get(key)) for key in (
        "organization", "organisation", "team_level", "teamType", "league", "title", "position"
    )).casefold()
    gender = clean(raw.get("team_gender") or raw.get("teamGender")).casefold()
    if role not in ALLOWED_ROLES:
        raise VacancyError(f"Role is outside scope: {role}")
    if "academy" in combined and not any(term in combined for term in ("first team", "national team", "senior")):
        raise VacancyError("Academy-only vacancies are excluded.")
    professional_club = any(term in combined for term in ("professional club", "pro club", "first team", "league club"))
    women = gender in {"women", "women's", "female"} or any(term in combined for term in ("women's club", "women club", "female club"))
    national_team = "national team" in combined
    if professional_club and women and not national_team:
        raise VacancyError("Women's professional-club vacancies are excluded.")


def stable_id(item: dict) -> str:
    parts = [item.get(key, "") for key in ("organization", "role", "country", "team_level", "official_source_url")]
    normalized = "|".join(re.sub(r"\s+", " ", clean(value).casefold()) for value in parts)
    return f"vacancy-{hashlib.sha256(normalized.encode()).hexdigest()[:16]}"


def source_hash(item: dict) -> str:
    payload = {key: clean(item.get(key)) for key in MEANINGFUL_FIELDS}
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode()).hexdigest()


def validate_date(value: str, field: str) -> None:
    if not value:
        return
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise VacancyError(f"{field} must use YYYY-MM-DD: {value}") from exc


def deadline_status(deadline: str, current: str, today: date) -> str:
    if current == "CLOSED":
        return "CLOSED"
    if not deadline:
        return current
    deadline_date = date.fromisoformat(deadline)
    days = (deadline_date - today).days
    if days < 0:
        return "EXPIRED"
    if days <= 7:
        return "CLOSING_SOON"
    return current


def normalise(raw: dict, *, today: date, origin: str = "chat") -> dict:
    organization = clean(raw.get("organization") or raw.get("organisation"))
    country = clean(raw.get("country"))
    source_url = clean(raw.get("official_source_url") or raw.get("sourceUrl"))
    if not organization or not country:
        raise VacancyError("organization and country are required.")
    if not valid_url(source_url):
        raise VacancyError("A real http(s) official_source_url is required; placeholders are rejected.")

    item = {key: "" for key in FIELDS}
    aliases = {
        "region": raw.get("region") or raw.get("continent"), "team_gender": raw.get("team_gender"),
        "team_level": raw.get("team_level") or raw.get("teamType"), "league": raw.get("league"),
        "source_type": raw.get("source_type") or raw.get("sourceType") or raw.get("sourcePlatform"),
        "application_url": raw.get("application_url") or raw.get("applicationLink"),
        "contact_email": raw.get("contact_email") or raw.get("contactEmail"),
        "contact_phone": raw.get("contact_phone") or raw.get("contactPhone"),
        "posted_date": raw.get("posted_date") if "posted_date" in raw else clean(raw.get("detectedAt"))[:10],
        "deadline": raw.get("deadline"),
        "licence_requirement": raw.get("licence_requirement") or raw.get("licenceRequirement") or raw.get("licenceNote"),
        "language_requirement": raw.get("language_requirement"), "contract_type": raw.get("contract_type"),
        "salary": raw.get("salary"), "housing": raw.get("housing"), "visa": raw.get("visa"),
        "flights": raw.get("flights"), "accuracy_level": raw.get("accuracy_level") or raw.get("accuracyLevel"),
        "fit_score": raw.get("fit_score") or raw.get("fitScore"),
        "fit_assessment": raw.get("fit_assessment") or raw.get("fitReason") or raw.get("licenceNote"),
        "last_checked": raw.get("last_checked") or raw.get("lastChecked") or today.isoformat(),
    }
    item.update({key: clean(value) for key, value in aliases.items()})
    role = canonical_role(clean(raw.get("role") or raw.get("roleType") or raw.get("title")))
    validate_scope(raw, role)
    item.update({
        "role": role,
        "organization": organization,
        "country": country,
        "official_source_url": source_url,
    })
    if not item["source_type"]:
        item["source_type"] = "Official source" if raw.get("official") else origin.title()
    validate_date(item["posted_date"], "posted_date")
    validate_date(item["deadline"], "deadline")
    validate_date(item["last_checked"], "last_checked")
    supplied = clean(raw.get("status")).upper().replace(" ", "_")
    if supplied in {"VERIFIED_OPEN", "OPEN"}:
        supplied = "NEW"
    if supplied == "TO_VERIFY":
        supplied = "UNVERIFIED"
    status = supplied if supplied in STATUSES else ("UNVERIFIED" if origin == "pipeline" else "NEW")
    item["status"] = deadline_status(item["deadline"], status, today)
    timestamp = now_iso()
    item["id"] = stable_id(item)
    item["created_at"] = clean(raw.get("created_at")) or timestamp
    item["updated_at"] = timestamp
    item["source_hash"] = source_hash(item)
    return item


def upsert(vacancies: list[dict], incoming: dict, history: list[dict], *, today: date) -> str:
    existing = next((item for item in vacancies if item.get("id") == incoming["id"]), None)
    if existing is None:
        existing = next((item for item in vacancies if item.get("source_hash") == incoming["source_hash"]), None)
    if existing is None:
        vacancies.append(incoming)
        history.append({"vacancy_id": incoming["id"], "action": "CREATED", "at": incoming["created_at"], "after": incoming})
        return "created"
    if existing.get("source_hash") == incoming["source_hash"]:
        computed = deadline_status(clean(existing.get("deadline")), clean(existing.get("status")), today)
        if computed == existing.get("status"):
            return "unchanged"
        before = dict(existing)
        existing["status"] = computed
        existing["updated_at"] = now_iso()
        history.append({"vacancy_id": existing["id"], "action": "STATUS_CHANGED", "at": existing["updated_at"], "before": before, "after": dict(existing)})
        return "updated"
    before = dict(existing)
    incoming["created_at"] = existing.get("created_at") or incoming["created_at"]
    if incoming["status"] == "NEW":
        incoming["status"] = deadline_status(incoming["deadline"], "UPDATED", today)
    existing.clear()
    existing.update(incoming)
    changed_fields = [key for key in MEANINGFUL_FIELDS if clean(before.get(key)) != clean(incoming.get(key))]
    history.append({"vacancy_id": incoming["id"], "action": "UPDATED", "at": incoming["updated_at"], "changed_fields": changed_fields, "before": before, "after": dict(incoming)})
    return "updated"


def process_records(records: list[dict], vacancies: list[dict], history: list[dict], *, today: date, origin: str) -> dict:
    result = {"created": 0, "updated": 0, "unchanged": 0, "rejected": 0, "errors": []}
    for raw in records:
        try:
            outcome = upsert(vacancies, normalise(raw, today=today, origin=origin), history, today=today)
            result[outcome] += 1
        except (VacancyError, TypeError) as exc:
            result["rejected"] += 1
            result["errors"].append(str(exc))
    return result


def run(*, files: list[Path], include_pipeline: bool, include_chat: bool = True, today_value: str | None = None) -> dict:
    today = today_seoul(today_value)
    vacancies = read_json(VACANCIES_PATH, [])
    history = read_json(HISTORY_PATH, [])
    summary = {"created": 0, "updated": 0, "unchanged": 0, "rejected": 0, "errors": []}
    inputs: list[tuple[list[dict], str]] = []
    if include_chat:
        inputs.append((read_json(CHAT_PATH, []), "chat"))
    for path in files:
        payload = read_json(path, [])
        inputs.append((payload if isinstance(payload, list) else [payload], "chat"))
    if include_pipeline:
        inputs.append((read_json(PIPELINE_PATH, []), "pipeline"))
    for records, origin in inputs:
        result = process_records(records, vacancies, history, today=today, origin=origin)
        for key in ("created", "updated", "unchanged", "rejected"):
            summary[key] += result[key]
        summary["errors"].extend(result["errors"])
    for item in vacancies:
        computed = deadline_status(clean(item.get("deadline")), clean(item.get("status")), today)
        if computed != item.get("status"):
            before = dict(item)
            item["status"] = computed
            item["updated_at"] = now_iso()
            history.append({"vacancy_id": item["id"], "action": "STATUS_CHANGED", "at": item["updated_at"], "before": before, "after": dict(item)})
            summary["updated"] += 1
    vacancies.sort(key=lambda item: (item.get("posted_date", ""), item.get("updated_at", "")), reverse=True)
    write_json(VACANCIES_PATH, vacancies)
    write_json(HISTORY_PATH, history)
    write_json(ARCHIVE_PATH, [item for item in vacancies if item.get("status") in {"CLOSED", "EXPIRED"}])
    if summary["created"] or summary["updated"] or summary["rejected"]:
        logs = read_json(UPDATE_LOG_PATH, [])
        logs.insert(0, {"run_at": now_iso(), "today_kst": today.isoformat(), **{key: summary[key] for key in ("created", "updated", "unchanged", "rejected")}})
        write_json(UPDATE_LOG_PATH, logs[:100])
    if summary["errors"]:
        errors = read_json(ERROR_LOG_PATH, [])
        errors.insert(0, {"run_at": now_iso(), "errors": summary["errors"]})
        write_json(ERROR_LOG_PATH, errors[:100])
    elif not ERROR_LOG_PATH.exists():
        write_json(ERROR_LOG_PATH, [])
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", action="append", type=Path, default=[])
    parser.add_argument("--inbox", action="store_true")
    parser.add_argument("--pipeline", action="store_true")
    parser.add_argument("--chat", action="store_true", help="Explicitly include the reviewed chat feed (included by default).")
    parser.add_argument("--today")
    args = parser.parse_args()
    files = list(args.file)
    if args.inbox:
        files.extend(sorted(INBOX_PATH.glob("*.json")))
    summary = run(files=files, include_pipeline=args.pipeline, include_chat=True, today_value=args.today)
    print(json.dumps(summary, ensure_ascii=False))
    return 1 if summary["rejected"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

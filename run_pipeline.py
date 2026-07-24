#!/usr/bin/env python3
"""Run the lightweight FIC opportunity-watch pipeline.

The pipeline uses one generic link collector for all automatically monitored
HTML/RSS sources. It never promotes a detected item to a verified job. Every
new candidate remains ``To Verify`` until a human checks the official source.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCES_PATH = ROOT / "sources" / "sources.json"
OPPORTUNITIES_PATH = ROOT / "data" / "opportunities.json"
UPDATES_PATH = ROOT / "data" / "updates.json"
MAX_RESPONSE_BYTES = 2_000_000

ROLE_PATTERNS = {
    "Head Coach": re.compile(
        r"\b(head coach|manager|treinador principal|entrenador principal|sélectionneur)\b",
        re.IGNORECASE,
    ),
    "Assistant Coach": re.compile(
        r"\b(assistant coach|assistant manager|treinador adjunto|asistente técnico|entraîneur adjoint)\b",
        re.IGNORECASE,
    ),
}
EVENT_PATTERN = re.compile(
    r"\b(vacanc(?:y|ies)|recruit(?:ment|ing)|applications?|apply|hiring|seeking|"
    r"resigned?|dismissed?|sacked|depart(?:ed|ure)|interim|contract ended|"
    r"non-renewal|vaga|candidatur[ae]|recrutamento|renunci[oó]|destituido)\b",
    re.IGNORECASE,
)
EXCLUDED_PATTERN = re.compile(
    r"\b(fitness coach|goalkeeper coach|performance coach|sport scientist|"
    r"performance analyst|video analyst|data analyst|technical director|"
    r"sporting director|academy coach|youth coach)\b",
    re.IGNORECASE,
)


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title_parts: list[str] = []
        self.in_title = False
        self.current_href: str | None = None
        self.current_text: list[str] = []
        self.links: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "title":
            self.in_title = True
        if tag.lower() == "a":
            self.current_href = dict(attrs).get("href")
            self.current_text = []

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self.in_title = False
        if tag.lower() == "a" and self.current_href:
            text = " ".join("".join(self.current_text).split())
            if text:
                self.links.append((self.current_href, text))
            self.current_href = None
            self.current_text = []

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title_parts.append(data)
        if self.current_href is not None:
            self.current_text.append(data)


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def fetch_text(url: str, timeout: int, user_agent: str) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml,application/rss+xml,application/xml;q=0.9,*/*;q=0.8",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        content_type = response.headers.get("Content-Type", "").lower()
        if not any(item in content_type for item in ("html", "text", "xml", "rss")):
            raise ValueError(f"unsupported content type: {content_type or 'unknown'}")
        return response.read(MAX_RESPONSE_BYTES).decode("utf-8", errors="replace")


def extract_links(base_url: str, document: str) -> list[tuple[str, str]]:
    parser = LinkParser()
    parser.feed(document)
    unique: dict[str, str] = {}
    for href, title in parser.links:
        url = urllib.parse.urljoin(base_url, href)
        parsed = urllib.parse.urlsplit(url)
        if parsed.scheme not in {"http", "https"}:
            continue
        normalized = urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path, parsed.query, ""))
        unique.setdefault(normalized, title[:300])
    return list(unique.items())[:250]


def match_candidate(title: str, url: str) -> tuple[str, str] | None:
    text = f"{title} {urllib.parse.unquote(url)}"
    if EXCLUDED_PATTERN.search(text) or not EVENT_PATTERN.search(text):
        return None
    for role, pattern in ROLE_PATTERNS.items():
        if pattern.search(text):
            event = "Vacancy" if re.search(
                r"vacanc|recruit|application|apply|hiring|seeking|vaga|candidatur|recrutamento",
                text,
                re.IGNORECASE,
            ) else "Coach Change"
            return role, event
    return None


def candidate_id(source_id: str, url: str, role: str) -> str:
    digest = hashlib.sha256(f"{source_id}|{url}|{role}".encode()).hexdigest()[:16]
    return f"opportunity-{digest}"


def deduplicate(items: list[dict]) -> list[dict]:
    strongest: dict[tuple[str, str, str], dict] = {}
    for item in items:
        key = (
            str(item.get("sourceUrl", "")).rstrip("/").casefold(),
            str(item.get("role", "")).casefold(),
            str(item.get("organisation", "")).casefold(),
        )
        current = strongest.get(key)
        if current is None or (item.get("official", False) and not current.get("official", False)):
            strongest[key] = item
    return sorted(strongest.values(), key=lambda item: item.get("detectedAt", ""), reverse=True)


def main() -> int:
    config = read_json(SOURCES_PATH)
    opportunities = read_json(OPPORTUNITIES_PATH)
    updates = read_json(UPDATES_PATH)
    existing_ids = {item.get("id") for item in opportunities}
    checked = 0
    skipped = 0
    added = 0
    warnings: list[str] = []
    run_at = now_iso()

    settings = config.get("settings", {})
    timeout = int(settings.get("requestTimeoutSeconds", 15))
    user_agent = settings.get("userAgent", "FIC-Opportunity-Watch/1.0")

    for source in config.get("sources", []):
        if not source.get("enabled", True):
            continue
        if source.get("collectionMode") != "automatic":
            skipped += 1
            continue
        try:
            document = fetch_text(source["url"], timeout, user_agent)
            checked += 1
            for url, title in extract_links(source["url"], document):
                match = match_candidate(title, url)
                if not match:
                    continue
                role, event_type = match
                item_id = candidate_id(source["id"], url, role)
                if item_id in existing_ids:
                    continue
                opportunities.append(
                    {
                        "id": item_id,
                        "status": "To Verify",
                        "role": role,
                        "eventType": event_type,
                        "country": source.get("country", "Regional"),
                        "region": source["region"],
                        "organisation": source["name"],
                        "title": title,
                        "sourceUrl": url,
                        "sourceType": source["type"],
                        "official": bool(source.get("official")),
                        "detectedAt": run_at,
                        "lastVerified": "Needs verification",
                    }
                )
                existing_ids.add(item_id)
                added += 1
        except (urllib.error.URLError, TimeoutError, ValueError, OSError) as exc:
            warnings.append(f"{source['id']}: {exc}")

    opportunities = deduplicate(opportunities)
    update = {
        "runAt": run_at,
        "status": "completed_with_warnings" if warnings else "completed",
        "sourcesChecked": checked,
        "registryOnlySources": skipped,
        "newCandidates": added,
        "warnings": warnings,
    }
    updates.insert(0, update)
    updates = updates[:30]

    write_json(OPPORTUNITIES_PATH, opportunities)
    write_json(UPDATES_PATH, updates)

    print(f"Sources checked: {checked}")
    print(f"Registry-only sources: {skipped}")
    print(f"New candidates: {added}")
    print(f"Warnings: {len(warnings)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

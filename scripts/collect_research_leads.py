#!/usr/bin/env python3
"""Collect potential FIC vacancy leads from explicitly configured public sources.

This script does not decide that a lead is verified and never writes to jobs.json.
It only creates or updates data/research_inbox.json for later verification.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from datetime import datetime, timezone
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES_PATH = ROOT / "config" / "research_sources.json"
TERMS_PATH = ROOT / "config" / "research_terms.json"
INBOX_PATH = ROOT / "data" / "research_inbox.json"
STATE_PATH = ROOT / "data" / "research_state.json"

TAG_RE = re.compile(r"<[^>]+>")
TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.I | re.S)
LINK_RE = re.compile(r'href=["\']([^"\']+)["\']', re.I)
SPACE_RE = re.compile(r"\s+")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def clean_text(raw: str) -> str:
    text = TAG_RE.sub(" ", raw)
    text = unescape(text)
    return SPACE_RE.sub(" ", text).strip()


def source_allowed(url: str, user_agent: str, respect_robots: bool) -> bool:
    if not respect_robots:
        return True
    parsed = urllib.parse.urlsplit(url)
    robots_url = urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, "/robots.txt", "", ""))
    parser = urllib.robotparser.RobotFileParser()
    parser.set_url(robots_url)
    try:
        parser.read()
        return parser.can_fetch(user_agent, url)
    except Exception:
        # Fail closed when robots rules cannot be evaluated.
        return False


def fetch_html(url: str, timeout: int, user_agent: str) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        content_type = response.headers.get("Content-Type", "")
        if not any(token in content_type.lower() for token in ("text", "html", "xml")):
            raise ValueError(f"Unsupported content type: {content_type}")
        return response.read(2_000_000).decode("utf-8", errors="replace")


def is_candidate(text: str, positive: list[str], vacancy: list[str], excluded: list[str]) -> bool:
    lowered = text.casefold()
    if any(term.casefold() in lowered for term in excluded):
        return False
    return (
        any(term.casefold() in lowered for term in positive)
        and any(term.casefold() in lowered for term in vacancy)
    )


def candidate_links(base_url: str, html: str) -> list[str]:
    links = []
    seen = set()
    for raw in LINK_RE.findall(html):
        url = urllib.parse.urljoin(base_url, unescape(raw))
        parsed = urllib.parse.urlsplit(url)
        if parsed.scheme not in {"http", "https"}:
            continue
        normalized = urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path, parsed.query, ""))
        if normalized not in seen:
            seen.add(normalized)
            links.append(normalized)
    return links[:200]


def make_id(source_id: str, url: str, title: str) -> str:
    digest = hashlib.sha256(f"{source_id}|{url}|{title}".encode("utf-8")).hexdigest()[:16]
    return f"lead-{digest}"


def main() -> int:
    config = read_json(SOURCES_PATH)
    terms = read_json(TERMS_PATH)
    inbox = read_json(INBOX_PATH)
    state = read_json(STATE_PATH)

    rules = config["rules"]
    timeout = int(rules.get("requestTimeoutSeconds", 20))
    max_pages = int(rules.get("maxPagesPerRun", 50))
    user_agent = rules.get("userAgent", "FIC-Research-Watch/1.0")
    respect_robots = bool(rules.get("respectRobotsTxt", True))

    existing_ids = {item.get("id") for item in inbox if isinstance(item, dict)}
    added = 0
    checked = 0
    errors = []

    for source in config.get("sources", []):
        if not source.get("enabled"):
            continue
        if checked >= max_pages:
            break

        source_id = source["id"]
        source_url = source["url"]

        if not source_allowed(source_url, user_agent, respect_robots):
            errors.append(f"{source_id}: robots.txt disallows or could not confirm access")
            continue

        try:
            html = fetch_html(source_url, timeout, user_agent)
            checked += 1
            source_text = clean_text(html)

            title_match = TITLE_RE.search(html)
            source_title = clean_text(title_match.group(1)) if title_match else source.get("name", source_url)

            candidates = [(source_url, source_title, source_text)]
            for link in candidate_links(source_url, html):
                link_text = link.replace("-", " ").replace("_", " ")
                if is_candidate(link_text, terms["positiveTerms"], terms["vacancyTerms"], terms["excludedTerms"]):
                    candidates.append((link, link_text, link_text))

            for url, title, searchable_text in candidates:
                if not is_candidate(
                    searchable_text,
                    terms["positiveTerms"],
                    terms["vacancyTerms"],
                    terms["excludedTerms"],
                ):
                    continue

                lead_id = make_id(source_id, url, title)
                if lead_id in existing_ids:
                    continue

                inbox.append({
                    "id": lead_id,
                    "status": "To Verify",
                    "discoveredAt": utc_now(),
                    "sourceId": source_id,
                    "sourceName": source.get("name"),
                    "sourceUrl": url,
                    "sourceOfficial": bool(source.get("official")),
                    "region": source.get("region", "To verify"),
                    "title": title[:300],
                    "matchedScope": "Potential Head Coach or Assistant Coach lead",
                    "verificationNotes": "Not yet verified. Review the official source before adding to jobs.json."
                })
                existing_ids.add(lead_id)
                added += 1

            state.setdefault("sourceStates", {})[source_id] = {
                "lastChecked": utc_now(),
                "lastResult": "success"
            }

        except (urllib.error.URLError, TimeoutError, ValueError, OSError) as exc:
            errors.append(f"{source_id}: {exc}")
            state.setdefault("sourceStates", {})[source_id] = {
                "lastChecked": utc_now(),
                "lastResult": "error",
                "error": str(exc)
            }

        time.sleep(0.2)

    state["lastRun"] = utc_now()
    if not errors:
        state["lastSuccessfulRun"] = state["lastRun"]
        state["lastError"] = None
    else:
        state["lastError"] = errors

    write_json(INBOX_PATH, inbox)
    write_json(STATE_PATH, state)

    print(f"Sources checked: {checked}")
    print(f"New leads added: {added}")
    if errors:
        print("Warnings:")
        for error in errors:
            print(f"- {error}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

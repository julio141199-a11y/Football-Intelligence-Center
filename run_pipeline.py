#!/usr/bin/env python3
"""Run the lightweight FIC opportunity-watch pipeline.

The pipeline uses one generic link collector for all automatically monitored
HTML/RSS sources. It never promotes a detected item to a verified job. Every
new candidate remains ``To Verify`` until a human checks the official source.
"""

from __future__ import annotations

import hashlib
import http.client
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
SOURCE_OVERRIDES_PATH = ROOT / "config" / "source_access_overrides.json"
CAREER_PROFILE_PATH = ROOT / "config" / "career_profile.json"
OPPORTUNITIES_PATH = ROOT / "data" / "opportunities.json"
CONTACTS_PATH = ROOT / "data" / "contacts.json"
SOCIAL_SOURCES_PATH = ROOT / "data" / "social_sources.json"
UPDATES_PATH = ROOT / "data" / "updates.json"
MAX_RESPONSE_BYTES = 2_000_000
CONTACT_LINK_PATTERN = re.compile(
    r"\b(contact|contact us|careers?|vacanc(?:y|ies)|jobs?|recruitment|about us|"
    r"contato|contactos?|contacto|contacto-nos)\b",
    re.IGNORECASE,
)
EMAIL_PATTERN = re.compile(
    r"(?<![\w.+-])([A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,})(?![\w.-])",
    re.IGNORECASE,
)
ROLE_EMAIL_PREFIXES = {
    "admin",
    "administration",
    "careers",
    "club",
    "communications",
    "contact",
    "enquiries",
    "enquiry",
    "football",
    "general",
    "hello",
    "hr",
    "info",
    "office",
    "recruitment",
    "secretariat",
}

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
U20_PATTERN = re.compile(r"\b(u[- ]?20|under[- ]?20|under 20)\b", re.IGNORECASE)
NATIONAL_TEAM_PATTERN = re.compile(
    r"\b(national team|senior national|seleção nacional|tim nasional)\b",
    re.IGNORECASE,
)
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


def apply_source_overrides(sources: list[dict]) -> list[dict]:
    """Apply small operational URL/mode fixes without changing the source registry."""
    if not SOURCE_OVERRIDES_PATH.exists():
        return sources
    overrides = read_json(SOURCE_OVERRIDES_PATH)
    return [{**source, **overrides.get(source.get("id"), {})} for source in sources]


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


def contact_page_links(base_url: str, links: list[tuple[str, str]]) -> list[str]:
    base_host = urllib.parse.urlsplit(base_url).netloc.casefold().removeprefix("www.")
    matches: list[str] = []
    for url, title in links:
        host = urllib.parse.urlsplit(url).netloc.casefold().removeprefix("www.")
        text = f"{title} {urllib.parse.unquote(url)}"
        if host == base_host and CONTACT_LINK_PATTERN.search(text) and url not in matches:
            matches.append(url)
    return matches[:3]


def extract_role_emails(document: str) -> list[str]:
    emails: set[str] = set()
    for email in EMAIL_PATTERN.findall(document):
        normalized = email.strip(".,;:()[]{}<>").casefold()
        prefix = normalized.split("@", 1)[0].split("+", 1)[0]
        if prefix in ROLE_EMAIL_PREFIXES:
            emails.add(normalized)
    return sorted(emails)


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


def career_priority(title: str, url: str, role: str, source_type: str) -> tuple[str, str]:
    """Apply Julio's pre-Pro target order without guessing licence recognition."""
    text_value = f"{title} {urllib.parse.unquote(url)}"
    if role == "Head Coach" and U20_PATTERN.search(text_value):
        return "Priority 1", "National U20 Head Coach — AFC A minimum confirmed for AFC competition registration."
    if role == "Assistant Coach" and NATIONAL_TEAM_PATTERN.search(text_value) and not U20_PATTERN.search(text_value):
        return "Priority 1", "Senior national-team Assistant Coach — AFC A minimum confirmed for AFC competition registration."
    if role == "Head Coach" and source_type in {"club", "league"}:
        return "Priority 2", "Professional-club Head Coach — official domestic licence and recognition rules must be verified."
    return "Monitor", "Target role detected; team level and licence fit require verification."


def contact_id(source_id: str, email: str) -> str:
    digest = hashlib.sha256(f"{source_id}|{email}".encode()).hexdigest()[:16]
    return f"contact-{digest}"


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


def deduplicate_contacts(items: list[dict]) -> list[dict]:
    unique: dict[tuple[str, str], dict] = {}
    for item in items:
        key = (
            str(item.get("organisation", "")).casefold(),
            str(item.get("email", "")).casefold(),
        )
        unique.setdefault(key, item)
    return sorted(unique.values(), key=lambda item: (item.get("region", ""), item.get("organisation", "")))


def build_social_registry(sources: list[dict], generated_at: str, existing: list[dict] | None = None) -> list[dict]:
    """Publish verified official social profiles without scraping gated posts."""
    records: list[dict] = []
    existing_by_id = {item.get("id"): item for item in (existing or [])}
    for source in sources:
        source_type = str(source.get("type", ""))
        if not source.get("enabled", True) or not source.get("official"):
            continue
        if source_type not in {"official-linkedin", "official-instagram", "official-club-instagram"}:
            continue
        platform = "LinkedIn" if source_type == "official-linkedin" else "Instagram"
        profile_url = source["url"].rstrip("/")
        records.append(
            {
                "id": source["id"],
                "platform": platform,
                "country": source.get("country", "Regional"),
                "region": source.get("region", "International"),
                "organisation": source["name"].removesuffix(" Official LinkedIn").removesuffix(" Official Instagram"),
                "profileUrl": profile_url,
                "jobsUrl": f"{profile_url}/jobs" if platform == "LinkedIn" else "Not applicable",
                "official": True,
                "monitoring": source.get("monitoring", "Registry only"),
                "watchFor": source.get(
                    "watchFor",
                    ["Head Coach", "Assistant Coach", "Vacancy", "Resigned", "Dismissed", "Appointed"],
                ),
                "lastVerified": source.get("lastVerified") or existing_by_id.get(source["id"], {}).get("lastVerified") or "Needs verification",
            }
        )
    return sorted(records, key=lambda item: (item["platform"], item["region"], item["organisation"]))


def main() -> int:
    config = read_json(SOURCES_PATH)
    config["sources"] = apply_source_overrides(config.get("sources", []))
    read_json(CAREER_PROFILE_PATH)
    opportunities = read_json(OPPORTUNITIES_PATH)
    contacts = read_json(CONTACTS_PATH)
    updates = read_json(UPDATES_PATH)
    existing_ids = {item.get("id") for item in opportunities}
    existing_contact_ids = {item.get("id") for item in contacts}
    checked = 0
    skipped = 0
    added = 0
    contacts_added = 0
    warnings: list[str] = []
    run_at = now_iso()
    previous_social_sources = read_json(SOCIAL_SOURCES_PATH)
    social_sources = build_social_registry(config.get("sources", []), run_at, previous_social_sources)

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
            links = extract_links(source["url"], document)
            for url, title in links:
                match = match_candidate(title, url)
                if not match:
                    continue
                role, event_type = match
                priority, licence_note = career_priority(title, url, role, source["type"])
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
                        "careerPriority": priority,
                        "licenceNote": licence_note,
                        "detectedAt": run_at,
                        "lastVerified": "Needs verification",
                    }
                )
                existing_ids.add(item_id)
                added += 1

            if source.get("official") and source.get("type") in {"federation", "league", "club"}:
                pages = [(source["url"], document)]
                for contact_url in contact_page_links(source["url"], links):
                    try:
                        pages.append((contact_url, fetch_text(contact_url, timeout, user_agent)))
                    except (urllib.error.URLError, TimeoutError, ValueError, OSError, http.client.HTTPException) as exc:
                        warnings.append(f"{source['id']} contact page: {exc}")
                for contact_url, contact_document in pages:
                    for email in extract_role_emails(contact_document):
                        item_id = contact_id(source["id"], email)
                        if item_id in existing_contact_ids:
                            continue
                        contacts.append(
                            {
                                "id": item_id,
                                "status": "To Verify",
                                "country": source.get("country", "Regional"),
                                "region": source["region"],
                                "organisation": source["name"],
                                "organisationType": source["type"].title(),
                                "email": email,
                                "website": source["url"],
                                "contactPage": contact_url,
                                "sourceUrl": contact_url,
                                "official": True,
                                "detectedAt": run_at,
                                "lastVerified": "Needs verification",
                            }
                        )
                        existing_contact_ids.add(item_id)
                        contacts_added += 1
        except (urllib.error.URLError, TimeoutError, ValueError, OSError, http.client.HTTPException) as exc:
            warnings.append(f"{source['id']}: {exc}")

    opportunities = deduplicate(opportunities)
    contacts = deduplicate_contacts(contacts)
    update = {
        "runAt": run_at,
        "status": "completed_with_warnings" if warnings else "completed",
        "sourcesChecked": checked,
        "registryOnlySources": skipped,
        "newCandidates": added,
        "newContacts": contacts_added,
        "socialProfiles": len(social_sources),
        "warnings": warnings,
    }
    meaningful_change = bool(added or contacts_added or social_sources != previous_social_sources)
    if meaningful_change:
        updates.insert(0, update)
    updates = updates[:30]

    write_json(OPPORTUNITIES_PATH, opportunities)
    write_json(CONTACTS_PATH, contacts)
    write_json(SOCIAL_SOURCES_PATH, social_sources)
    write_json(UPDATES_PATH, updates)

    print(f"Sources checked: {checked}")
    print(f"Registry-only sources: {skipped}")
    print(f"New candidates: {added}")
    print(f"New contacts: {contacts_added}")
    print(f"Warnings: {len(warnings)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

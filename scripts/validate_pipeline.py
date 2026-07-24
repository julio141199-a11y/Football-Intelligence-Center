#!/usr/bin/env python3
"""Validate the generated FIC opportunity-watch files."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
ALLOWED_ROLES = {"Head Coach", "Assistant Coach"}
ALLOWED_STATUSES = {"To Verify", "Verified Open", "Closed", "Filled"}


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    errors: list[str] = []
    sources = load(ROOT / "sources" / "sources.json")
    opportunities = load(ROOT / "data" / "opportunities.json")
    contacts = load(ROOT / "data" / "contacts.json")
    social_sources = load(ROOT / "data" / "social_sources.json")
    updates = load(ROOT / "data" / "updates.json")

    if not isinstance(sources.get("sources"), list):
        errors.append("sources/sources.json.sources must be an array.")
    if not isinstance(opportunities, list):
        errors.append("data/opportunities.json must be an array.")
    if not isinstance(updates, list):
        errors.append("data/updates.json must be an array.")
    if not isinstance(contacts, list):
        errors.append("data/contacts.json must be an array.")
    if not isinstance(social_sources, list):
        errors.append("data/social_sources.json must be an array.")

    source_ids: set[str] = set()
    allowed_modes = {"automatic", "registry-only"}
    for index, source in enumerate(sources.get("sources", [])):
        label = f"sources/sources.json.sources[{index}]"
        source_id = source.get("id")
        if not source_id:
            errors.append(f"{label}.id is required.")
        elif source_id in source_ids:
            errors.append(f"Duplicate source id: {source_id}")
        source_ids.add(source_id)
        if source.get("collectionMode") not in allowed_modes:
            errors.append(f"{label}.collectionMode is invalid: {source.get('collectionMode')}")
        parsed = urlparse(str(source.get("url", "")))
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            errors.append(f"{label}.url is invalid.")

    ids: set[str] = set()
    keys: set[tuple[str, str, str]] = set()
    for index, item in enumerate(opportunities):
        label = f"data/opportunities.json[{index}]"
        if item.get("role") not in ALLOWED_ROLES:
            errors.append(f"{label}.role is outside scope: {item.get('role')}")
        if item.get("status") not in ALLOWED_STATUSES:
            errors.append(f"{label}.status is invalid: {item.get('status')}")
        if item.get("id") in ids:
            errors.append(f"Duplicate opportunity id: {item.get('id')}")
        ids.add(item.get("id"))
        key = (
            str(item.get("sourceUrl", "")).rstrip("/").casefold(),
            str(item.get("role", "")).casefold(),
            str(item.get("organisation", "")).casefold(),
        )
        if key in keys:
            errors.append(f"Duplicate opportunity: {key}")
        keys.add(key)
        parsed = urlparse(str(item.get("sourceUrl", "")))
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            errors.append(f"{label}.sourceUrl is invalid.")

    social_ids: set[str] = set()
    social_urls: set[str] = set()
    for index, item in enumerate(social_sources):
        label = f"data/social_sources.json[{index}]"
        if item.get("platform") not in {"Instagram", "LinkedIn"}:
            errors.append(f"{label}.platform is invalid.")
        if item.get("id") in social_ids:
            errors.append(f"Duplicate social source id: {item.get('id')}")
        social_ids.add(item.get("id"))
        url = str(item.get("profileUrl", "")).rstrip("/").casefold()
        if url in social_urls:
            errors.append(f"Duplicate social source URL: {url}")
        social_urls.add(url)
        parsed = urlparse(str(item.get("profileUrl", "")))
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            errors.append(f"{label}.profileUrl is invalid.")
        jobs_url = str(item.get("jobsUrl", ""))
        if item.get("platform") == "LinkedIn":
            parsed_jobs = urlparse(jobs_url)
            if parsed_jobs.scheme not in {"http", "https"} or not parsed_jobs.netloc:
                errors.append(f"{label}.jobsUrl is invalid.")

    contact_ids: set[str] = set()
    contact_keys: set[tuple[str, str]] = set()
    for index, item in enumerate(contacts):
        label = f"data/contacts.json[{index}]"
        if item.get("status") != "To Verify":
            errors.append(f"{label}.status must remain To Verify.")
        if item.get("id") in contact_ids:
            errors.append(f"Duplicate contact id: {item.get('id')}")
        contact_ids.add(item.get("id"))
        key = (
            str(item.get("organisation", "")).casefold(),
            str(item.get("email", "")).casefold(),
        )
        if key in contact_keys:
            errors.append(f"Duplicate generated contact: {key}")
        contact_keys.add(key)
        email = str(item.get("email", ""))
        if email.count("@") != 1 or " " in email:
            errors.append(f"{label}.email is invalid.")
        parsed = urlparse(str(item.get("sourceUrl", "")))
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            errors.append(f"{label}.sourceUrl is invalid.")

    if errors:
        print("Pipeline validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Pipeline validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

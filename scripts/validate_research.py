#!/usr/bin/env python3
from __future__ import annotations
import json
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    errors = []
    for path in [
        ROOT / "config" / "research_sources.json",
        ROOT / "config" / "research_terms.json",
        ROOT / "data" / "research_inbox.json",
        ROOT / "data" / "research_state.json",
    ]:
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"{path.relative_to(ROOT)}: {exc}")

    inbox = json.loads((ROOT / "data" / "research_inbox.json").read_text(encoding="utf-8"))
    ids = set()
    for idx, lead in enumerate(inbox):
        label = f"research_inbox[{idx}]"
        if lead.get("id") in ids:
            errors.append(f"Duplicate lead id: {lead.get('id')}")
        ids.add(lead.get("id"))
        if lead.get("status") not in {"To Verify", "Rejected", "Promoted"}:
            errors.append(f"{label}: invalid status")
        url = lead.get("sourceUrl", "")
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            errors.append(f"{label}: invalid source URL")

    if errors:
        print("Research validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Research validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

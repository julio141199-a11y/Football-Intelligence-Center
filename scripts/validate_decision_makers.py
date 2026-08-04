#!/usr/bin/env python3
"""Validate the focused AFC/OFC federation decision-maker database."""
import json
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = {
    "id", "country", "confederation", "priority", "association", "officialWebsite",
    "officialEmail", "officialPhone", "president", "generalSecretary", "technicalDirector",
    "nationalCoachMen", "recommendedRecipient", "applicationRoute", "sourceUrl",
    "lastVerified", "verificationStatus"
}


def main() -> int:
    records = json.loads((ROOT / "data/decision_makers.json").read_text(encoding="utf-8"))
    errors, ids, countries = [], set(), set()
    for item in records:
        missing = REQUIRED - set(item)
        if missing:
            errors.append(f"{item.get('country')}: missing {sorted(missing)}")
        if item.get("id") in ids or item.get("country") in countries:
            errors.append(f"duplicate record: {item.get('country')}")
        ids.add(item.get("id")); countries.add(item.get("country"))
        if item.get("confederation") not in {"AFC", "OFC"}:
            errors.append(f"{item.get('country')}: invalid confederation")
        parsed = urlparse(item.get("sourceUrl", ""))
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            errors.append(f"{item.get('country')}: invalid source")
    if len(records) != 31:
        errors.append(f"expected 31 target associations, found {len(records)}")
    if errors:
        print("\n".join(errors)); return 1
    print(f"Decision-maker validation passed: {len(records)} associations.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Refresh public federation decision-makers from official FIFA association pages."""
from __future__ import annotations

import argparse
import html
import json
import re
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "decision_maker_markets.json"
OUTPUT = ROOT / "data" / "decision_makers.json"
ROLE_KEYS = {
    "President": "president",
    "General Secretary": "generalSecretary",
    "Acting General Secretary": "generalSecretary",
    "Technical Director": "technicalDirector",
    "National Coach Men": "nationalCoachMen",
    "National Coach Women": "nationalCoachWomen",
}


def read_json(path: Path, default):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def extract_json_string(document: str, pattern: str) -> str:
    match = re.search(pattern, document)
    return html.unescape(json.loads(f'"{match.group(1)}"')) if match else "Not publicly listed"


def parse_fifa_page(document: str, market: dict, source_url: str, checked: str) -> dict:
    association = extract_json_string(document, r'"association":\{"label":"Member Associations","value":"((?:\\.|[^"\\])*)"')
    website = extract_json_string(document, r'"website":\{"label":"Website","href":"((?:\\.|[^"\\])*)"')
    email = extract_json_string(document, r'"email":\{"label":"Email","data":"((?:\\.|[^"\\])*)"')
    phone = extract_json_string(document, r'"phone":\{"label":"Phone","data":"((?:\\.|[^"\\])*)"')
    people = {value: "Not publicly listed" for value in ROLE_KEYS.values()}
    for match in re.finditer(r'\{"name":"((?:\\.|[^"\\])*)","roles":(\[[^\]]*\])', document):
        name = html.unescape(json.loads(f'"{match.group(1)}"'))
        try:
            roles = json.loads(match.group(2))
        except json.JSONDecodeError:
            continue
        for role in roles:
            if role in ROLE_KEYS and people[ROLE_KEYS[role]] == "Not publicly listed":
                people[ROLE_KEYS[role]] = name
    if association == "Not publicly listed":
        raise ValueError("FIFA association payload was not found")
    return {
        "id": f"federation-{market['fifaCode'].lower()}",
        "country": market["country"], "fifaCode": market["fifaCode"],
        "confederation": market["confederation"], "priority": market["priority"],
        "association": association, "officialWebsite": website,
        "officialEmail": email, "officialPhone": phone, **people,
        "recommendedRecipient": people["technicalDirector"] if people["technicalDirector"] != "Not publicly listed" else people["generalSecretary"],
        "applicationRoute": "Use the official federation email to ask the Technical Director or General Secretary for the correct coaching application route.",
        "sourceUrl": source_url, "sourceType": "FIFA official member-association page",
        "lastVerified": checked, "verificationStatus": "Verified official directory",
        "notes": "Public professional information only; confirm the recipient before sending a CV."
    }


def fetch(url: str, timeout: int) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "FIC-Decision-Maker-Watch/1.0"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace")


def refresh(timeout: int = 20) -> tuple[int, int]:
    markets = read_json(CONFIG, {"markets": []})["markets"]
    existing = {item["country"]: item for item in read_json(OUTPUT, [])}
    checked = datetime.now(timezone.utc).date().isoformat()
    successes = failures = 0
    fifa_markets = []
    for market in markets:
        code = market.get("fifaCode")
        if not code:
            existing.setdefault(market["country"], {
                "id": "federation-nmi", "country": market["country"], "fifaCode": "",
                "confederation": market["confederation"], "priority": market["priority"],
                "association": "Northern Mariana Islands Football Association",
                "officialWebsite": market["officialWebsite"], "officialEmail": "Not publicly listed",
                "officialPhone": "Not publicly listed", "president": "Needs verification",
                "generalSecretary": "Needs verification", "technicalDirector": "Needs verification",
                "nationalCoachMen": "Needs verification", "nationalCoachWomen": "Needs verification",
                "recommendedRecipient": "General Secretary / Technical Director",
                "applicationRoute": "Use the NMIFA official contact route and request the correct coaching recipient.",
                "sourceUrl": market["officialWebsite"], "sourceType": "Official association website",
                "lastVerified": "Needs verification", "verificationStatus": "Research required",
                "notes": market["note"]
            })
            continue
        fifa_markets.append(market)

    def collect(market: dict) -> tuple[str, dict]:
        url = f"https://inside.fifa.com/associations/{market['fifaCode']}/organisation"
        return market["country"], parse_fifa_page(fetch(url, timeout), market, url, checked)

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(collect, market): market for market in fifa_markets}
        for future in as_completed(futures):
            market = futures[future]
            try:
                country, record = future.result()
                existing[country] = record
                successes += 1
            except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
                failures += 1
                print(f"WARNING {market['country']}: {exc}")
    records = sorted(existing.values(), key=lambda item: (item.get("confederation", ""), item.get("country", "")))
    write_json(OUTPUT, records)
    return successes, failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=int, default=20)
    args = parser.parse_args()
    successes, failures = refresh(args.timeout)
    print(f"Decision-maker records refreshed: {successes}; failures preserved: {failures}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

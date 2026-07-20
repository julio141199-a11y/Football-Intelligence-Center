#!/usr/bin/env python3
"""Create a Markdown review report from unverified research leads."""

from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INBOX = ROOT / "data" / "research_inbox.json"
REPORT = ROOT / "data" / "research_report.md"


def main() -> int:
    leads = json.loads(INBOX.read_text(encoding="utf-8"))
    pending = [lead for lead in leads if lead.get("status") == "To Verify"]

    lines = [
        "# FIC Research Review",
        "",
        f"Pending leads: **{len(pending)}**",
        "",
        "These are leads only. They must not be copied into `jobs.json` until verified.",
        "",
    ]

    for lead in pending[:50]:
        lines.extend([
            f"## {lead.get('title', 'Untitled lead')}",
            f"- Region: {lead.get('region', 'To verify')}",
            f"- Source: {lead.get('sourceName', 'Unknown')}",
            f"- Official source flag: {lead.get('sourceOfficial', False)}",
            f"- URL: {lead.get('sourceUrl', '')}",
            f"- Discovered: {lead.get('discoveredAt', '')}",
            f"- Status: {lead.get('status', '')}",
            "",
        ])

    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Research report created with {len(pending)} pending leads.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

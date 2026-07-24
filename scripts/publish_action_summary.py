#!/usr/bin/env python3
"""Create a concise GitHub Actions summary and a high-signal alert body."""

from __future__ import annotations

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def current_candidates(updates: list[dict], opportunities: list[dict]) -> tuple[dict, list[dict]]:
    latest = updates[0] if updates else {}
    run_at = latest.get("runAt")
    candidates = [
        item
        for item in opportunities
        if run_at and item.get("detectedAt") == run_at and item.get("role") in {"Head Coach", "Assistant Coach"}
    ]
    return latest, candidates


def summary_markdown(latest: dict, candidates: list[dict]) -> str:
    lines = [
        "# FIC Daily Update",
        "",
        f"- Sources checked: {latest.get('sourcesChecked', 0)}",
        f"- Official social profiles: {latest.get('socialProfiles', 0)}",
        f"- New Head/Assistant Coach candidates: {len(candidates)}",
        f"- New contact candidates: {latest.get('newContacts', 0)}",
        f"- Warnings: {len(latest.get('warnings', []))}",
    ]
    if candidates:
        lines.extend(["", "## New candidates"])
        for item in candidates:
            lines.append(
                f"- [{item.get('role')}: {item.get('organisation')}]"
                f"({item.get('sourceUrl')}) — {item.get('country')} — **To Verify**"
            )
    return "\n".join(lines) + "\n"


def main() -> int:
    latest, candidates = current_candidates(
        load(ROOT / "data" / "updates.json"),
        load(ROOT / "data" / "opportunities.json"),
    )
    summary = summary_markdown(latest, candidates)
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    output_path = os.environ.get("GITHUB_OUTPUT")
    alert_path = os.environ.get("FIC_ALERT_PATH")

    if summary_path:
        with Path(summary_path).open("a", encoding="utf-8") as handle:
            handle.write(summary)
    else:
        print(summary, end="")
    if alert_path:
        Path(alert_path).write_text(summary, encoding="utf-8")
    if output_path:
        with Path(output_path).open("a", encoding="utf-8") as handle:
            handle.write(f"new_candidates={len(candidates)}\n")
            handle.write(f"run_date={str(latest.get('runAt', 'unknown'))[:10]}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

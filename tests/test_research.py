import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_research_files_parse():
    for rel in [
        "config/research_sources.json",
        "config/research_terms.json",
        "data/research_inbox.json",
        "data/research_state.json",
    ]:
        json.loads((ROOT / rel).read_text(encoding="utf-8"))


def test_research_validator():
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "validate_research.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr

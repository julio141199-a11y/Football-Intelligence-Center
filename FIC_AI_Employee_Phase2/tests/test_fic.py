import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_jobs_json_parses():
    data = json.loads((ROOT / "jobs.json").read_text(encoding="utf-8"))
    assert isinstance(data, list)


def test_repository_validator():
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "validate_repository.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from run_pipeline import match_candidate


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


def test_pipeline_validator():
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "validate_pipeline.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_pipeline_accepts_only_target_roles():
    assert match_candidate("Head Coach vacancy", "https://example.com/jobs") == ("Head Coach", "Vacancy")
    assert match_candidate("Assistant Coach recruitment", "https://example.com/jobs") == ("Assistant Coach", "Vacancy")
    assert match_candidate("Fitness Coach vacancy", "https://example.com/jobs") is None

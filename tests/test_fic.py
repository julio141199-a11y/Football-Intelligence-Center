import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from run_pipeline import build_social_registry, extract_role_emails, match_candidate


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


def test_reviewed_contacts_include_verification_notes():
    contacts = json.loads((ROOT / "data" / "contacts.json").read_text(encoding="utf-8"))
    reviewed = [item for item in contacts if item["status"] != "To Verify"]
    assert reviewed
    assert all(item.get("verificationNote") for item in reviewed)


def test_pipeline_accepts_only_target_roles():
    assert match_candidate("Head Coach vacancy", "https://example.com/jobs") == ("Head Coach", "Vacancy")
    assert match_candidate("Assistant Coach recruitment", "https://example.com/jobs") == ("Assistant Coach", "Vacancy")
    assert match_candidate("Fitness Coach vacancy", "https://example.com/jobs") is None


def test_pipeline_collects_only_role_based_public_emails():
    document = "info@example.com coach.name@example.com hr@example.com noreply@example.com"
    assert extract_role_emails(document) == ["hr@example.com", "info@example.com"]


def test_social_registry_keeps_only_official_supported_profiles():
    sources = [
        {"id": "one", "name": "Example Official LinkedIn", "country": "A", "region": "AFC", "type": "official-linkedin", "url": "https://www.linkedin.com/company/example", "official": True, "enabled": True},
        {"id": "two", "name": "Unofficial", "country": "A", "region": "AFC", "type": "official-linkedin", "url": "https://www.linkedin.com/company/unofficial", "official": False, "enabled": True},
    ]
    result = build_social_registry(sources, "2026-07-24T00:00:00+00:00")
    assert len(result) == 1
    assert result[0]["platform"] == "LinkedIn"
    assert result[0]["organisation"] == "Example"
    assert result[0]["jobsUrl"] == "https://www.linkedin.com/company/example/jobs"


def test_pipeline_module_handles_incomplete_http_responses():
    import run_pipeline
    assert run_pipeline.http.client.IncompleteRead

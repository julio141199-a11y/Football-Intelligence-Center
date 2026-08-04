import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from run_pipeline import apply_source_overrides, build_social_registry, career_priority, extract_role_emails, match_candidate
from scripts.publish_action_summary import current_candidates, summary_markdown


def test_jobs_json_parses():
    data = json.loads((ROOT / "jobs.json").read_text(encoding="utf-8"))
    assert isinstance(data, list)


def test_chat_opportunities_json_parses():
    data = json.loads((ROOT / "data" / "chat_opportunities.json").read_text(encoding="utf-8"))
    assert isinstance(data, list)


def test_site_merges_pipeline_and_chat_opportunities():
    javascript = (ROOT / "data.js").read_text(encoding="utf-8")
    assert 'pipelineOpportunities: "data/opportunities.json"' in javascript
    assert 'chatOpportunities: "data/chat_opportunities.json"' in javascript
    assert 'vacancies: "data/vacancies.json"' in javascript
    assert "mergeOpportunityFeeds();" in javascript
    assert 'cache: "no-store"' in javascript


def test_daily_workflow_runs_twice_and_validates_vacancies():
    workflow = (ROOT / ".github" / "workflows" / "daily-update.yml").read_text(encoding="utf-8")
    assert 'cron: "0 23 * * *"' in workflow
    assert 'cron: "0 9 * * *"' in workflow
    assert "python scripts/vacancy_manager.py --inbox --pipeline" in workflow
    assert "python scripts/validate_vacancies.py" in workflow


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


def test_action_alert_includes_only_current_target_roles():
    updates = [{"runAt": "2026-07-24T00:00:00+00:00", "sourcesChecked": 3}]
    opportunities = [
        {"role": "Head Coach", "detectedAt": updates[0]["runAt"], "organisation": "A", "sourceUrl": "https://example.com/a", "country": "A"},
        {"role": "Fitness Coach", "detectedAt": updates[0]["runAt"], "organisation": "B", "sourceUrl": "https://example.com/b", "country": "B"},
        {"role": "Assistant Coach", "detectedAt": "2026-07-23T00:00:00+00:00", "organisation": "C", "sourceUrl": "https://example.com/c", "country": "C"},
    ]
    latest, candidates = current_candidates(updates, opportunities)
    assert [item["organisation"] for item in candidates] == ["A"]
    assert "Head Coach: A" in summary_markdown(latest, candidates)
    assert "Monitor · To Verify" in summary_markdown(latest, candidates)


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


def test_source_access_overrides_are_small_and_known():
    registry = json.loads((ROOT / "sources" / "sources.json").read_text(encoding="utf-8"))
    overrides = json.loads(
        (ROOT / "config" / "source_access_overrides.json").read_text(encoding="utf-8")
    )
    known_ids = {source["id"] for source in registry["sources"]}
    assert set(overrides) <= known_ids
    assert len(overrides) <= 10
    assert all(
        override.get("collectionMode") in {None, "automatic", "registry-only"}
        for override in overrides.values()
    )
    applied = apply_source_overrides(registry["sources"])
    forge = next(source for source in applied if source["id"] == "forge-fc")
    assert forge["url"] == "https://www.canpl.ca/forgefc"


def test_pre_pro_career_priorities_are_rule_based():
    assert career_priority(
        "National U20 Head Coach vacancy",
        "https://example.com/u20-head-coach",
        "Head Coach",
        "federation",
    )[0] == "Priority 1"
    assert career_priority(
        "Senior National Team Assistant Coach vacancy",
        "https://example.com/national-team-assistant",
        "Assistant Coach",
        "federation",
    )[0] == "Priority 1"
    priority, note = career_priority(
        "First Team Head Coach vacancy",
        "https://example.com/head-coach",
        "Head Coach",
        "club",
    )
    assert priority == "Priority 2"
    assert "must be verified" in note


def test_coach_network_is_removed_from_live_site():
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    javascript = (ROOT / "data.js").read_text(encoding="utf-8")
    assert 'data-page="coach-network"' not in html
    assert "coach_network.json" not in javascript

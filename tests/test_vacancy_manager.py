import json
import sys
from datetime import date
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import import_chat_vacancies  # noqa: E402
import vacancy_manager  # noqa: E402
from vacancy_manager import VacancyError, normalise, upsert  # noqa: E402


def raw(**changes):
    value = {
        "organization": "Test Football Federation", "country": "Testland",
        "role": "Head Coach", "team_level": "Senior National Team", "team_gender": "Men",
        "official_source_url": "https://football.example/vacancy", "deadline": "2026-08-10",
    }
    value.update(changes)
    return value


def test_roles_and_organisation_scope():
    today = date(2026, 8, 4)
    assert normalise(raw(), today=today)["role"] == "Head Coach"
    assert normalise(raw(role="Assistant Manager"), today=today)["role"] == "Assistant Coach"
    assert normalise(raw(team_level="Women's Senior National Team", team_gender="Women"), today=today)["role"] == "Head Coach"
    assert normalise(raw(team_level="Men's Professional Club First Team"), today=today)["role"] == "Head Coach"
    assert normalise(raw(team_level="Women's National U20", team_gender="Women"), today=today)["role"] == "Head Coach"
    for role in ("Fitness Coach", "Technical Director", "Coach Education", "Performance Analyst", "Scout"):
        with pytest.raises(VacancyError):
            normalise(raw(role=role), today=today)
    with pytest.raises(VacancyError):
        normalise(raw(team_level="Women's Professional Club First Team", team_gender="Women"), today=today)
    with pytest.raises(VacancyError):
        normalise(raw(team_level="Academy"), today=today)


def test_new_duplicate_updated_closing_expired_and_closed():
    today = date(2026, 8, 4)
    vacancies, history = [], []
    first = normalise(raw(), today=today)
    assert first["status"] == "CLOSING_SOON"
    assert upsert(vacancies, first, history, today=today) == "created"
    assert upsert(vacancies, first, history, today=today) == "unchanged"
    changed = normalise(raw(deadline="2026-08-20"), today=today)
    assert upsert(vacancies, changed, history, today=today) == "updated"
    assert vacancies[0]["status"] == "UPDATED"
    assert normalise(raw(deadline="2026-08-01"), today=today)["status"] == "EXPIRED"
    assert normalise(raw(status="Filled", deadline=""), today=today)["status"] == "CLOSED"


def configure_paths(tmp_path, monkeypatch):
    paths = {name: tmp_path / filename for name, filename in {
        "VACANCIES_PATH": "vacancies.json", "HISTORY_PATH": "history.json", "ARCHIVE_PATH": "archive.json",
        "UPDATE_LOG_PATH": "update.json", "ERROR_LOG_PATH": "error.json", "CHAT_PATH": "chat.json",
        "PIPELINE_PATH": "pipeline.json",
    }.items()}
    for name, path in paths.items():
        monkeypatch.setattr(vacancy_manager, name, path)
    paths["PIPELINE_PATH"].write_text("[]\n", encoding="utf-8")
    return paths


def test_chat_feed_to_vacancies_to_website_integration(tmp_path, monkeypatch):
    paths = configure_paths(tmp_path, monkeypatch)
    summary = import_chat_vacancies.upsert_feed([raw(deadline="2026-08-20")], feed_path=paths["CHAT_PATH"], today="2026-08-04")
    assert summary["created"] == 1
    result = vacancy_manager.run(files=[], include_pipeline=False, include_chat=True, today_value="2026-08-04")
    assert result["created"] == 1
    vacancies = json.loads(paths["VACANCIES_PATH"].read_text())
    assert vacancies[0]["role"] == "Head Coach"
    javascript = (ROOT / "data.js").read_text(encoding="utf-8")
    assert 'chatOpportunities: "data/chat_opportunities.json"' in javascript
    assert "item.official_source_url ? vacancyToJob(item)" in javascript


def test_inbox_import_moves_processed_and_deduplicates(tmp_path):
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    feed = tmp_path / "chat.json"
    payload = raw(role="Assistant Coach", deadline="2026-08-20")
    (inbox / "reviewed.json").write_text(json.dumps(payload), encoding="utf-8")
    first = import_chat_vacancies.import_inbox(inbox_path=inbox, feed_path=feed, today="2026-08-04")
    assert first["created"] == 1 and first["processed_files"] == 1
    assert (inbox / "processed" / "reviewed.json").exists()
    assert len(json.loads(feed.read_text())) == 1
    assert import_chat_vacancies.upsert_feed([payload], feed_path=feed, today="2026-08-04")["unchanged"] == 1


def test_rejected_input_never_enters_reviewed_feed(tmp_path):
    feed = tmp_path / "chat.json"
    with pytest.raises(VacancyError):
        import_chat_vacancies.upsert_feed([raw(role="Fitness Coach")], feed_path=feed, today="2026-08-04")
    assert not feed.exists()

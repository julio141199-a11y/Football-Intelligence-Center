import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import vacancy_manager  # noqa: E402
from import_chat_opportunities import import_records  # noqa: E402
from vacancy_manager import VacancyError, normalise, upsert  # noqa: E402


def raw(**changes):
    value = {
        "organization": "Test Football Federation",
        "country": "Testland",
        "role": "Head Coach",
        "team_level": "Senior National Team",
        "official_source_url": "https://football.example/vacancy",
        "deadline": "2026-08-10",
    }
    value.update(changes)
    return value


def test_new_duplicate_and_updated_change_history():
    today = date(2026, 8, 4)
    vacancies, history = [], []
    first = normalise(raw(), today=today)
    assert first["status"] == "CLOSING_SOON"
    assert upsert(vacancies, first, history, today=today) == "created"
    assert upsert(vacancies, first, history, today=today) == "unchanged"
    changed = normalise(raw(deadline="2026-08-20"), today=today)
    assert upsert(vacancies, changed, history, today=today) == "updated"
    assert vacancies[0]["status"] == "UPDATED"
    assert history[-1]["changed_fields"]


def test_deadline_and_closed_states():
    assert normalise(raw(deadline="2026-08-01"), today=date(2026, 8, 4))["status"] == "EXPIRED"
    assert normalise(raw(status="Closed", deadline=""), today=date(2026, 8, 4))["status"] == "CLOSED"


def test_accepts_fitness_coach_and_rejects_technical_director():
    import pytest
    assert normalise(raw(role="Fitness Coach"), today=date(2026, 8, 4))["role"] == "Fitness Coach"
    with pytest.raises(VacancyError):
        normalise(raw(role="Technical Director"), today=date(2026, 8, 4))
    with pytest.raises(VacancyError):
        normalise(raw(official_source_url="To verify"), today=date(2026, 8, 4))
    with pytest.raises(VacancyError):
        normalise(raw(team_level="Women's Professional Club", team_gender="Women"), today=date(2026, 8, 4))
    with pytest.raises(VacancyError):
        normalise(raw(team_level="Academy"), today=date(2026, 8, 4))
    assert normalise(raw(team_level="Women's National Team", team_gender="Women"), today=date(2026, 8, 4))["role"] == "Head Coach"


def test_same_vacancy_source_hash_is_not_duplicated():
    today = date(2026, 8, 4)
    vacancies, history = [], []
    first = normalise(raw(), today=today)
    same_content_different_id = {**first, "id": "vacancy-different-id"}
    assert upsert(vacancies, first, history, today=today) == "created"
    assert upsert(vacancies, same_content_different_id, history, today=today) == "unchanged"
    assert len(vacancies) == 1


def test_chat_feed_to_vacancies_to_website_integration(tmp_path, monkeypatch):
    paths = {
        "VACANCIES_PATH": tmp_path / "vacancies.json",
        "HISTORY_PATH": tmp_path / "history.json",
        "ARCHIVE_PATH": tmp_path / "archive.json",
        "UPDATE_LOG_PATH": tmp_path / "update.json",
        "ERROR_LOG_PATH": tmp_path / "error.json",
        "CHAT_PATH": tmp_path / "chat.json",
        "PIPELINE_PATH": tmp_path / "pipeline.json",
    }
    for name, path in paths.items():
        monkeypatch.setattr(vacancy_manager, name, path)
    paths["PIPELINE_PATH"].write_text("[]\n", encoding="utf-8")
    reviewed = raw(role="Fitness Coach", deadline="2026-08-20", team_gender="Women")
    assert import_records([reviewed], feed_path=paths["CHAT_PATH"], today="2026-08-04")["created"] == 1
    summary = vacancy_manager.run(files=[], include_pipeline=True, include_chat=True, today_value="2026-08-04")
    assert summary["created"] == 1
    vacancies = vacancy_manager.read_json(paths["VACANCIES_PATH"], [])
    assert len(vacancies) == 1
    assert vacancies[0]["role"] == "Fitness Coach"
    javascript = (ROOT / "data.js").read_text(encoding="utf-8")
    assert 'chatOpportunities: "data/chat_opportunities.json"' in javascript
    assert "state.chatOpportunities.map(pipelineOpportunityToJob)" in javascript
    assert "state.vacancies.map(vacancyToJob)" in javascript

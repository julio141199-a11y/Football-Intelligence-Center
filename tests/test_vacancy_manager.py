import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

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


def test_rejects_wrong_role_and_placeholder_source():
    import pytest
    with pytest.raises(VacancyError):
        normalise(raw(role="Fitness Coach"), today=date(2026, 8, 4))
    with pytest.raises(VacancyError):
        normalise(raw(official_source_url="To verify"), today=date(2026, 8, 4))

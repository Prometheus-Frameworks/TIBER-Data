import json
from datetime import date, datetime
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

OWNERSHIP_STATUSES = {
    "active_roster", "practice_squad", "unsigned_draft_pick", "college", "devy",
    "free_agent", "retired", "injured_reserve", "suspended", "unknown",
}
EVENT_TYPES = {
    "team_change", "status_change", "signing", "release", "trade", "draft_selection",
    "practice_squad_change", "injured_reserve_change", "free_agent_status_change", "college_program_change",
}


def _parse_dt(v: str) -> None:
    datetime.fromisoformat(v.replace("Z", "+00:00"))


def _validate_source_refs(source_refs: list[dict]) -> None:
    assert source_refs and isinstance(source_refs, list)
    for ref in source_refs:
        assert ref["source_name"]
        _parse_dt(ref["observed_at"])
        assert ref["confidence"]


def test_player_ownership_latest_fixture_valid() -> None:
    payload = json.loads((ROOT / "exports/promoted/player_ownership/player_ownership_latest.json").read_text())
    assert payload["contract_version"] == "player_ownership_v0"
    _parse_dt(payload["generated_at"])
    assert payload["players"]
    for row in payload["players"]:
        assert row["ownership_status"] in OWNERSHIP_STATUSES
        _parse_dt(row["last_verified_at"])
        if row["valid_from"] is not None:
            _parse_dt(row["valid_from"])
        if row["valid_to"] is not None:
            _parse_dt(row["valid_to"])
        _validate_source_refs(row["source_refs"])


def test_player_ownership_event_fixture_valid() -> None:
    path = ROOT / "exports/promoted/player_ownership/events/player_ownership_events_2026.jsonl"
    events = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    assert events
    for event in events:
        assert event["event_type"] in EVENT_TYPES
        _parse_dt(event["detected_at"])
        date.fromisoformat(event["effective_date"])
        assert event["source_refs"]
        _validate_source_refs(event["source_refs"])


def test_player_ownership_fails_closed_on_invalid_status() -> None:
    row = {
        "ownership_status": "starter_lock",
        "last_verified_at": "2026-05-23T13:00:00Z",
        "source_refs": [{"source_name": "x", "observed_at": "2026-05-23T13:00:00Z", "confidence": "c"}],
    }
    with pytest.raises(AssertionError):
        assert row["ownership_status"] in OWNERSHIP_STATUSES


def test_player_ownership_fails_closed_on_invalid_timestamps() -> None:
    with pytest.raises(ValueError):
        _parse_dt("2026/05/23 13:00:00")


def test_player_ownership_fails_closed_on_missing_source_metadata() -> None:
    with pytest.raises((AssertionError, KeyError)):
        _validate_source_refs([{"source_name": "fixture_without_observed_at"}])


def test_player_ownership_event_fails_closed_on_malformed_event() -> None:
    malformed = {"event_type": "tradee", "detected_at": "bad-ts", "effective_date": "2026-13-77", "source_refs": []}
    with pytest.raises(AssertionError):
        assert malformed["event_type"] in EVENT_TYPES

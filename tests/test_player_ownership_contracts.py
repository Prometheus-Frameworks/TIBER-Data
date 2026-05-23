import json
import re
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
RFC3339_UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


def _is_rfc3339_utc_datetime(value: str) -> bool:
    if not isinstance(value, str):
        return False
    if not RFC3339_UTC_RE.match(value):
        return False
    # Ensure calendar/time components are real values, not just shape matches.
    try:
        from datetime import datetime

        datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return False
    return True


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def _validator(schema_path: str) -> Draft202012Validator:
    schema = _load_json(ROOT / schema_path)
    format_checker = FormatChecker()
    format_checker.checks("date-time")(_is_rfc3339_utc_datetime)
    return Draft202012Validator(schema, format_checker=format_checker)


def test_player_ownership_latest_fixture_validates_against_schema() -> None:
    validator = _validator("schemas/player_ownership_v0.schema.json")
    payload = _load_json(ROOT / "exports/promoted/player_ownership/player_ownership_latest.json")
    validator.validate(payload)


def test_player_ownership_event_fixture_validates_against_schema() -> None:
    validator = _validator("schemas/player_ownership_change_event_v0.schema.json")
    path = ROOT / "exports/promoted/player_ownership/events/player_ownership_events_2026.jsonl"
    events = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    assert events
    for event in events:
        validator.validate(event)


def test_player_ownership_schema_rejects_invalid_status_value() -> None:
    validator = _validator("schemas/player_ownership_v0.schema.json")
    payload = _load_json(ROOT / "exports/promoted/player_ownership/player_ownership_latest.json")
    payload["players"][0]["ownership_status"] = "starter_lock"
    with pytest.raises(Exception):
        validator.validate(payload)


def test_player_ownership_schema_rejects_invalid_timestamp_format() -> None:
    validator = _validator("schemas/player_ownership_v0.schema.json")
    payload = _load_json(ROOT / "exports/promoted/player_ownership/player_ownership_latest.json")
    payload["players"][0]["last_verified_at"] = "2026/05/23 13:00:00"
    with pytest.raises(Exception):
        validator.validate(payload)


def test_player_ownership_schema_rejects_missing_required_source_metadata() -> None:
    validator = _validator("schemas/player_ownership_v0.schema.json")
    payload = _load_json(ROOT / "exports/promoted/player_ownership/player_ownership_latest.json")
    del payload["players"][0]["source_refs"][0]["observed_at"]
    with pytest.raises(Exception):
        validator.validate(payload)


def test_event_schema_rejects_malformed_event_record() -> None:
    validator = _validator("schemas/player_ownership_change_event_v0.schema.json")
    event = json.loads(
        (ROOT / "exports/promoted/player_ownership/events/player_ownership_events_2026.jsonl").read_text().splitlines()[0]
    )
    event["event_type"] = "tradee"
    with pytest.raises(Exception):
        validator.validate(event)

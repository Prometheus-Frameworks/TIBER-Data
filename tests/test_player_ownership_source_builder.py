from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.build_player_ownership_source_roster_smoke_test_2026_05_24 import (
    NAME_ALIASES,
    SMOKE_TEST_NAMES,
    build_draft_row,
    build_roster_row,
    build_source_output,
    load_draft_by_name,
    load_roster_by_latest_week,
    match_draft_player,
    match_roster_player,
    normalize_input_name,
)

ROOT = Path(__file__).resolve().parents[1]
RFC3339_UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")

ROSTER_SOURCE_PATH = ROOT / "data/processed/evidence/roster_player_team_map_2025.source_backed.json"
DRAFT_SOURCE_PATH = ROOT / "exports/promoted/nfl_draft_results/nfl_draft_results_2026.json"


# ---------------------------------------------------------------------------
# Name normalization
# ---------------------------------------------------------------------------


def test_normalize_input_name_applies_jr_alias() -> None:
    assert normalize_input_name("Michael Penix") == "Michael Penix Jr."
    assert normalize_input_name("Chris Rodriguez") == "Chris Rodriguez Jr."
    assert normalize_input_name("Mike Washington") == "Mike Washington Jr."


def test_normalize_input_name_applies_nickname_alias() -> None:
    assert normalize_input_name("Tet McMillan") == "Tetairoa McMillan"


def test_normalize_input_name_returns_name_unchanged_when_no_alias() -> None:
    assert normalize_input_name("Jalen Hurts") == "Jalen Hurts"
    assert normalize_input_name("Dallas Goedert") == "Dallas Goedert"


def test_all_smoke_test_names_are_defined() -> None:
    assert len(SMOKE_TEST_NAMES) == 26


# ---------------------------------------------------------------------------
# Roster matching
# ---------------------------------------------------------------------------


def test_match_roster_player_finds_exact_name() -> None:
    roster = load_roster_by_latest_week(ROSTER_SOURCE_PATH)
    record = match_roster_player("Jalen Hurts", roster)
    assert record is not None
    assert record["player_id"] == "00-0036389"
    assert record["position"] == "QB"
    assert record["team"] == "PHI"


def test_match_roster_player_returns_latest_week_record() -> None:
    roster = load_roster_by_latest_week(ROSTER_SOURCE_PATH)
    record = match_roster_player("Khalil Shakir", roster)
    assert record is not None
    assert record["week"] == 20


def test_match_roster_player_finds_after_normalization() -> None:
    roster = load_roster_by_latest_week(ROSTER_SOURCE_PATH)
    normalized = normalize_input_name("Michael Penix")
    record = match_roster_player(normalized, roster)
    assert record is not None
    assert record["player_name"] == "Michael Penix Jr."
    assert record["player_id"] == "00-0039917"


def test_match_roster_player_finds_tetairoa_mcmillan_via_alias() -> None:
    roster = load_roster_by_latest_week(ROSTER_SOURCE_PATH)
    normalized = normalize_input_name("Tet McMillan")
    record = match_roster_player(normalized, roster)
    assert record is not None
    assert record["player_name"] == "Tetairoa McMillan"
    assert record["team"] == "CAR"


def test_match_roster_player_returns_none_for_unknown_name() -> None:
    roster = load_roster_by_latest_week(ROSTER_SOURCE_PATH)
    assert match_roster_player("Nonexistent Player", roster) is None


# ---------------------------------------------------------------------------
# Draft matching
# ---------------------------------------------------------------------------


def test_match_draft_player_finds_2026_rookie() -> None:
    draft = load_draft_by_name(DRAFT_SOURCE_PATH)
    record = match_draft_player("Garrett Nussmeier", draft)
    assert record is not None
    assert record["player_id"] == "qb-garrett-nussmeier"
    assert record["team"] == "Kansas City Chiefs"


def test_match_draft_player_finds_mike_washington_jr_via_alias() -> None:
    draft = load_draft_by_name(DRAFT_SOURCE_PATH)
    normalized = normalize_input_name("Mike Washington")
    record = match_draft_player(normalized, draft)
    assert record is not None
    assert record["player_id"] == "rb-mike-washington-jr"
    assert record["team"] == "Las Vegas Raiders"


def test_match_draft_player_returns_none_for_unknown_name() -> None:
    draft = load_draft_by_name(DRAFT_SOURCE_PATH)
    assert match_draft_player("Nobody Here", draft) is None


# ---------------------------------------------------------------------------
# Row builders
# ---------------------------------------------------------------------------


def test_build_roster_row_sets_required_ownership_fields() -> None:
    record = {
        "player_id": "00-0036389",
        "player_name": "Jalen Hurts",
        "position": "QB",
        "team": "PHI",
        "week": 19,
    }
    row = build_roster_row("Jalen Hurts", record)
    assert row["player_id"] == "00-0036389"
    assert row["team_id"] == "nfl-phi"
    assert row["team_abbr"] == "PHI"
    assert row["team_name"] == "Philadelphia Eagles"
    assert row["ownership_status"] == "active_roster"
    assert row["football_level"] == "NFL"
    assert row["ownership_confidence"] == "source_verified"
    assert RFC3339_UTC_RE.match(row["observed_at"])


def test_build_roster_row_includes_alias_note_when_name_normalized() -> None:
    record = {
        "player_id": "00-0039917",
        "player_name": "Michael Penix Jr.",
        "position": "QB",
        "team": "ATL",
        "week": 18,
    }
    row = build_roster_row("Michael Penix", record)
    assert "Michael Penix" in row["notes"]
    assert "Michael Penix Jr." in row["notes"]


def test_build_roster_row_no_alias_note_when_name_unchanged() -> None:
    record = {
        "player_id": "00-0036389",
        "player_name": "Jalen Hurts",
        "position": "QB",
        "team": "PHI",
        "week": 19,
    }
    row = build_roster_row("Jalen Hurts", record)
    assert "normalized" not in row["notes"].lower()


def test_build_draft_row_sets_unsigned_draft_pick_status() -> None:
    record = {
        "player_id": "qb-garrett-nussmeier",
        "player_name": "Garrett Nussmeier",
        "position": "QB",
        "team": "Kansas City Chiefs",
        "round": 7,
        "overall_pick": 249,
        "provenance_status": "source_verified",
    }
    row = build_draft_row("Garrett Nussmeier", record)
    assert row is not None
    assert row["ownership_status"] == "unsigned_draft_pick"
    assert row["team_id"] == "nfl-kc"
    assert row["team_abbr"] == "KC"
    assert row["football_level"] == "NFL"
    assert row["ownership_confidence"] == "source_verified"
    assert row["source_url"] is not None


def test_build_draft_row_returns_none_for_unresolved_player_id() -> None:
    record = {
        "player_id": None,
        "player_name": "Mystery Rookie",
        "position": "WR",
        "team": "Buffalo Bills",
        "round": 3,
        "overall_pick": 70,
        "provenance_status": "source_verified_player_id_unresolved",
    }
    assert build_draft_row("Mystery Rookie", record) is None


# ---------------------------------------------------------------------------
# Source metadata
# ---------------------------------------------------------------------------


def test_build_source_output_contains_source_name_and_generated_at() -> None:
    roster = load_roster_by_latest_week(ROSTER_SOURCE_PATH)
    draft = load_draft_by_name(DRAFT_SOURCE_PATH)
    source_payload, _ = build_source_output(
        SMOKE_TEST_NAMES, roster, draft, generated_at="2026-05-24T00:00:00Z"
    )
    assert source_payload["source_name"] == "tiber_data_roster_smoke_test_2026_05_24"
    assert source_payload["generated_at"] == "2026-05-24T00:00:00Z"
    assert isinstance(source_payload["players"], list)


def test_build_source_output_all_26_players_matched() -> None:
    roster = load_roster_by_latest_week(ROSTER_SOURCE_PATH)
    draft = load_draft_by_name(DRAFT_SOURCE_PATH)
    source_payload, match_results = build_source_output(
        SMOKE_TEST_NAMES, roster, draft, generated_at="2026-05-24T00:00:00Z"
    )
    matched = [r for r in match_results if r["matched"]]
    unmatched = [r for r in match_results if not r["matched"]]
    assert len(matched) == 26
    assert len(unmatched) == 0
    assert len(source_payload["players"]) == 26


def test_build_source_output_timestamps_are_rfc3339() -> None:
    roster = load_roster_by_latest_week(ROSTER_SOURCE_PATH)
    draft = load_draft_by_name(DRAFT_SOURCE_PATH)
    source_payload, _ = build_source_output(
        SMOKE_TEST_NAMES, roster, draft, generated_at="2026-05-24T00:00:00Z"
    )
    for row in source_payload["players"]:
        observed_at = row.get("observed_at")
        assert observed_at and RFC3339_UTC_RE.match(observed_at), (
            f"observed_at not RFC3339 for {row.get('player_name')}: {observed_at}"
        )


def test_build_source_output_name_normalized_players_have_notes() -> None:
    roster = load_roster_by_latest_week(ROSTER_SOURCE_PATH)
    draft = load_draft_by_name(DRAFT_SOURCE_PATH)
    _, match_results = build_source_output(
        SMOKE_TEST_NAMES, roster, draft, generated_at="2026-05-24T00:00:00Z"
    )
    normalized = [r for r in match_results if r["name_normalized"]]
    assert len(normalized) == len(NAME_ALIASES)
    input_names = {r["input_name"] for r in normalized}
    assert input_names == set(NAME_ALIASES.keys())


# ---------------------------------------------------------------------------
# Unresolved player handling
# ---------------------------------------------------------------------------


def test_build_source_output_unmatched_player_is_explicit_in_results() -> None:
    roster = load_roster_by_latest_week(ROSTER_SOURCE_PATH)
    draft = load_draft_by_name(DRAFT_SOURCE_PATH)
    names_with_ghost = SMOKE_TEST_NAMES + ["Ghost Player XYZ"]
    _, match_results = build_source_output(
        names_with_ghost, roster, draft, generated_at="2026-05-24T00:00:00Z"
    )
    unmatched = [r for r in match_results if not r["matched"]]
    assert len(unmatched) == 1
    assert unmatched[0]["input_name"] == "Ghost Player XYZ"
    assert "no_source_match" in unmatched[0]["warnings"]
    assert unmatched[0]["player_id"] is None


def test_build_source_output_unmatched_player_not_in_source_rows() -> None:
    roster = load_roster_by_latest_week(ROSTER_SOURCE_PATH)
    draft = load_draft_by_name(DRAFT_SOURCE_PATH)
    names_with_ghost = SMOKE_TEST_NAMES + ["Ghost Player XYZ"]
    source_payload, _ = build_source_output(
        names_with_ghost, roster, draft, generated_at="2026-05-24T00:00:00Z"
    )
    names_in_source = {r["player_name"] for r in source_payload["players"]}
    assert "Ghost Player XYZ" not in names_in_source
    assert len(source_payload["players"]) == 26


# ---------------------------------------------------------------------------
# Schema validation of produced source file
# ---------------------------------------------------------------------------


def test_produced_source_file_validates_against_player_ownership_schema() -> None:
    from jsonschema import Draft202012Validator, FormatChecker

    schema = json.loads((ROOT / "schemas/player_ownership_v0.schema.json").read_text())

    def _is_rfc3339_utc(value: object) -> bool:
        if not isinstance(value, str):
            return True
        if not RFC3339_UTC_RE.match(value):
            return False
        from datetime import datetime

        try:
            datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            return False
        return True

    format_checker = FormatChecker()
    format_checker.checks("date-time")(_is_rfc3339_utc)
    validator = Draft202012Validator(schema, format_checker=format_checker)

    roster = load_roster_by_latest_week(ROSTER_SOURCE_PATH)
    draft = load_draft_by_name(DRAFT_SOURCE_PATH)
    source_payload, _ = build_source_output(
        SMOKE_TEST_NAMES, roster, draft, generated_at="2026-05-24T00:00:00Z"
    )

    from scripts.ingest_player_ownership import normalize_source_player

    source_path = ROOT / "data/raw/player_ownership/player_ownership_source_roster_smoke_test_2026_05_24.json"
    source_meta = {
        k: v
        for k, v in source_payload.items()
        if k not in {"players", "sources"} and not isinstance(v, (dict, list))
    }
    normalized_players = [
        normalize_source_player(row, source_meta=source_meta, source_path=source_path)
        for row in source_payload["players"]
    ]
    payload = {
        "contract_version": "player_ownership_v0",
        "generated_at": "2026-05-24T00:00:00Z",
        "players": normalized_players,
    }
    errors = list(validator.iter_errors(payload))
    assert errors == [], f"Schema errors: {[e.message for e in errors[:5]]}"

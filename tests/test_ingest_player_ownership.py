from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.ingest_player_ownership import build_dry_run_report

ROOT = Path(__file__).resolve().parents[1]
STARTED_AT = "2026-05-23T14:00:00Z"
COMPLETED_AT = "2026-05-23T14:01:00Z"


def _write_json(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def _player(**overrides: object) -> dict:
    player = {
        "player_id": "wr-tee-higgins",
        "player_name": "Tee Higgins",
        "position": "WR",
        "football_level": "NFL",
        "current_team_id": "nfl-cin",
        "current_team_abbr": "CIN",
        "current_team_name": "Cincinnati Bengals",
        "ownership_status": "active_roster",
        "valid_from": "2025-03-01T00:00:00Z",
        "valid_to": None,
        "last_verified_at": "2026-05-23T13:00:00Z",
        "confidence": "provisional",
        "source_refs": [
            {
                "source_name": "fixture_demonstration_only",
                "source_url": None,
                "observed_at": "2026-05-23T13:00:00Z",
                "source_updated_at": None,
                "confidence": "fixture_only",
                "notes": "Fixture-only scaffold artifact.",
            }
        ],
    }
    player.update(overrides)
    return player


def _previous_payload(players: list[dict]) -> dict:
    return {
        "contract_version": "player_ownership_v0",
        "generated_at": "2026-05-23T13:00:00Z",
        "players": players,
    }


def _source_row(**overrides: object) -> dict:
    row = {
        "player_id": "wr-tee-higgins",
        "player_name": "Tee Higgins",
        "position": "wr",
        "football_level": "nfl",
        "team_id": "NFL-CIN",
        "team_abbr": "cin",
        "team_name": "Cincinnati Bengals",
        "ownership_status": "active roster",
        "valid_from": "2025-03-01T00:00:00Z",
        "valid_to": None,
        "ownership_confidence": "source_verified",
        "source_confidence": "fixture_only",
    }
    row.update(overrides)
    return row


def _source_payload(rows: list[dict]) -> dict:
    return {
        "source_name": "pytest_source_fixture",
        "observed_at": "2026-05-23T14:00:00Z",
        "source_confidence": "fixture_only",
        "players": rows,
    }


def _report(tmp_path: Path, *, previous_players: list[dict], source_rows: list[dict]) -> dict:
    previous_path = _write_json(tmp_path / "previous.json", _previous_payload(previous_players))
    source_path = _write_json(tmp_path / "source.json", _source_payload(source_rows))
    return build_dry_run_report(
        source_path=source_path,
        previous_path=previous_path,
        started_at=STARTED_AT,
        completed_at=COMPLETED_AT,
    )


def test_fixture_dry_run_reports_unchanged_against_latest_artifact() -> None:
    report = build_dry_run_report(
        source_path=ROOT / "data/fixtures/player_ownership/source_roster_fixture.json",
        previous_path=ROOT / "exports/promoted/player_ownership/player_ownership_latest.json",
        started_at=STARTED_AT,
        completed_at=COMPLETED_AT,
    )

    assert report["mode"] == "dry_run"
    assert report["players_checked"] == 1
    assert report["unchanged_count"] == 1
    assert report["team_changes"] == []
    assert report["status_changes"] == []
    assert report["validation_errors"] == []
    assert report["would_write_latest_artifact"] is False
    assert report["would_append_change_events"] is False


def test_team_change_candidate_is_reported_with_source_evidence(tmp_path: Path) -> None:
    report = _report(
        tmp_path,
        previous_players=[_player()],
        source_rows=[
            _source_row(
                team_id="nfl-no",
                team_abbr="NO",
                team_name="New Orleans Saints",
            )
        ],
    )

    assert report["unchanged_count"] == 0
    assert report["team_change_count"] == 1
    change = report["team_changes"][0]
    assert change["previous"]["current_team_abbr"] == "CIN"
    assert change["current"]["current_team_abbr"] == "NO"
    assert change["source_refs"][0]["source_name"] == "pytest_source_fixture"


def test_status_change_candidate_is_reported(tmp_path: Path) -> None:
    report = _report(
        tmp_path,
        previous_players=[_player()],
        source_rows=[_source_row(ownership_status="injured reserve")],
    )

    assert report["status_change_count"] == 1
    assert report["status_changes"][0]["previous"]["ownership_status"] == "active_roster"
    assert report["status_changes"][0]["current"]["ownership_status"] == "injured_reserve"
    assert report["team_changes"] == []


def test_unresolved_identity_is_reported_separately(tmp_path: Path) -> None:
    row = _source_row(player_id=None, player_name="Mystery Receiver")
    report = _report(tmp_path, previous_players=[], source_rows=[row])

    assert report["unresolved_identity_count"] == 1
    assert report["identity_unresolved"][0]["reason"] == "missing_player_id"
    assert report["new_players"] == []
    assert report["validation_errors"] == []


def test_invalid_source_row_is_validation_error_and_not_change_candidate(tmp_path: Path) -> None:
    report = _report(
        tmp_path,
        previous_players=[_player()],
        source_rows=[_source_row(ownership_status="starter lock")],
    )

    assert report["validation_error_count"] == 1
    assert report["skipped_invalid_source_count"] == 1
    assert report["status_changes"] == []
    assert report["team_changes"] == []
    assert report["removed_or_missing_from_source"] == []


def test_missing_source_row_is_uncertainty_not_release(tmp_path: Path) -> None:
    report = _report(tmp_path, previous_players=[_player()], source_rows=[])

    assert report["players_checked"] == 0
    assert report["removed_or_missing_from_source_count"] == 1
    assert (
        report["removed_or_missing_from_source"][0]["reason"]
        == "missing_source_row_is_uncertainty_not_release"
    )
    assert report["status_changes"] == []
    assert report["new_players"] == []


def test_source_conflict_is_reported_and_excluded_from_diff(tmp_path: Path) -> None:
    report = _report(
        tmp_path,
        previous_players=[_player()],
        source_rows=[
            _source_row(team_id="nfl-cin", team_abbr="CIN", team_name="Cincinnati Bengals"),
            _source_row(team_id="nfl-no", team_abbr="NO", team_name="New Orleans Saints"),
        ],
    )

    assert report["source_conflict_count"] == 1
    assert report["source_conflicts"][0]["conflict_fields"] == [
        "current_team_id",
        "current_team_abbr",
        "current_team_name",
    ]
    assert report["team_changes"] == []

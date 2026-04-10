from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.compare_forge_weekly_support_lanes import _compare_players
from scripts.compare_forge_weekly_support_lanes import _mismatch_fields
from scripts.compare_forge_weekly_support_lanes import _player_filter
from src.ingest.forge_weekly_upstream_support_scaffold import SUPPORTED_WEEKS


def test_player_filter_orders_by_week_for_amon_ra_focus() -> None:
    sample = [
        {"player_id": "00-0037834", "full_name": "Amon-Ra St. Brown", "season": 2024, "week": 3},
        {"player_id": "00-0037834", "full_name": "Amon-Ra St. Brown", "season": 2024, "week": 1},
        {"player_id": "00-0037834", "full_name": "Amon-Ra St. Brown", "season": 2024, "week": 2},
        {"player_id": "00-0038047", "full_name": "Sam LaPorta", "season": 2024, "week": 1},
    ]

    rows = _player_filter(sample, player_id=None, player_name="Amon-Ra St. Brown")

    assert [int(row["week"]) for row in rows] == list(SUPPORTED_WEEKS)
    assert {str(row["player_id"]) for row in rows} == {"00-0037834"}


def test_player_filter_supports_player_id_focus() -> None:
    sample = [
        {"player_id": "00-0037834", "full_name": "Amon-Ra St. Brown", "season": 2024, "week": 1},
        {"player_id": "00-0038047", "full_name": "Sam LaPorta", "season": 2024, "week": 1},
    ]

    rows = _player_filter(sample, player_id="00-0037834", player_name=None)

    assert len(rows) == 1
    assert rows[0]["full_name"] == "Amon-Ra St. Brown"


def test_compare_players_marks_identity_mismatch(capsys: pytest.CaptureFixture[str]) -> None:
    legacy = [
        {
            "player_id": "00-0037834",
            "full_name": "Amon-Ra St. Brown",
            "team": "DET",
            "season": 2024,
            "week": 1,
        }
    ]
    upstream = [
        {
            "player_id": "00-0036963",
            "full_name": "Amon-Ra St. Brown",
            "team": "DET",
            "season": 2024,
            "week": 1,
        }
    ]
    _compare_players(legacy, upstream, player_id=None, player_name="Amon-Ra St. Brown")
    out = capsys.readouterr().out
    assert "legacy_id=00-0037834" in out
    assert "upstream_id=00-0036963" in out
    assert "id_mismatch" in out
    assert "Player summary: paired_rows=1, id_mismatch_rows=1" in out


def test_mismatch_fields_reports_only_changed_fields() -> None:
    legacy = {"targets": 10, "receptions": 8, "air_yards": 120}
    upstream = {"targets": 10, "receptions": 7, "air_yards": 119}

    fields = _mismatch_fields(legacy, upstream, ("targets", "receptions", "air_yards"))

    assert fields == ["receptions", "air_yards"]

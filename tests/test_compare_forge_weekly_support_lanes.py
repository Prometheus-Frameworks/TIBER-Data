from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

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

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.compare_forge_weekly_derived_lanes import compare_derived_rows


def test_compare_derived_rows_marks_identity_mismatch(capsys: pytest.CaptureFixture[str]) -> None:
    legacy = [
        {
            "season": 2024,
            "week": 1,
            "playerId": "00-0037834",
            "playerName": "Amon-Ra St. Brown",
            "team": "DET",
            "position": "WR",
        }
    ]
    upstream = [
        {
            "season": 2024,
            "week": 1,
            "playerId": "00-0036963",
            "playerName": "Amon-Ra St. Brown",
            "team": "DET",
            "position": "WR",
        }
    ]
    compare_derived_rows(legacy, upstream, player_id=None, player_name="Amon-Ra St. Brown")
    out = capsys.readouterr().out
    assert "legacy_id=00-0037834" in out
    assert "upstream_id=00-0036963" in out
    assert "id_mismatch" in out

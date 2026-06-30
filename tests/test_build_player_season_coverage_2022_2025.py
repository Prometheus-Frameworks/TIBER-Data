from datetime import date
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pytest


def _load_module():
    module_path = Path(__file__).resolve().parents[1] / "scripts" / "build_player_season_coverage_2022_2025.py"
    spec = spec_from_file_location("build_player_season_coverage_2022_2025", module_path)
    assert spec is not None and spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _FakeFrame:
    def __init__(self, rows: list[dict]) -> None:
        self.columns = list(rows[0].keys()) if rows else []
        self._rows = rows

    def to_dicts(self) -> list[dict]:
        return self._rows


# --- pure helper functions -------------------------------------------------


def test_records_from_dataframe_prefers_polars_to_dicts() -> None:
    module = _load_module()

    class _Polars:
        def to_dicts(self):
            return [{"a": 1}]

    assert module._records_from_dataframe(_Polars()) == [{"a": 1}]


def test_records_from_dataframe_falls_back_to_pandas() -> None:
    module = _load_module()

    class _Pandas:
        def to_dict(self, orient):
            assert orient == "records"
            return [{"a": 2}]

    assert module._records_from_dataframe(_Pandas()) == [{"a": 2}]


def test_json_safe_value_handles_nan_inf_and_dates() -> None:
    module = _load_module()
    import math

    assert module._json_safe_value(math.nan) is None
    assert module._json_safe_value(float("inf")) is None
    assert module._json_safe_value(3.5) == 3.5
    assert module._json_safe_value(date(1995, 1, 26)) == "1995-01-26"
    assert module._json_safe_value(None) is None


def test_resolve_column_required_raises_when_missing() -> None:
    module = _load_module()
    with pytest.raises(ValueError):
        module._resolve_column({"a", "b"}, ["c"], "c_field")


def test_resolve_column_optional_returns_none_when_missing() -> None:
    module = _load_module()
    assert module._resolve_column({"a"}, ["missing"], "x", required=False) is None


def test_round_or_none() -> None:
    module = _load_module()
    assert module._round_or_none(None) is None
    assert module._round_or_none(0.123456, 4) == 0.1235
    import math

    assert module._round_or_none(math.nan) is None


def test_season_age_handles_string_birth_date() -> None:
    """Regression test: nflreadpy.load_players() returns birth_date as an ISO string,
    not a datetime.date object. The age calc must parse strings, not silently return None."""
    module = _load_module()
    age = module._season_age("1995-01-26", 2023)
    assert age is not None
    assert 28.0 < age < 29.0


def test_season_age_handles_date_object() -> None:
    module = _load_module()
    age = module._season_age(date(1995, 1, 26), 2023)
    assert age is not None
    assert 28.0 < age < 29.0


def test_season_age_none_for_missing_or_invalid_birth_date() -> None:
    module = _load_module()
    assert module._season_age(None, 2023) is None
    assert module._season_age("not-a-date", 2023) is None
    # future birth date relative to reference: guarded against negative age
    assert module._season_age("2999-01-01", 2023) is None


def test_coverage_status_thresholds() -> None:
    module = _load_module()
    assert module._coverage_status(17) == "full_season"
    assert module._coverage_status(15) == "full_season"
    assert module._coverage_status(14) == "partial_season"
    assert module._coverage_status(2) == "partial_season"
    assert module._coverage_status(1) == "single_week"
    assert module._coverage_status(0) == "unknown"


def test_build_team_context_multi_team_primary_team_rule() -> None:
    module = _load_module()
    week_records = [
        {"_player_id": "p1", "season": 2023, "week": 1, "team": "ARI"},
        {"_player_id": "p1", "season": 2023, "week": 2, "team": "ARI"},
        {"_player_id": "p1", "season": 2023, "week": 3, "team": "MIN"},
    ]
    ctx = module._build_team_context(week_records, "season", "week", "team")
    key = (2023, "p1")
    assert ctx[key]["teams"] == ["ARI", "MIN"]
    assert ctx[key]["primary_team"] == "ARI"
    assert ctx[key]["weeks_observed"] == 3
    assert {tw["team"]: tw["weeks_observed"] for tw in ctx[key]["team_weeks"]} == {"ARI": 2, "MIN": 1}


def test_build_team_context_single_team() -> None:
    module = _load_module()
    week_records = [
        {"_player_id": "p2", "season": 2023, "week": 1, "team": "PHI"},
        {"_player_id": "p2", "season": 2023, "week": 2, "team": "PHI"},
    ]
    ctx = module._build_team_context(week_records, "season", "week", "team")
    key = (2023, "p2")
    assert ctx[key]["teams"] == ["PHI"]
    assert ctx[key]["primary_team"] == "PHI"
    assert ctx[key]["team_unknown"] is False


# --- end-to-end build (mocked nflreadpy, no network) ------------------------


def _week_row(season, week, player_id, team, position="WR", season_type="REG"):
    return {
        "season": season,
        "week": week,
        "player_id": player_id,
        "team": team,
        "season_type": season_type,
        "position": position,
    }


def _reg_row(season, player_id, name, team, position, games, **overrides):
    base = {
        "season": season,
        "player_id": player_id,
        "player_display_name": name,
        "team": team,
        "position": position,
        "games": games,
        "season_type": "REG",
        "completions": 0,
        "attempts": 0,
        "passing_yards": 0,
        "passing_tds": 0,
        "passing_interceptions": 0,
        "carries": 10,
        "rushing_yards": 50,
        "rushing_tds": 1,
        "receptions": 40,
        "targets": 60,
        "receiving_yards": 400,
        "receiving_tds": 3,
        "receiving_air_yards": 500,
        "target_share": 0.2,
        "air_yards_share": 0.25,
        "wopr": 0.5,
        "racr": 0.8,
        "fantasy_points_ppr": 150.0,
    }
    base.update(overrides)
    return base


def test_build_source_backed_payload_end_to_end(monkeypatch) -> None:
    module = _load_module()
    module.SEASONS = [2023]

    week_rows = [
        _week_row(2023, 1, "p1", "ARI"),
        _week_row(2023, 2, "p1", "ARI"),
        _week_row(2023, 3, "p1", "MIN"),  # multi-team
        _week_row(2023, 1, "p2", "PHI"),
    ]
    reg_rows = [
        _reg_row(2023, "p1", "Multi Team Player", "MIN", "WR", games=3),
        _reg_row(2023, "p2", "Single Team Player", "PHI", "RB", games=1),
    ]
    players_rows = [
        {
            "gsis_id": "p1",
            "birth_date": "1998-05-01",
            "draft_year": 2020,
            "draft_round": 3,
            "draft_pick": 80,
            "draft_team": "MIN",
            "rookie_season": 2020,
            "espn_id": "111",
        },
        # p2 deliberately absent from players index -> provisional identity_confidence
    ]

    def _fake_load_player_stats(seasons, summary_level="week"):
        if summary_level == "week":
            return _FakeFrame(week_rows)
        return _FakeFrame(reg_rows)

    monkeypatch.setattr(module.nfl, "load_player_stats", _fake_load_player_stats)
    monkeypatch.setattr(module.nfl, "load_players", lambda: _FakeFrame(players_rows))

    payload = module.build_source_backed_payload()

    assert payload["status"] == "candidate_evidence_artifact_not_promoted"
    assert payload["row_grain"] == "player_id + season + season_type"
    records = payload["records"]
    assert len(records) == 2

    by_id = {r["player_id"]: r for r in records}

    p1 = by_id["p1"]
    assert p1["season_type"] == "REG"
    assert p1["teams"] == ["ARI", "MIN"]
    assert p1["primary_team"] == "ARI"
    assert p1["primary_team_rule"]
    assert p1["weeks_observed"] == 3
    assert p1["identity_confidence"] == "source_verified"
    assert p1["birth_date"] == "1998-05-01"
    assert p1["season_age"] is not None
    assert p1["rookie_year"] == 2020
    assert p1["career_year"] == 2023 - 2020 + 1
    assert p1["draft_year"] == 2020
    # unavailable usage fields must be null, never zero
    assert p1["usage_summary"]["snap_share"] is None
    assert p1["usage_summary"]["routes_run"] is None

    p2 = by_id["p2"]
    assert p2["teams"] == ["PHI"]
    assert p2["primary_team_rule"] is None  # single team: no rule needed
    assert p2["identity_confidence"] == "provisional"
    assert p2["birth_date"] is None
    assert p2["season_age"] is None
    assert p2["career_year"] is None
    assert "birth_date" in p2["missing_fields"]
    assert "career_year" in p2["missing_fields"]

    # no row ever asserts active/inactive availability status
    for r in records:
        assert "active_status" not in r
        assert "ownership_status" not in r
        assert "active_roster_status" not in r


def test_build_source_backed_payload_rejects_non_skill_positions(monkeypatch) -> None:
    module = _load_module()
    module.SEASONS = [2023]

    week_rows = [_week_row(2023, 1, "p9", "DAL", position="DT")]
    reg_rows = [_reg_row(2023, "p9", "Lineman", "DAL", "DT", games=1)]

    monkeypatch.setattr(
        module.nfl,
        "load_player_stats",
        lambda seasons, summary_level="week": _FakeFrame(week_rows if summary_level == "week" else reg_rows),
    )
    monkeypatch.setattr(module.nfl, "load_players", lambda: _FakeFrame([]))

    with pytest.raises(ValueError):
        module.build_source_backed_payload()


def test_build_source_backed_payload_fails_closed_on_duplicate_grain(monkeypatch) -> None:
    module = _load_module()
    module.SEASONS = [2023]

    week_rows = [_week_row(2023, 1, "p1", "ARI")]
    reg_rows = [
        _reg_row(2023, "p1", "Dup A", "ARI", "WR", games=1),
        _reg_row(2023, "p1", "Dup B", "ARI", "WR", games=1),
    ]

    monkeypatch.setattr(
        module.nfl,
        "load_player_stats",
        lambda seasons, summary_level="week": _FakeFrame(week_rows if summary_level == "week" else reg_rows),
    )
    monkeypatch.setattr(module.nfl, "load_players", lambda: _FakeFrame([{"gsis_id": "unrelated-player"}]))

    with pytest.raises(ValueError, match="Duplicate"):
        module.build_source_backed_payload()

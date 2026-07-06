from datetime import date
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pytest


def _load_module():
    module_path = Path(__file__).resolve().parents[1] / "scripts" / "build_player_season_coverage_2021_candidate.py"
    spec = spec_from_file_location("build_player_season_coverage_2021_candidate", module_path)
    assert spec is not None and spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _FakeFrame:
    def __init__(self, rows: list[dict], columns: list[str] | None = None) -> None:
        self.columns = columns if columns is not None else (list(rows[0].keys()) if rows else [])
        self._rows = rows

    def to_dicts(self) -> list[dict]:
        return self._rows


_PLAYERS = [
    ("00-1", "QB"),
    ("00-2", "RB"),
    ("00-3", "WR"),
    ("00-4", "TE"),
]

_REG_STAT_FIELDS = {
    "completions": 0,
    "attempts": 0,
    "passing_yards": 0,
    "passing_tds": 0,
    "passing_interceptions": 0,
    "carries": 0,
    "rushing_yards": 0,
    "rushing_tds": 0,
    "receptions": 0,
    "targets": 0,
    "receiving_yards": 0,
    "receiving_tds": 0,
    "receiving_air_yards": 0,
    "target_share": 0.0,
    "air_yards_share": 0.0,
    "wopr": 0.0,
    "racr": 0.0,
    "fantasy_points_ppr": 0.0,
}


def _week_rows(players: list[tuple[str, str]] = _PLAYERS, weeks: range = range(1, 19)) -> list[dict]:
    rows = []
    for pid, _pos in players:
        for week in weeks:
            rows.append(
                {
                    "season": 2021,
                    "week": week,
                    "player_id": pid,
                    "team": "KC",
                    "season_type": "REG",
                }
            )
    return rows


def _reg_rows(players: list[tuple[str, str]] = _PLAYERS) -> list[dict]:
    return [
        {
            "player_id": pid,
            "player_display_name": f"Player {pid}",
            "position": pos,
            "games": 17,
            "season_type": "REG",
            **_REG_STAT_FIELDS,
        }
        for pid, pos in players
    ]


def _players_rows(players: list[tuple[str, str]] = _PLAYERS) -> list[dict]:
    return [
        {
            "gsis_id": pid,
            "birth_date": "1995-01-01",
            "draft_year": 2017,
            "draft_round": 1,
            "draft_pick": 10,
            "draft_team": "KC",
            "rookie_season": 2017,
            "espn_id": 1,
        }
        for pid, _pos in players
    ]


def _build(module, week_rows=None, reg_rows=None, players_rows=None):
    return module.build_candidate_payload(
        _FakeFrame(week_rows if week_rows is not None else _week_rows()),
        _FakeFrame(reg_rows if reg_rows is not None else _reg_rows()),
        _FakeFrame(players_rows if players_rows is not None else _players_rows()),
    )


def test_happy_path_builds_candidate_with_all_positions() -> None:
    module = _load_module()
    payload = _build(module)
    assert payload["status"] == "candidate_evidence_artifact_not_promoted"
    assert payload["seasons"] == [2021]
    assert payload["season_type_scope"] == ["REG"]
    assert len(payload["records"]) == 4
    assert payload["row_counts_by_position"] == {"QB": 1, "RB": 1, "WR": 1, "TE": 1}
    assert payload["identity_join_rate"] == 1.0
    assert payload["tracking_issue"].startswith("TIBER-Data#200")
    for record in payload["records"]:
        assert record["season"] == 2021
        assert record["season_type"] == "REG"
        assert record["coverage_status"] == "full_season"


def test_missing_required_reg_column_fails_closed() -> None:
    module = _load_module()
    reg_rows = [{k: v for k, v in r.items() if k != "games"} for r in _reg_rows()]
    with pytest.raises(module.SourceFeasibilityError, match="games"):
        _build(module, reg_rows=reg_rows)


def test_missing_required_week_column_fails_closed() -> None:
    module = _load_module()
    week_rows = [{k: v for k, v in r.items() if k != "team"} for r in _week_rows()]
    with pytest.raises(module.SourceFeasibilityError, match="team"):
        _build(module, week_rows=week_rows)


def test_zero_reg_week_level_rows_fails_closed() -> None:
    module = _load_module()
    week_rows = [dict(r, season_type="POST") for r in _week_rows()]
    with pytest.raises(module.SourceFeasibilityError, match="No REG week-level rows"):
        _build(module, week_rows=week_rows)


def test_zero_rows_for_included_positions_fails_closed() -> None:
    module = _load_module()
    reg_rows = [dict(r, position="K") for r in _reg_rows()]
    with pytest.raises(module.SourceFeasibilityError, match="No valid source-backed"):
        _build(module, reg_rows=reg_rows)


def test_missing_one_of_four_positions_fails_closed() -> None:
    module = _load_module()
    players_without_te = [p for p in _PLAYERS if p[1] != "TE"]
    payload_week_rows = _week_rows(players=players_without_te)
    payload_reg_rows = _reg_rows(players=players_without_te)
    payload_players_rows = _players_rows(players=players_without_te)
    with pytest.raises(module.SourceFeasibilityError, match=r"\['TE'\]"):
        _build(
            module,
            week_rows=payload_week_rows,
            reg_rows=payload_reg_rows,
            players_rows=payload_players_rows,
        )


def test_incomplete_week_span_fails_closed() -> None:
    """A league-wide gap (no player recorded a week-5 stat line) must fail closed,
    not silently pass because the season still starts at 1 and ends at 18."""
    module = _load_module()
    week_rows = [row for row in _week_rows() if row["week"] != 5]
    with pytest.raises(module.SourceFeasibilityError, match="not the complete 1-18"):
        _build(module, week_rows=week_rows)


def test_week_span_beyond_18_fails_closed() -> None:
    module = _load_module()
    week_rows = _week_rows() + [{"season": 2021, "week": 19, "player_id": "00-1", "team": "KC", "season_type": "REG"}]
    with pytest.raises(module.SourceFeasibilityError, match="not the complete 1-18"):
        _build(module, week_rows=week_rows)


def test_duplicate_grain_fails_closed() -> None:
    module = _load_module()
    reg_rows = _reg_rows() + [_reg_rows()[0]]
    with pytest.raises(module.SourceFeasibilityError, match="Duplicate player-season-season_type grain"):
        _build(module, reg_rows=reg_rows)


def test_identity_join_rate_below_floor_fails_closed() -> None:
    module = _load_module()
    with pytest.raises(module.SourceFeasibilityError, match="identity join rate"):
        _build(module, players_rows=[_players_rows()[0]])


def test_resolve_column_required_raises() -> None:
    module = _load_module()
    with pytest.raises(module.SourceFeasibilityError):
        module._resolve_column({"a", "b"}, ["c"], "c_field")


def test_resolve_column_optional_returns_none_when_missing() -> None:
    module = _load_module()
    assert module._resolve_column({"a"}, ["missing"], "x", required=False) is None


def test_season_age_computed_against_september_first() -> None:
    module = _load_module()
    assert module._season_age(date(1995, 9, 1), 2021) == 26.0
    assert module._season_age(None, 2021) is None


def test_main_refuses_to_write_under_promoted_path(monkeypatch: pytest.MonkeyPatch) -> None:
    """Defense in depth: the output-path guard must fire before any network call."""
    module = _load_module()
    monkeypatch.setattr(
        module,
        "OUTPUT_PATH",
        module.REPO_ROOT / "exports" / "promoted" / "nfl" / "player_season_coverage_2021_candidate.json",
    )

    def _fail_if_called(*args, **kwargs):
        raise AssertionError("network/source call must not happen once the promoted-path guard fires")

    monkeypatch.setattr(module.nfl, "load_player_stats", _fail_if_called)
    monkeypatch.setattr(module.nfl, "load_players", _fail_if_called)

    with pytest.raises(module.SourceFeasibilityError, match="promoted path"):
        module.main()

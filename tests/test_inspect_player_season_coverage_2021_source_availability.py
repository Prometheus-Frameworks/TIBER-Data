from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


def _load_module():
    module_path = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "inspect_player_season_coverage_2021_source_availability.py"
    )
    spec = spec_from_file_location(
        "inspect_player_season_coverage_2021_source_availability", module_path
    )
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


_PROMOTED_META = {"counts": {"records": 2383, "by_season": {"2022": 609}}, "seasons": [2022, 2023, 2024, 2025]}

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


def _week_rows() -> list[dict]:
    rows = []
    for pid, pos in (("00-1", "QB"), ("00-2", "RB"), ("00-3", "WR"), ("00-4", "TE")):
        for week in range(1, 19):
            rows.append(
                {
                    "season": 2021,
                    "week": week,
                    "player_id": pid,
                    "team": "KC",
                    "season_type": "REG",
                    "position": pos,
                }
            )
    return rows


def _reg_rows() -> list[dict]:
    return [
        {
            "player_id": pid,
            "player_display_name": f"Player {pid}",
            "position": pos,
            "games": 17,
            "season_type": "REG",
            **_REG_STAT_FIELDS,
        }
        for pid, pos in (("00-1", "QB"), ("00-2", "RB"), ("00-3", "WR"), ("00-4", "TE"))
    ]


def _players_rows() -> list[dict]:
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
        for pid in ("00-1", "00-2", "00-3", "00-4")
    ]


def _assess(module, week_rows=None, reg_rows=None, players_rows=None, players_columns=None):
    return module.assess_2021_source_availability(
        _FakeFrame(week_rows if week_rows is not None else _week_rows()),
        _FakeFrame(reg_rows if reg_rows is not None else _reg_rows()),
        _FakeFrame(
            players_rows if players_rows is not None else _players_rows(),
            columns=players_columns,
        ),
        _PROMOTED_META,
    )


def test_fully_compatible_source_emits_candidate_build_decision() -> None:
    module = _load_module()
    payload = _assess(module)
    assert payload["decision"] == "may_open_player_season_coverage_2021_candidate_build_issue"
    assert payload["blocking_failures"] == []
    assert payload["redesign_failures"] == []
    assert payload["availability"]["row_counts_by_position_reg_level"] == {
        "QB": 1,
        "RB": 1,
        "WR": 1,
        "TE": 1,
    }
    assert payload["availability"]["player_counts_by_position"]["QB"] == 1
    assert payload["methodology_compatibility"]["hypothesis_verified"] is True
    assert payload["identity_age_draft"]["identity_join_rate_gsis_id"] == 1.0
    # This report must never carry per-player artifact records.
    assert "records" not in payload
    # Path must be POSIX-style regardless of host OS (repo convention), never backslashes.
    promoted_artifact_path = payload["comparison_to_promoted_2022_2025"]["promoted_artifact"]
    assert promoted_artifact_path == "exports/promoted/nfl/player_season_coverage_v0.json"
    assert "\\" not in promoted_artifact_path


def test_no_2021_rows_emits_source_unavailable_decision() -> None:
    module = _load_module()
    week_cols = ["season", "week", "player_id", "team", "season_type", "position"]
    reg_cols = ["player_id", "player_display_name", "position", "games", "season_type"]
    payload = module.assess_2021_source_availability(
        _FakeFrame([], columns=week_cols),
        _FakeFrame([], columns=reg_cols),
        _FakeFrame(_players_rows()),
        _PROMOTED_META,
    )
    assert (
        payload["decision"]
        == "player_season_coverage_2021_source_unavailable_blocks_additional_validation"
    )
    assert "week_level_2021_rows_exist" in payload["blocking_failures"]


def test_missing_position_emits_source_unavailable_decision() -> None:
    module = _load_module()
    reg_rows = [r for r in _reg_rows() if r["position"] != "TE"]
    payload = _assess(module, reg_rows=reg_rows)
    assert (
        payload["decision"]
        == "player_season_coverage_2021_source_unavailable_blocks_additional_validation"
    )
    assert "all_four_positions_present" in payload["blocking_failures"]


def test_week_span_beyond_18_emits_redesign_decision() -> None:
    module = _load_module()
    week_rows = _week_rows() + [
        {
            "season": 2021,
            "week": 19,
            "player_id": "00-1",
            "team": "KC",
            "season_type": "REG",
            "position": "QB",
        }
    ]
    payload = _assess(module, week_rows=week_rows)
    assert payload["decision"] == "player_season_coverage_2021_requires_source_boundary_redesign"
    assert "reg_week_span_1_to_18" in payload["redesign_failures"]


def test_week_gap_with_endpoints_intact_emits_redesign_decision() -> None:
    """First/last observed weeks are 1 and 18, but week 5 never appears league-wide.

    Regression test for a real gap: endpoint-only checks (first >= 1, last == 18)
    would pass here even though the source is missing a whole week, silently
    overclaiming full 1-18 coverage. The check must compare the full observed set
    against range(1, 19).
    """
    module = _load_module()
    week_rows = [row for row in _week_rows() if row["week"] != 5]
    payload = _assess(module, week_rows=week_rows)
    assert payload["decision"] == "player_season_coverage_2021_requires_source_boundary_redesign"
    assert "reg_week_span_1_to_18" in payload["redesign_failures"]
    assert 5 not in payload["availability"]["reg_week_numbers_observed"]


def test_missing_required_reg_column_emits_redesign_decision() -> None:
    module = _load_module()
    reg_rows = [{k: v for k, v in r.items() if k != "games"} for r in _reg_rows()]
    payload = _assess(module, reg_rows=reg_rows)
    assert payload["decision"] == "player_season_coverage_2021_requires_source_boundary_redesign"
    assert "games" in payload["schema_compatibility"]["missing_required_reg_level"]


def test_low_identity_join_rate_emits_redesign_decision() -> None:
    module = _load_module()
    payload = _assess(module, players_rows=[_players_rows()[0]])
    assert payload["decision"] == "player_season_coverage_2021_requires_source_boundary_redesign"
    assert "identity_join_rate_at_or_above_floor" in payload["redesign_failures"]


def test_decision_always_in_allowed_set_and_never_authorizes_promotion() -> None:
    module = _load_module()
    payload = _assess(module)
    assert payload["decision"] in module.ALLOWED_DECISIONS
    assert "promotion of any artifact" in payload["decisions_not_emitted_and_not_authorized"]


def test_render_markdown_contains_decision_and_no_promotion_claim() -> None:
    module = _load_module()
    payload = _assess(module)
    md = module.render_markdown(payload)
    assert payload["decision"] in md
    assert "not a candidate artifact" in md
    assert "promoted 2022-2025" in md.lower() or "promoted" in md  # comparison section exists

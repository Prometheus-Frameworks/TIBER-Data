"""Offline tests for the TIBER-Data #216 2015-2020 source-availability audit.

All tests run without network or nflreadpy data access: source frames are injected
as fixtures. They pin the audit's fail-closed behavior — per-season isolation,
not_observed vs fail vs pass separation, the terminal-decision enum, and the rule
that committed reports carry aggregates only (no player names, IDs, or rows).
"""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


def _load_module():
    module_path = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "audit_player_season_coverage_2015_2020_source_availability.py"
    )
    spec = spec_from_file_location(
        "audit_player_season_coverage_2015_2020_source_availability", module_path
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


_PROMOTED_MANIFEST = {
    "seasons": [2021, 2022, 2023, 2024, 2025],
    "counts": {"records": 3016, "by_season": {"2021": 633}},
}

_SEASONS = (2015, 2016, 2017, 2018, 2019, 2020)
_PLAYER_IDS = ("00-00fx001", "00-00fx002", "00-00fx003", "00-00fx004")
_POSITIONS = ("QB", "RB", "WR", "TE")

_REG_STAT_FIELDS = {
    "completions": 0,
    "attempts": 0,
    "passing_yards": 0,
    "passing_tds": 0,
    "passing_interceptions": 0,
    "carries": 10,
    "rushing_yards": 0,
    "rushing_tds": 0,
    "receptions": 5,
    "targets": 8,
    "receiving_yards": 0,
    "receiving_tds": 0,
    "receiving_air_yards": 0,
    "target_share": 0.1,
    "air_yards_share": 0.1,
    "wopr": 0.2,
    "racr": 0.9,
    "fantasy_points_ppr": 12.5,
}

_WEEK_COLUMNS = ["season", "week", "player_id", "team", "season_type", "position"]
_REG_COLUMNS = [
    "player_id",
    "player_display_name",
    "position",
    "games",
    "season_type",
    *_REG_STAT_FIELDS.keys(),
]


def _week_rows(season: int, weeks=None) -> list[dict]:
    rows = []
    for pid, pos in zip(_PLAYER_IDS, _POSITIONS, strict=True):
        for week in weeks if weeks is not None else range(1, 18):
            rows.append(
                {
                    "season": season,
                    "week": week,
                    "player_id": pid,
                    "team": "KC",
                    "season_type": "REG",
                    "position": pos,
                }
            )
    return rows


def _reg_rows(season: int, games: int = 16) -> list[dict]:
    return [
        {
            "player_id": pid,
            "player_display_name": f"FIXTURE PLAYER {pid}",
            "position": pos,
            "games": games,
            "season_type": "REG",
            **_REG_STAT_FIELDS,
        }
        for pid, pos in zip(_PLAYER_IDS, _POSITIONS, strict=True)
    ]


def _players_rows() -> list[dict]:
    return [
        {
            "gsis_id": pid,
            "birth_date": "1990-01-01",
            "draft_year": 2012,
            "draft_round": 1,
            "draft_pick": 10,
            "draft_team": "KC",
            "rookie_season": 2012,
        }
        for pid in _PLAYER_IDS
    ]


def _run(module, week_overrides=None, reg_overrides=None, players_rows=None, players_raises=False):
    """Run the audit with fixture loaders. Overrides map season -> frame or Exception."""
    week_overrides = week_overrides or {}
    reg_overrides = reg_overrides or {}

    def load_week(season):
        value = week_overrides.get(season)
        if isinstance(value, Exception):
            raise value
        if value is not None:
            return value
        return _FakeFrame(_week_rows(season), columns=_WEEK_COLUMNS)

    def load_reg(season):
        value = reg_overrides.get(season)
        if isinstance(value, Exception):
            raise value
        if value is not None:
            return value
        return _FakeFrame(_reg_rows(season), columns=_REG_COLUMNS)

    def load_players():
        if players_raises:
            raise ConnectionError("players download blocked")
        return _FakeFrame(players_rows if players_rows is not None else _players_rows())

    return module.run_audit(load_week, load_reg, load_players, _PROMOTED_MANIFEST)


def test_all_seasons_clean_17_week_span_emits_may_open_decision() -> None:
    module = _load_module()
    payload = _run(module)
    assert payload["decision"] == "may_open_player_season_coverage_2015_2020_candidate_build_issue"
    assert payload["summary"]["seasons_fully_cleared"] == list(_SEASONS)
    assert payload["summary"]["seasons_not_observed"] == []
    for r in payload["seasons"]:
        assert r["statuses"]["source_rows_exist"] == "pass"
        assert r["statuses"]["required_columns_present"] == "pass"
        assert r["statuses"]["identity_join_sufficient"] == "pass"
        assert r["statuses"]["schedule_method_observed"] == "pass"
        assert r["statuses"]["existing_schema_compatible"] == "pass"
        assert r["statuses"]["existing_validator_semantics_compatible"] == "pass"
        # A 1-17 span can never be "compatible_as_is" with the 2021+ builder's
        # hard-coded EXPECTED_REG_WEEKS = set(range(1, 19)).
        assert r["statuses"]["builder_compatible"] == "compatible_with_explicit_week_span_parameter"
        assert r["availability"]["min_reg_week"] == 1
        assert r["availability"]["max_reg_week"] == 17
        assert r["availability"]["week_gaps"] == []


def test_narrowest_rule_derived_from_evidence_not_2021_assumption() -> None:
    module = _load_module()
    payload = _run(module)
    rule = payload["schedule_methodology"]["narrowest_supported_rule"]
    assert "set(range(1, 18))" in rule
    assert "range(1, 19)" in payload["schedule_methodology"]["rule_not_reused"]


def test_mixed_week_spans_require_per_season_parameterization() -> None:
    module = _load_module()
    payload = _run(
        module,
        week_overrides={
            2020: _FakeFrame(_week_rows(2020, weeks=range(1, 19)), columns=_WEEK_COLUMNS)
        },
        reg_overrides={2020: _FakeFrame(_reg_rows(2020, games=17), columns=_REG_COLUMNS)},
    )
    rule = payload["schedule_methodology"]["narrowest_supported_rule"]
    assert "DIFFERENT" in rule
    by_season = {r["season"]: r["statuses"]["builder_compatible"] for r in payload["seasons"]}
    assert by_season[2020] == "compatible_as_is"
    assert by_season[2015] == "compatible_with_explicit_week_span_parameter"


def test_single_season_source_error_is_isolated_and_forces_followup() -> None:
    module = _load_module()
    payload = _run(module, week_overrides={2017: ConnectionError("403 blocked")})
    assert payload["decision"] == "player_season_coverage_2015_2020_source_audit_requires_followup"
    by_season = {r["season"]: r for r in payload["seasons"]}
    assert by_season[2017]["statuses"]["source_rows_exist"] == "not_observed"
    assert by_season[2017]["statuses"]["builder_compatible"] == "not_observed"
    assert by_season[2017]["availability"] is None
    error_calls = [c for c in by_season[2017]["source_calls"] if c["status"] == "error"]
    assert error_calls and "403 blocked" in error_calls[0]["error"]
    # Other seasons are still fully inspected — one failure never contaminates the rest.
    assert by_season[2016]["statuses"]["source_rows_exist"] == "pass"
    assert payload["summary"]["seasons_not_observed"] == [2017]
    # A not-observed season is never counted as cleared (no partial-success-as-pass).
    assert 2017 not in payload["summary"]["seasons_fully_cleared"]


def test_all_seasons_blocked_reports_unknown_not_absent() -> None:
    module = _load_module()
    payload = _run(
        module,
        week_overrides={s: ConnectionError("egress blocked") for s in _SEASONS},
        reg_overrides={s: ConnectionError("egress blocked") for s in _SEASONS},
        players_raises=True,
    )
    assert payload["decision"] == "player_season_coverage_2015_2020_source_audit_requires_followup"
    assert payload["summary"]["seasons_fully_cleared"] == []
    assert payload["summary"]["seasons_not_observed"] == list(_SEASONS)
    assert payload["load_players_call"]["status"] == "error"
    for r in payload["seasons"]:
        assert all(v in ("not_observed",) for v in r["statuses"].values())
        assert any("UNKNOWN, not absent" in item for item in r["followup_items"])
    rule = payload["schedule_methodology"]["narrowest_supported_rule"]
    assert "no schedule-span rule can be stated" in rule


def test_missing_required_reg_column_emits_do_not_pursue() -> None:
    module = _load_module()
    reg_cols = [c for c in _REG_COLUMNS if c != "games"]
    bad = _FakeFrame(
        [{k: v for k, v in r.items() if k != "games"} for r in _reg_rows(2016)], columns=reg_cols
    )
    payload = _run(module, reg_overrides={2016: bad})
    assert (
        payload["decision"]
        == "do_not_pursue_player_season_coverage_2015_2020_under_current_source_contract"
    )
    assert 2016 in payload["summary"]["seasons_with_definitive_failures"]
    assert "2016" in payload["decision_basis"]
    by_season = {r["season"]: r for r in payload["seasons"]}
    assert by_season[2016]["statuses"]["required_columns_present"] == "fail"
    assert "games" in by_season[2016]["schema_compatibility"]["missing_required_reg_level"]


def test_missing_position_emits_do_not_pursue() -> None:
    module = _load_module()
    rows = [r for r in _reg_rows(2018) if r["position"] != "TE"]
    payload = _run(module, reg_overrides={2018: _FakeFrame(rows, columns=_REG_COLUMNS)})
    assert (
        payload["decision"]
        == "do_not_pursue_player_season_coverage_2015_2020_under_current_source_contract"
    )
    by_season = {r["season"]: r for r in payload["seasons"]}
    assert by_season[2018]["statuses"]["source_rows_exist"] == "fail"
    assert by_season[2018]["availability"]["row_counts_by_position_reg_level"]["TE"] == 0


def test_week_gap_emits_followup_not_do_not_pursue() -> None:
    module = _load_module()
    rows = [r for r in _week_rows(2019) if r["week"] != 5]
    payload = _run(module, week_overrides={2019: _FakeFrame(rows, columns=_WEEK_COLUMNS)})
    assert payload["decision"] == "player_season_coverage_2015_2020_source_audit_requires_followup"
    by_season = {r["season"]: r for r in payload["seasons"]}
    assert by_season[2019]["statuses"]["schedule_method_observed"] == "fail"
    assert by_season[2019]["availability"]["week_gaps"] == [5]
    assert 5 not in by_season[2019]["availability"]["reg_week_numbers_observed"]


def test_week_beyond_18_emits_followup() -> None:
    module = _load_module()
    rows = _week_rows(2015) + [
        {
            "season": 2015,
            "week": 19,
            "player_id": "00-00fx001",
            "team": "KC",
            "season_type": "REG",
            "position": "QB",
        }
    ]
    payload = _run(module, week_overrides={2015: _FakeFrame(rows, columns=_WEEK_COLUMNS)})
    assert payload["decision"] == "player_season_coverage_2015_2020_source_audit_requires_followup"
    by_season = {r["season"]: r for r in payload["seasons"]}
    assert by_season[2015]["availability"]["unexpected_week_values"] == [19]
    assert by_season[2015]["statuses"]["schedule_method_observed"] == "fail"


def test_low_identity_join_rate_emits_followup() -> None:
    module = _load_module()
    payload = _run(module, players_rows=[_players_rows()[0]])
    assert payload["decision"] == "player_season_coverage_2015_2020_source_audit_requires_followup"
    for r in payload["seasons"]:
        assert r["statuses"]["identity_join_sufficient"] == "fail"
        assert r["identity_age_draft"]["identity_join_rate_gsis_id"] == 0.25


def test_players_load_failure_leaves_identity_not_observed() -> None:
    module = _load_module()
    payload = _run(module, players_raises=True)
    assert payload["decision"] == "player_season_coverage_2015_2020_source_audit_requires_followup"
    assert payload["load_players_call"]["status"] == "error"
    for r in payload["seasons"]:
        assert r["statuses"]["identity_join_sufficient"] == "not_observed"
        # Row evidence is still recorded; only identity stays unknown.
        assert r["statuses"]["source_rows_exist"] == "pass"


def test_duplicate_grain_emits_followup() -> None:
    module = _load_module()
    rows = _reg_rows(2020) + [_reg_rows(2020)[0]]
    payload = _run(module, reg_overrides={2020: _FakeFrame(rows, columns=_REG_COLUMNS)})
    assert payload["decision"] == "player_season_coverage_2015_2020_source_audit_requires_followup"
    by_season = {r["season"]: r for r in payload["seasons"]}
    assert by_season[2020]["availability"]["duplicate_grain_pairs"] == 1
    assert by_season[2020]["statuses"]["existing_schema_compatible"] == "fail"


def test_report_is_aggregate_only_no_player_names_ids_or_rows() -> None:
    import json

    module = _load_module()
    payload = _run(module)
    dump = json.dumps(payload)
    assert "records" not in payload
    assert "FIXTURE PLAYER" not in dump
    for pid in _PLAYER_IDS:
        assert pid not in dump
    md = module.render_markdown(payload)
    assert "FIXTURE PLAYER" not in md
    for pid in _PLAYER_IDS:
        assert pid not in md


def test_report_ordering_is_deterministic_ascending_seasons() -> None:
    module = _load_module()
    payload = _run(module)
    assert [r["season"] for r in payload["seasons"]] == list(_SEASONS)
    assert payload["seasons_inspected"] == list(_SEASONS)


def test_decision_always_in_allowed_enum_and_never_authorizes_build_or_promotion() -> None:
    module = _load_module()
    payload = _run(module)
    assert payload["decision"] in module.ALLOWED_DECISIONS
    assert set(module.ALLOWED_DECISIONS) == {
        "may_open_player_season_coverage_2015_2020_candidate_build_issue",
        "player_season_coverage_2015_2020_source_audit_requires_followup",
        "do_not_pursue_player_season_coverage_2015_2020_under_current_source_contract",
    }
    not_authorized = payload["decisions_not_emitted_and_not_authorized"]
    assert any("promotion" in item for item in not_authorized)
    assert any("candidate build" in item for item in not_authorized)
    assert payload["audit_may_not_establish"] == [
        "candidate_built",
        "promoted",
        "Forecast_ready",
        "2015-2025_available_to_consumers",
    ]


def test_render_markdown_contains_decision_statuses_and_boundaries() -> None:
    module = _load_module()
    payload = _run(module)
    md = module.render_markdown(payload)
    assert payload["decision"] in md
    assert "not** a candidate artifact" in md
    assert "schedule_method_observed" in md
    assert "existing_validator_semantics_compatible" in md
    assert "2015-2025 is available" in md  # quoted only as the prohibited phrase
    assert "prohibited" in md

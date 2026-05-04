from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path


def _load_module():
    module_path = Path(__file__).resolve().parents[1] / "scripts" / "build_goblin_signal_candidates_2025.py"
    spec = spec_from_file_location("build_goblin_signal_candidates_2025", module_path)
    assert spec is not None and spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_wrapper(path: Path, records: list[dict]) -> None:
    path.write_text(json.dumps({"provenance": "fixture", "source_path": "fixture", "records": records}), encoding="utf-8")


def _write_array(path: Path, rows: list[dict]) -> None:
    path.write_text(json.dumps(rows), encoding="utf-8")


def _base_rows():
    identity = [
        {"season": 2025, "week": 1, "player_id": "p1", "player_name": "P1", "team": "AAA", "position": "WR"},
        {"season": 2025, "week": 2, "player_id": "p1", "player_name": "P1", "team": "AAA", "position": "WR"},
        {"season": 2025, "week": 1, "player_id": "p2", "player_name": "P2", "team": "BBB", "position": "RB"},
    ]
    usage = [
        {"season": 2025, "week": 1, "player_id": "p1", "targets": 6, "receptions": 2, "target_share": 0.22, "air_yards": 80, "air_yards_share": -0.1, "rushing_attempts": 0},
        {"season": 2025, "week": 2, "player_id": "p1", "targets": 9, "receptions": 3, "target_share": 0.31, "air_yards": 140, "air_yards_share": 0.2, "rushing_attempts": 1},
        {"season": 2025, "week": 1, "player_id": "p2", "targets": 1, "receptions": 1, "target_share": 0.03, "air_yards": 2, "air_yards_share": 0.01, "rushing_attempts": 12},
    ]
    ppr = [
        {
            "season": 2025,
            "week": 1,
            "player_id": "p1",
            "ppr_points": 7.5,
            "receptions": 2,
            "targets": 6,
            "receiving_yards": 30,
            "receiving_tds": 0,
            "rushing_attempts": 0,
            "rushing_yards": 0,
            "rushing_tds": 0,
            "passing_yards": 0,
            "passing_tds": 0,
            "interceptions": 0,
            "rolling_3_week_ppr": 7.5,
            "rolling_5_week_ppr": 7.5,
            "season_ppr": 7.5,
            "games_played": 1,
        },
        {
            "season": 2025,
            "week": 2,
            "player_id": "p1",
            "ppr_points": 7.0,
            "receptions": 3,
            "targets": 9,
            "receiving_yards": 35,
            "receiving_tds": 0,
            "rushing_attempts": 1,
            "rushing_yards": 2,
            "rushing_tds": 0,
            "passing_yards": 0,
            "passing_tds": 0,
            "interceptions": 0,
            "rolling_3_week_ppr": 7.25,
            "rolling_5_week_ppr": 7.25,
            "season_ppr": 14.5,
            "games_played": 2,
        },
        {
            "season": 2025,
            "week": 1,
            "player_id": "p2",
            "ppr_points": 5.0,
            "receptions": 1,
            "targets": 1,
            "receiving_yards": 5,
            "receiving_tds": 0,
            "rushing_attempts": 12,
            "rushing_yards": 40,
            "rushing_tds": 0,
            "passing_yards": 0,
            "passing_tds": 0,
            "interceptions": 0,
            "rolling_3_week_ppr": 5.0,
            "rolling_5_week_ppr": 5.0,
            "season_ppr": 5.0,
            "games_played": 1,
        },
    ]
    return identity, usage, ppr


def _run(tmp_path: Path, identity: list[dict], usage: list[dict], ppr: list[dict]):
    module = _load_module()
    idp, usp, pprp = tmp_path / "id.json", tmp_path / "usage.json", tmp_path / "ppr.json"
    _write_wrapper(idp, identity)
    _write_wrapper(usp, usage)
    _write_array(pprp, ppr)
    return module.build_goblin_signal_candidates(idp, usp, pprp)


def _run_with_generated_at(tmp_path: Path, identity: list[dict], usage: list[dict], ppr: list[dict], generated_at: str):
    module = _load_module()
    idp, usp, pprp = tmp_path / "id.json", tmp_path / "usage.json", tmp_path / "ppr.json"
    _write_wrapper(idp, identity)
    _write_wrapper(usp, usage)
    _write_array(pprp, ppr)
    return module.build_goblin_signal_candidates(idp, usp, pprp, generated_at=generated_at)


def test_flag_emissions_and_wrapper_fields(tmp_path):
    identity, usage, ppr = _base_rows()
    payload = _run(tmp_path, identity, usage, ppr)
    assert payload["source_type"] == "source_backed_research"
    assert payload["mode"] == "research_candidate_scanner"
    rows = payload["records"]
    by_key = {(r["week"], r["player_id"]): r for r in rows}

    w1 = by_key[(1, "p1")]
    assert "low_ppr_high_targets" in w1["legitimate_indicator_flags"]
    assert "air_yards_without_output" in w1["legitimate_indicator_flags"]
    assert "target_share_without_touchdown" in w1["legitimate_indicator_flags"]
    assert "negative_air_yards_share_context" in w1["legitimate_indicator_flags"]

    w2 = by_key[(2, "p1")]
    assert "usage_spike_without_box_score" in w2["legitimate_indicator_flags"]

    rb = by_key[(1, "p2")]
    assert "carries_without_points" in rb["legitimate_indicator_flags"]

    assert "routes_run" in w1["blocked_or_missing_fields"]
    assert "snap_share" in w1["blocked_or_missing_fields"]
    assert "red_zone_targets" in w1["blocked_or_missing_fields"]
    assert "market_line" in w1["blocked_or_missing_fields"]


def test_high_ppr_not_emitted_and_ppr_only_ignored(tmp_path):
    identity, usage, ppr = _base_rows()
    ppr.append(
        {
            "season": 2025,
            "week": 1,
            "player_id": "p3",
            "ppr_points": 30.0,
            "receptions": 10,
            "targets": 12,
            "receiving_yards": 150,
            "receiving_tds": 2,
            "rushing_attempts": 0,
            "rushing_yards": 0,
            "rushing_tds": 0,
            "passing_yards": 0,
            "passing_tds": 0,
            "interceptions": 0,
            "rolling_3_week_ppr": 30.0,
            "rolling_5_week_ppr": 30.0,
            "season_ppr": 30.0,
            "games_played": 1,
        }
    )
    payload = _run(tmp_path, identity, usage, ppr)
    assert all(r["player_id"] != "p3" for r in payload["records"])


def test_usage_without_ppr_fails_closed(tmp_path):
    module = _load_module()
    identity, usage, ppr = _base_rows()
    usage.append({"season": 2025, "week": 3, "player_id": "p9", "targets": 7, "receptions": 2, "target_share": 0.2, "air_yards": 70, "air_yards_share": 0.1, "rushing_attempts": 0})
    idp, usp, pprp = tmp_path / "id.json", tmp_path / "usage.json", tmp_path / "ppr.json"
    _write_wrapper(idp, identity + [{"season": 2025, "week": 3, "player_id": "p9", "player_name": "P9", "team": "CCC", "position": "WR"}])
    _write_wrapper(usp, usage)
    _write_array(pprp, ppr)
    try:
        module.build_goblin_signal_candidates(idp, usp, pprp)
        assert False
    except Exception as exc:
        assert "Usage rows cannot join to PPR" in str(exc)


def test_missing_identity_fails_closed(tmp_path):
    module = _load_module()
    identity, usage, ppr = _base_rows()
    identity = [row for row in identity if not (row["week"] == 2 and row["player_id"] == "p1")]
    idp, usp, pprp = tmp_path / "id.json", tmp_path / "usage.json", tmp_path / "ppr.json"
    _write_wrapper(idp, identity)
    _write_wrapper(usp, usage)
    _write_array(pprp, ppr)
    try:
        module.build_goblin_signal_candidates(idp, usp, pprp)
        assert False
    except Exception as exc:
        assert "cannot join to identity" in str(exc)


def test_deterministic_output_stable_across_two_calls(tmp_path):
    identity, usage, ppr = _base_rows()
    first = _run_with_generated_at(tmp_path, identity, usage, ppr, "2026-01-01T00:00:00+00:00")
    second = _run_with_generated_at(tmp_path, identity, usage, ppr, "2026-01-01T00:00:00+00:00")
    assert first == second


def test_low_ppr_high_target_share_independent_of_target_count(tmp_path):
    identity = [{"season": 2025, "week": 1, "player_id": "p10", "player_name": "P10", "team": "DDD", "position": "WR"}]
    usage = [{"season": 2025, "week": 1, "player_id": "p10", "targets": 4, "receptions": 2, "target_share": 0.25, "air_yards": 30, "air_yards_share": 0.1, "rushing_attempts": 0}]
    ppr = [{
        "season": 2025, "week": 1, "player_id": "p10", "ppr_points": 7.0, "receptions": 2, "targets": 4, "receiving_yards": 20, "receiving_tds": 0,
        "rushing_attempts": 0, "rushing_yards": 0, "rushing_tds": 0, "passing_yards": 0, "passing_tds": 0, "interceptions": 0,
        "rolling_3_week_ppr": 7.0, "rolling_5_week_ppr": 7.0, "season_ppr": 7.0, "games_played": 1
    }]
    payload = _run(tmp_path, identity, usage, ppr)
    flags = payload["records"][0]["legitimate_indicator_flags"]
    assert "low_ppr_high_target_share" in flags
    assert "low_ppr_high_targets" not in flags


def test_air_yards_without_output_independent_emit(tmp_path):
    identity = [{"season": 2025, "week": 1, "player_id": "p11", "player_name": "P11", "team": "EEE", "position": "WR"}]
    usage = [{"season": 2025, "week": 1, "player_id": "p11", "targets": 2, "receptions": 1, "target_share": 0.09, "air_yards": 75, "air_yards_share": 0.2, "rushing_attempts": 0}]
    ppr = [{
        "season": 2025, "week": 1, "player_id": "p11", "ppr_points": 5.0, "receptions": 1, "targets": 2, "receiving_yards": 10, "receiving_tds": 0,
        "rushing_attempts": 0, "rushing_yards": 0, "rushing_tds": 0, "passing_yards": 0, "passing_tds": 0, "interceptions": 0,
        "rolling_3_week_ppr": 5.0, "rolling_5_week_ppr": 5.0, "season_ppr": 5.0, "games_played": 1
    }]
    payload = _run(tmp_path, identity, usage, ppr)
    flags = payload["records"][0]["legitimate_indicator_flags"]
    assert flags == ["air_yards_without_output"]


def test_target_share_without_touchdown_emits_when_total_tds_zero_and_candidate_score_null(tmp_path):
    identity = [{"season": 2025, "week": 1, "player_id": "p12", "player_name": "P12", "team": "FFF", "position": "TE"}]
    usage = [{"season": 2025, "week": 1, "player_id": "p12", "targets": 5, "receptions": 3, "target_share": 0.21, "air_yards": 20, "air_yards_share": 0.05, "rushing_attempts": 0}]
    ppr = [{
        "season": 2025, "week": 1, "player_id": "p12", "ppr_points": 9.0, "receptions": 3, "targets": 5, "receiving_yards": 25, "receiving_tds": 0,
        "rushing_attempts": 0, "rushing_yards": 0, "rushing_tds": 0, "passing_yards": 0, "passing_tds": 0, "interceptions": 0,
        "rolling_3_week_ppr": 9.0, "rolling_5_week_ppr": 9.0, "season_ppr": 9.0, "games_played": 1
    }]
    payload = _run(tmp_path, identity, usage, ppr)
    row = payload["records"][0]
    assert "target_share_without_touchdown" in row["legitimate_indicator_flags"]
    assert row["candidate_score"] is None

from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path


def _load_module():
    module_path = Path(__file__).resolve().parents[1] / "scripts" / "check_goblin_source_readiness_2025.py"
    spec = spec_from_file_location("check_goblin_source_readiness_2025", module_path)
    assert spec is not None and spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_payload(path: Path, records: list[dict], provenance: str = "test") -> None:
    path.write_text(
        json.dumps({"provenance": provenance, "source_path": "fixture", "records": records}),
        encoding="utf-8",
    )

def _write_array_payload(path: Path, rows: list[dict]) -> None:
    path.write_text(json.dumps(rows), encoding="utf-8")


def _base_rows():
    identity = [{"season": 2025, "week": 1, "player_id": "p1", "player_name": "P1", "team": "A", "position": "WR"}]
    ppr = [
        {
            "season": 2025,
            "week": 1,
            "player_id": "p1",
            "player_name": "P1",
            "team": "A",
            "position": "WR",
            "ppr_points": 1.0,
            "receiving_tds": 0,
            "rushing_tds": 0,
            "passing_tds": 0,
        }
    ]
    usage = [
        {
            "season": 2025,
            "week": 1,
            "player_id": "p1",
            "player_name": "P1",
            "team": "A",
            "position": "WR",
            "targets": 8,
            "receptions": 4,
            "target_share": None,
            "air_yards": 60,
            "air_yards_share": -0.1,
            "rushing_attempts": 0,
            "routes_run": None,
            "route_participation": None,
            "team_rushing_attempts": None,
            "rush_share": None,
            "red_zone_targets": None,
            "red_zone_carries": None,
            "snap_share": None,
        }
    ]
    return identity, ppr, usage


def test_missing_artifact_fails_closed(tmp_path):
    module = _load_module()
    identity, ppr, usage = _base_rows()
    idp, pprp, usp = tmp_path / "id.json", tmp_path / "ppr.json", tmp_path / "usage.json"
    _write_payload(idp, identity)
    _write_payload(pprp, ppr)

    try:
        module.generate_readiness_report(idp, pprp, usp)
        assert False
    except Exception as exc:
        assert "Missing required artifact" in str(exc)


def test_default_ppr_path_points_to_computed_source_backed_artifact():
    module = _load_module()
    assert str(module.PPR_PATH) == "data/processed/evidence/player_weekly_ppr_outcomes_2025.computed_source_backed.json"


def test_invalid_json_fails_closed(tmp_path):
    module = _load_module()
    idp, pprp, usp = tmp_path / "id.json", tmp_path / "ppr.json", tmp_path / "usage.json"
    idp.write_text("{invalid", encoding="utf-8")
    _write_payload(pprp, [])
    _write_payload(usp, [])
    try:
        module.generate_readiness_report(idp, pprp, usp)
        assert False
    except Exception as exc:
        assert "Invalid JSON artifact" in str(exc)


def test_empty_records_fails_closed(tmp_path):
    module = _load_module()
    idp, pprp, usp = tmp_path / "id.json", tmp_path / "ppr.json", tmp_path / "usage.json"
    _write_payload(idp, [])
    _write_payload(pprp, [])
    _write_payload(usp, [])
    try:
        module.generate_readiness_report(idp, pprp, usp)
        assert False
    except Exception as exc:
        assert "records are empty" in str(exc)


def test_computed_ppr_direct_array_succeeds(tmp_path):
    module = _load_module()
    identity, ppr, usage = _base_rows()
    ppr[0]["source"] = "src/ppr_raw.json"
    idp, pprp, usp = tmp_path / "id.json", tmp_path / "ppr.json", tmp_path / "usage.json"
    _write_payload(idp, identity)
    _write_array_payload(pprp, ppr)
    _write_payload(usp, usage)
    report, ok = module.generate_readiness_report(idp, pprp, usp)
    assert ok is True
    assert "Status: READY" in report
    assert "provenance=src/ppr_raw.json" in report


def test_computed_ppr_empty_array_fails_closed(tmp_path):
    module = _load_module()
    identity, _, usage = _base_rows()
    idp, pprp, usp = tmp_path / "id.json", tmp_path / "ppr.json", tmp_path / "usage.json"
    _write_payload(idp, identity)
    _write_array_payload(pprp, [])
    _write_payload(usp, usage)
    try:
        module.generate_readiness_report(idp, pprp, usp)
        assert False
    except Exception as exc:
        assert "records are empty" in str(exc)


def test_computed_ppr_wrapper_still_succeeds(tmp_path):
    module = _load_module()
    identity, ppr, usage = _base_rows()
    idp, pprp, usp = tmp_path / "id.json", tmp_path / "ppr.json", tmp_path / "usage.json"
    _write_payload(idp, identity)
    _write_payload(pprp, ppr, provenance="wrapped")
    _write_payload(usp, usage)
    report, ok = module.generate_readiness_report(idp, pprp, usp)
    assert ok is True
    assert "provenance=wrapped" in report


def test_identity_usage_still_require_wrapper_fields(tmp_path):
    module = _load_module()
    _, ppr, _ = _base_rows()
    idp, pprp, usp = tmp_path / "id.json", tmp_path / "ppr.json", tmp_path / "usage.json"
    idp.write_text(json.dumps([{"season": 2025, "week": 1, "player_id": "p1"}]), encoding="utf-8")
    _write_payload(pprp, ppr)
    usp.write_text(json.dumps([{"season": 2025, "week": 1, "player_id": "p1"}]), encoding="utf-8")
    try:
        module.generate_readiness_report(idp, pprp, usp)
        assert False
    except Exception as exc:
        assert "payload must be an object" in str(exc)


def test_duplicate_keys_fail_closed(tmp_path):
    module = _load_module()
    identity, ppr, usage = _base_rows()
    ppr.append(dict(ppr[0]))
    idp, pprp, usp = tmp_path / "id.json", tmp_path / "ppr.json", tmp_path / "usage.json"
    _write_payload(idp, identity)
    _write_payload(pprp, ppr)
    _write_payload(usp, usage)
    try:
        module.generate_readiness_report(idp, pprp, usp)
        assert False
    except Exception as exc:
        assert "duplicate key rows" in str(exc)


def test_duplicate_usage_keys_fail_closed(tmp_path):
    module = _load_module()
    identity, ppr, usage = _base_rows()
    usage.append(dict(usage[0]))
    idp, pprp, usp = tmp_path / "id.json", tmp_path / "ppr.json", tmp_path / "usage.json"
    _write_payload(idp, identity)
    _write_payload(pprp, ppr)
    _write_payload(usp, usage)
    try:
        module.generate_readiness_report(idp, pprp, usp)
        assert False
    except Exception as exc:
        assert "Usage duplicate key rows detected" in str(exc)


def test_join_succeeds_when_keys_match_and_reports_fields(tmp_path):
    module = _load_module()
    identity, ppr, usage = _base_rows()
    idp, pprp, usp = tmp_path / "id.json", tmp_path / "ppr.json", tmp_path / "usage.json"
    _write_payload(idp, identity)
    _write_payload(pprp, ppr)
    _write_payload(usp, usage)
    report, ok = module.generate_readiness_report(idp, pprp, usp)
    assert ok is True
    assert "Status: READY" in report
    assert "ppr_usage_join_coverage: 1/1 ppr, 1/1 usage" in report
    assert "negative air_yards_share count: 1" in report
    assert "routes_run null count: 1" in report
    assert "low_ppr_high_targets: ready" in report
    assert "high_route_participation_low_output: blocked" in report


def test_missing_required_field_fails_closed(tmp_path):
    module = _load_module()
    identity, ppr, usage = _base_rows()
    del usage[0]["targets"]
    idp, pprp, usp = tmp_path / "id.json", tmp_path / "ppr.json", tmp_path / "usage.json"
    _write_payload(idp, identity)
    _write_payload(pprp, ppr)
    _write_payload(usp, usage)
    try:
        module.generate_readiness_report(idp, pprp, usp)
        assert False
    except Exception as exc:
        assert "Usage rows missing required fields" in str(exc)

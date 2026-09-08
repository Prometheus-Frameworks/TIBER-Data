"""Offline checks for the bounded proposal, never an admission/activation gate."""
import csv
import io
import json
from copy import deepcopy
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pytest


def load_module(name, path):
    spec = spec_from_file_location(name, path)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ROOT = Path(__file__).resolve().parents[1]
audit = load_module("admission_audit", ROOT / "scripts/audit_draft_review_evidence_admission.py")


def identity_inputs():
    return [json.loads((ROOT / p).read_bytes()) for p in [audit.CANDIDATES, audit.CROSSWALK, audit.COVERAGE]] + [
        list(csv.DictReader(io.StringIO((ROOT / audit.CONFLICTS).read_text())))]


def test_pinned_replay_matches_and_never_grants_admission():
    report = audit.build_report()
    assert audit.render_report(report) == (ROOT / audit.REPORT).read_text()
    assert report["status"] == "proposed_inactive"
    assert report["consumer_allowed"] is False
    assert report["operator_admission_decision"] is None
    assert report["identity"]["resulting_count_if_later_promoted"] == 72
    assert len(report["historical_validation"]["regular_season_position_conflicts"]) == 9


def test_four_proposals_fit_existing_v2_without_mutating_promoted_rows():
    args = identity_inputs()
    original = deepcopy(args[1])
    proposed = audit.inspect_identities(*args)
    promoter = load_module("identity_promoter", ROOT / "scripts/promote_identity_crosswalk_rows.py")
    candidate_by_id = {r["sleeper_id"]: r for r in args[0]["rows"]}
    for row in proposed:
        assert row == promoter.build_record(candidate_by_id[row["provider_player_id"]], row["source_updated_at"])
    virtual = deepcopy(original)
    virtual["records"] += proposed
    virtual["record_count"] += 4
    virtual["record_count_by_match_method"]["name_exact"] += 4
    promoter.validate_artifact(virtual)
    assert args[1] == original


@pytest.mark.parametrize("mutation", ["duplicate_candidate", "reverse_collision", "promoted_collision", "review_conflict", "canonical_conflict"])
def test_conflicting_or_ambiguous_identity_fails(mutation):
    args = identity_inputs()
    row = next(r for r in args[0]["rows"] if r["sleeper_id"] == "7526")
    if mutation == "duplicate_candidate":
        args[0]["rows"].append(deepcopy(row))
    elif mutation == "reverse_collision":
        other = deepcopy(row)
        other["sleeper_id"] = "synthetic-other"
        args[0]["rows"].append(other)
    elif mutation == "promoted_collision":
        args[1]["records"].append({"provider_player_id": "7526", "tiber_player_id": "00-0000001"})
    elif mutation == "review_conflict":
        args[3].append({"player_id": row["tiber_player_id"]})
    else:
        next(r for r in args[2]["records"] if r["player_id"] == row["tiber_player_id"] and r["season"] == 2025)["position"] = "QB"
    with pytest.raises(ValueError):
        audit.inspect_identities(*args)


def test_source_byte_drift_rejected(tmp_path):
    p = tmp_path / audit.CANDIDATES
    p.parent.mkdir(parents=True)
    p.write_text((ROOT / audit.CANDIDATES).read_text() + " ")
    with pytest.raises(ValueError, match="source hash drift"):
        audit.read_pinned(tmp_path, audit.CANDIDATES)


def weekly_fixture():
    u = {"season": 2025, "week": 1, "player_id": "00-0000001", "team": "X", "opponent": "Y", "position": "WR",
         "targets": 0, "receptions": 0, "rushing_attempts": 0, "target_share": None, "air_yards_share": -0.1,
         **dict.fromkeys(audit.UNSUPPORTED)}
    return ({"provenance": "nflreadpy.load_player_stats", "records": [u]},
            {"provenance": "nflreadpy.load_player_stats", "records": [deepcopy(u)]})


def test_supported_zero_does_not_equal_null():
    u, o = weekly_fixture()
    audit.inspect_weekly(u, o)
    o["records"][0]["targets"] = None
    with pytest.raises(ValueError, match="cross-source disagreement"):
        audit.inspect_weekly(u, o)


def test_negative_and_above_one_air_share_are_preserved():
    for value in [-0.548, 1.316]:
        u, o = weekly_fixture()
        u["records"][0]["air_yards_share"] = value
        audit.inspect_weekly(u, o)
        assert u["records"][0]["air_yards_share"] == value


def test_missing_usage_and_conflicting_positions_are_reported_not_filled():
    u, o = weekly_fixture()
    o["records"][0]["position"] = "RB"
    extra = deepcopy(o["records"][0])
    extra["week"] = 2
    o["records"].append(extra)
    report = audit.inspect_weekly(u, o)
    assert report["usage_rows"] == 1 and report["outcome_rows"] == 2
    assert report["regular_season_position_conflicts"][0]["outcome_position"] == "RB"
    assert len(u["records"]) == 1


def test_duplicate_weekly_keys_fail_closed():
    u, o = weekly_fixture()
    u["records"].append(deepcopy(u["records"][0]))
    with pytest.raises(ValueError, match="duplicate weekly key"):
        audit.inspect_weekly(u, o)

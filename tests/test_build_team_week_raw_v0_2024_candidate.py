from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pytest


def _load_module():
    module_path = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "build_team_week_raw_v0_2024_candidate.py"
    )
    spec = spec_from_file_location("build_team_week_raw_v0_2024_candidate", module_path)
    assert spec is not None and spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def mod():
    return _load_module()


# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------


def test_canon_team_maps_la_to_lar(mod):
    assert mod.canon_team("LA") == "LAR"


def test_canon_team_passes_through_other_codes(mod):
    assert mod.canon_team("KC") == "KC"


def test_canon_team_passes_through_none(mod):
    assert mod.canon_team(None) is None


def test_is_offensive_play_includes_kneel_and_spike(mod):
    assert mod.is_offensive_play({"play_type": "qb_kneel", "two_point_attempt": False})
    assert mod.is_offensive_play({"play_type": "qb_spike", "two_point_attempt": False})


def test_is_offensive_play_excludes_two_point_attempt(mod):
    assert not mod.is_offensive_play({"play_type": "run", "two_point_attempt": True})


def test_is_offensive_play_excludes_punt(mod):
    assert not mod.is_offensive_play({"play_type": "punt", "two_point_attempt": False})


def test_is_competitive_play_excludes_kneel_and_spike(mod):
    assert not mod.is_competitive_play({"play_type": "qb_kneel", "two_point_attempt": False})


def test_is_competitive_play_excludes_two_point_attempt(mod):
    assert not mod.is_competitive_play({"play_type": "pass", "two_point_attempt": True})


def test_is_competitive_play_includes_pass_and_run(mod):
    assert mod.is_competitive_play({"play_type": "pass", "two_point_attempt": False})
    assert mod.is_competitive_play({"play_type": "run", "two_point_attempt": False})


def test_is_neutral_script_true_within_margin_in_first_quarter(mod):
    assert mod.is_neutral_script(
        {"score_differential": 3, "game_half": "Half1", "qtr": 1, "quarter_seconds_remaining": 500}
    )


def test_is_neutral_script_false_outside_margin(mod):
    assert not mod.is_neutral_script(
        {"score_differential": 9, "game_half": "Half1", "qtr": 1, "quarter_seconds_remaining": 500}
    )


def test_is_neutral_script_false_in_overtime(mod):
    assert not mod.is_neutral_script(
        {
            "score_differential": 0,
            "game_half": "Overtime",
            "qtr": 5,
            "quarter_seconds_remaining": 500,
        }
    )


def test_is_neutral_script_false_in_q4_garbage_time(mod):
    assert not mod.is_neutral_script(
        {"score_differential": 0, "game_half": "Half2", "qtr": 4, "quarter_seconds_remaining": 200}
    )


def test_is_neutral_script_true_in_q4_within_min_seconds_window(mod):
    assert mod.is_neutral_script(
        {"score_differential": 0, "game_half": "Half2", "qtr": 4, "quarter_seconds_remaining": 600}
    )


def test_is_neutral_script_false_when_score_differential_missing(mod):
    assert not mod.is_neutral_script({"score_differential": None, "qtr": 1})


def test_is_explosive_pass_requires_completion_and_threshold(mod):
    assert mod.is_explosive_pass(
        {"pass_attempt": True, "complete_pass": True, "yards_gained": 15}
    )
    assert not mod.is_explosive_pass(
        {"pass_attempt": True, "complete_pass": True, "yards_gained": 14}
    )
    assert not mod.is_explosive_pass(
        {"pass_attempt": True, "complete_pass": False, "yards_gained": 40}
    )


def test_is_explosive_rush_threshold(mod):
    assert mod.is_explosive_rush({"rush_attempt": True, "yards_gained": 10})
    assert not mod.is_explosive_rush({"rush_attempt": True, "yards_gained": 9})


def test_safe_ratio_zero_denominator_is_none(mod):
    assert mod.safe_ratio(5, 0) is None


def test_safe_ratio_normal_division(mod):
    assert mod.safe_ratio(1, 4) == 0.25


def test_round_handles_none(mod):
    assert mod._round(None) is None


def test_round_rounds_to_requested_precision(mod):
    assert mod._round(1.0 / 3, digits=4) == 0.3333


def test_nflverse_data_url_appends_parquet_suffix(mod):
    url = mod._nflverse_data_url("pbp/play_by_play_2024")
    assert url.endswith("pbp/play_by_play_2024.parquet")
    assert url.startswith("https://")


def test_to_contract_input_source_includes_source_type_and_notes(mod):
    source_info = {
        "sourceUrlOrDatasetId": "https://example.invalid/pbp.parquet",
        "retrievalTimestamp": "2024-01-01T00:00:00+00:00",
        "sourceName": "nflverse play-by-play",
        "retrievalMethod": "nflreadpy.load_pbp([2024])",
        "packageVersion": "0.1.5",
    }
    contract_source = mod._to_contract_input_source(source_info)
    assert contract_source["source"] == source_info["sourceUrlOrDatasetId"]
    assert contract_source["sourceType"] == "nflverse"
    assert "nflreadpy 0.1.5" in contract_source["notes"]


# ---------------------------------------------------------------------------
# aggregate_game
# ---------------------------------------------------------------------------


def test_aggregate_game_excludes_two_point_attempts_from_offense_and_drives(mod):
    plays = [
        {
            "posteam": "KC", "play_type": "pass", "two_point_attempt": True,
            "fixed_drive": 1, "yardline_100": 2, "qtr": 2, "quarter_seconds_remaining": 500,
            "qb_dropback": True, "epa": 2.0, "success": True,
        },
    ]
    stats = mod.aggregate_game(plays)
    assert stats["KC"].offensive_plays == 0
    assert stats["KC"].competitive_plays == 0
    assert stats["KC"].drive_ids == set()


def test_aggregate_game_canonicalizes_la_team_code(mod):
    plays = [
        {
            "posteam": "LA", "play_type": "run", "two_point_attempt": False,
            "fixed_drive": 1, "yardline_100": 50, "qtr": 1, "quarter_seconds_remaining": 800,
            "qb_dropback": False, "epa": 0.5, "success": True, "rush_attempt": True,
            "yards_gained": 4,
        },
    ]
    stats = mod.aggregate_game(plays)
    assert "LAR" in stats
    assert "LA" not in stats


def test_aggregate_game_red_zone_td_intersection(mod):
    plays = [
        {
            "posteam": "KC", "play_type": "run", "two_point_attempt": False, "fixed_drive": 1,
            "yardline_100": 5, "qtr": 1, "quarter_seconds_remaining": 700,
            "qb_dropback": False, "rush_attempt": True, "yards_gained": 5, "rush_touchdown": True,
        },
        {
            "posteam": "KC", "play_type": "pass", "two_point_attempt": False, "fixed_drive": 2,
            "yardline_100": 75, "qtr": 1, "quarter_seconds_remaining": 600,
            "qb_dropback": True, "pass_attempt": True, "complete_pass": True,
            "yards_gained": 75, "pass_touchdown": True,
        },
    ]
    stats = mod.aggregate_game(plays)
    kc = stats["KC"]
    assert kc.drive_ids == {1, 2}
    assert kc.red_zone_trip_drive_ids == {1}
    assert kc.offensive_td_drive_ids == {1, 2}
    assert kc.red_zone_trip_drive_ids & kc.offensive_td_drive_ids == {1}


def test_aggregate_game_pace_valid_and_anomalous_intervals(mod):
    plays = [
        {
            "posteam": "KC", "play_type": "run", "two_point_attempt": False, "fixed_drive": 1,
            "qtr": 1, "quarter_seconds_remaining": 700, "rush_attempt": True, "yards_gained": 4,
            "qb_dropback": False,
        },
        {
            "posteam": "KC", "play_type": "pass", "two_point_attempt": False, "fixed_drive": 1,
            "qtr": 1, "quarter_seconds_remaining": 660, "qb_dropback": True,
            "pass_attempt": True, "complete_pass": True, "yards_gained": 6,
        },
        {
            "posteam": "KC", "play_type": "pass", "two_point_attempt": False, "fixed_drive": 1,
            "qtr": 1, "quarter_seconds_remaining": 660, "qb_dropback": True,
            "pass_attempt": True, "complete_pass": False, "yards_gained": 0,
        },
    ]
    stats = mod.aggregate_game(plays)
    kc = stats["KC"]
    assert kc.pace_valid_intervals == 1
    assert kc.pace_elapsed_seconds == 40
    assert kc.pace_anomalous_intervals == 1


def test_aggregate_game_null_dropback_increments_block_counter(mod):
    plays = [
        {
            "posteam": "KC", "play_type": "pass", "two_point_attempt": False, "fixed_drive": 1,
            "qtr": 1, "quarter_seconds_remaining": 700, "qb_dropback": None,
            "pass_attempt": True, "complete_pass": True, "yards_gained": 5, "epa": 0.3,
        },
    ]
    stats = mod.aggregate_game(plays)
    kc = stats["KC"]
    assert kc.competitive_plays == 1
    assert kc.dropback_null_rows == 1
    assert kc.pass_plays == 0
    assert kc.rush_plays == 0
    assert kc.epa_values == [0.3]
    assert kc.pass_epa_values == []


def test_aggregate_game_tracks_excluded_possession_plays(mod):
    plays = [{"posteam": "KC", "play_type": "punt", "two_point_attempt": False}]
    stats = mod.aggregate_game(plays)
    assert stats["KC"].excluded_possession_plays == 1
    assert stats["KC"].offensive_plays == 0


# ---------------------------------------------------------------------------
# build_team_week_row
# ---------------------------------------------------------------------------


def test_build_team_week_row_dropback_block_nulls_pass_and_rush_fields(mod):
    stats = mod.TeamGameStats()
    stats.competitive_plays = 10
    stats.dropback_null_rows = 1
    stats.pass_plays = 4
    stats.rush_plays = 5
    stats.pass_epa_values = [0.1, 0.2]
    stats.rush_epa_values = [-0.1]
    row, diag = mod.build_team_week_row(
        season=2024, week=1, team="KC", opponent="LAR", game_id="2024_01_KC_LAR",
        points_for=20, points_against=10, stats=stats,
    )
    assert row["passRate"] is None
    assert row["rushRate"] is None
    assert row["passEpaPerPlay"] is None
    assert row["rushEpaPerPlay"] is None
    assert diag["dropbackSplitBlocked"] is True


def test_build_team_week_row_pace_block_when_no_valid_intervals(mod):
    stats = mod.TeamGameStats()
    stats.competitive_plays = 5
    stats.pace_valid_intervals = 0
    row, diag = mod.build_team_week_row(
        season=2024, week=1, team="KC", opponent="LAR", game_id="2024_01_KC_LAR",
        points_for=20, points_against=10, stats=stats,
    )
    assert row["secondsPerPlay"] is None
    assert diag["paceBlocked"] is True


def test_build_team_week_row_zero_denominator_fields_are_null(mod):
    stats = mod.TeamGameStats()
    row, diag = mod.build_team_week_row(
        season=2024, week=1, team="KC", opponent="LAR", game_id="2024_01_KC_LAR",
        points_for=0, points_against=0, stats=stats,
    )
    assert row["neutralPassRate"] is None
    assert row["redZoneTdRate"] is None
    assert row["pointsPerDrive"] is None
    assert row["passRate"] is None
    assert diag["neutralPlaysDenominatorZero"] is True
    assert diag["redZoneTripsDenominatorZero"] is True


# ---------------------------------------------------------------------------
# build_coverage
# ---------------------------------------------------------------------------


def test_build_coverage_detects_missing_and_unexpected_teams(mod):
    rows = [{"teamCode": "KC", "week": 1}, {"teamCode": "ZZZ", "week": 1}]
    coverage = mod.build_coverage(2024, rows, scheduled_game_count=1)
    assert "ZZZ" in coverage["unexpectedTeams"]
    assert "ARI" in coverage["missingTeams"]
    assert coverage["isFullLeague"] is False
    assert coverage["expectedTeamGameRows"] == 2
    assert coverage["actualTeamGameRows"] == 2


# ---------------------------------------------------------------------------
# build_lineage_manifest
# ---------------------------------------------------------------------------


def test_build_lineage_manifest_includes_non_governed_status(mod):
    manifest = mod.build_lineage_manifest([{"sourceName": "x"}])
    assert manifest["governanceStatus"] == "ungoverned"
    assert manifest["governanceSource"] == "not_set"
    assert manifest["sources"] == [{"sourceName": "x"}]


# ---------------------------------------------------------------------------
# build_validation_report -- synthetic full-coverage fixture
# ---------------------------------------------------------------------------

GOOD_RETRIEVAL_SOURCE = {
    "sourceName": "nflverse play-by-play",
    "sourceType": "nflverse",
    "retrievalMethod": "nflreadpy.load_pbp([2024])",
    "retrievalTimestamp": "2024-01-01T00:00:00+00:00",
    "packageVersion": "0.1.5",
    "sourceUrlOrDatasetId": "https://example.invalid/pbp_2024.parquet",
    "transformCodePath": "scripts/build_team_week_raw_v0_2024_candidate.py",
    "sourceRefs": ["nflverse-data:pbp/play_by_play_2024"],
    "checksum": {"algorithm": "sha256", "value": "a" * 64},
}


def _good_row(team, opponent, season=2024, week=1):
    return {
        "season": season, "week": week, "teamCode": team, "opponentCode": opponent,
        "gameId": f"{season}_{week:02d}_{team}_{opponent}", "isByeWeek": False,
        "pointsFor": 20, "pointsAgainst": 17,
        "offensivePlays": 60, "neutralPlays": 30,
        "secondsPerPlay": 25.0, "passRate": 0.55, "neutralPassRate": 0.5, "rushRate": 0.45,
        "epaPerPlay": 0.05, "passEpaPerPlay": 0.1, "rushEpaPerPlay": -0.02,
        "successRate": 0.45, "explosivePlayRate": 0.1,
        "drives": 10, "pointsPerDrive": 2.0,
        "redZoneTrips": 3, "redZoneTdRate": 0.5,
        "sacksAllowed": 2, "pressureRateAllowed": None, "turnovers": 1,
        "fantasyPointsForQB": None, "fantasyPointsForRB": None, "fantasyPointsForWR": None,
        "fantasyPointsForTE": None, "fantasyPointsAllowedQB": None, "fantasyPointsAllowedRB": None,
        "fantasyPointsAllowedWR": None, "fantasyPointsAllowedTE": None,
    }


def _good_diag(team, season=2024, week=1):
    return {
        "season": season, "week": week, "teamCode": team,
        "competitivePlays": 60, "neutralPlaysDenominatorZero": False,
        "redZoneTripsDenominatorZero": False, "paceBlocked": False,
        "paceAnomalousIntervals": 0, "dropbackSplitBlocked": False,
        "dropbackNullRows": 0, "excludedPossessionPlays": 5,
    }


def _good_fixture(mod):
    teams = sorted(mod.CANONICAL_TEAMS)
    pairs = [(teams[i], teams[i + 1]) for i in range(0, len(teams), 2)]
    rows = []
    diagnostics = []
    for home, away in pairs:
        rows.append(_good_row(home, away))
        rows.append(_good_row(away, home))
        diagnostics.append(_good_diag(home))
        diagnostics.append(_good_diag(away))

    coverage = mod.build_coverage(2024, rows, scheduled_game_count=len(pairs))
    metadata = {
        "provenanceStatus": "partial_real_data",
        "provenanceNotes": ["synthetic test fixture"],
        "inputSources": [],
        "coverage": coverage,
        "governance": {
            "governanceStatus": "ungoverned",
            "governanceSource": "not_set",
            "notes": "synthetic test fixture",
        },
        "deferredFields": ["pressureRateAllowed"],
        "deferredFieldReasons": {"pressureRateAllowed": "test"},
        "fieldReadiness": {
            "pressureRateAllowed": "deferred",
            "neutralPassRate": "available",
            "redZoneTdRate": "available",
            "secondsPerPlay": "available",
        },
        "blockedFieldRows": {
            "secondsPerPlay": [],
            "dropbackSplit(passRate/rushRate/passEpaPerPlay/rushEpaPerPlay)": [],
        },
        "buildDiagnostics": {},
        "validationReportPath": str(mod.CANDIDATE_VALIDATION_REPORT_PATH),
        "lineageManifestPath": str(mod.LINEAGE_MANIFEST_PATH),
    }
    artifact = {
        "artifact": "team_week_raw_v0",
        "generatedAt": "2024-01-01T00:00:00+00:00",
        "season": 2024,
        "sourceArtifacts": ["nflverse-data:pbp/play_by_play_2024", "nflverse-data:schedules/games"],
        "metadata": metadata,
        "rows": rows,
    }
    lineage_manifest = {
        "artifact": "team_week_raw_v0_2024_real_source_candidate",
        "season": 2024,
        "generatedAt": "2024-01-01T00:00:00+00:00",
        "sources": [dict(GOOD_RETRIEVAL_SOURCE), dict(GOOD_RETRIEVAL_SOURCE)],
        "validationReportPath": str(mod.CANDIDATE_VALIDATION_REPORT_PATH),
        "lineageManifestPath": str(mod.LINEAGE_MANIFEST_PATH),
        "governanceStatus": "ungoverned",
        "governanceSource": "not_set",
        "notes": [],
    }
    return artifact, diagnostics, lineage_manifest


def _check(report, name):
    return next(c for c in report["checks"] if c["name"] == name)


def test_validation_report_passes_for_well_formed_artifact(mod):
    artifact, diagnostics, lineage_manifest = _good_fixture(mod)
    report = mod.build_validation_report(artifact, diagnostics, lineage_manifest)
    failed = [c["name"] for c in report["checks"] if not c["passed"]]
    assert failed == []
    assert report["allPassed"] is True
    assert report["rowCount"] == 32
    assert report["teamCount"] == 32


def test_validation_report_fails_when_team_missing(mod):
    artifact, diagnostics, lineage_manifest = _good_fixture(mod)
    artifact["rows"] = [row for row in artifact["rows"] if row["teamCode"] != "ARI"]
    artifact["metadata"]["coverage"] = mod.build_coverage(
        2024, artifact["rows"], scheduled_game_count=16
    )
    report = mod.build_validation_report(artifact, diagnostics, lineage_manifest)
    assert _check(report, "all_32_teams_present")["passed"] is False
    assert report["allPassed"] is False


def test_validation_report_fails_when_team_game_row_count_short_of_schedule(mod):
    artifact, diagnostics, lineage_manifest = _good_fixture(mod)
    artifact["metadata"]["coverage"] = mod.build_coverage(
        2024, artifact["rows"], scheduled_game_count=17
    )
    report = mod.build_validation_report(artifact, diagnostics, lineage_manifest)
    # The new check catches the schedule shortfall even though all 32 teams are
    # still present, weeks are in-window, and there are no duplicates.
    assert _check(report, "expected_team_game_row_count")["passed"] is False
    assert _check(report, "all_32_teams_present")["passed"] is True
    assert _check(report, "expected_weeks_present_per_team")["passed"] is True
    assert _check(report, "no_duplicate_team_week_rows")["passed"] is True
    assert report["allPassed"] is False


def test_validation_report_fails_when_a_team_game_row_is_dropped(mod):
    artifact, diagnostics, lineage_manifest = _good_fixture(mod)
    # Drop one scheduled team-game row while keeping the recorded schedule count.
    artifact["rows"] = artifact["rows"][:-1]
    artifact["metadata"]["coverage"] = mod.build_coverage(
        2024, artifact["rows"], scheduled_game_count=16
    )
    report = mod.build_validation_report(artifact, diagnostics, lineage_manifest)
    check = _check(report, "expected_team_game_row_count")
    assert check["passed"] is False
    assert check["details"]["expectedTeamGameRows"] == 32
    assert check["details"]["actualTeamGameRows"] == 31
    assert check["details"]["rowCount"] == 31
    assert report["allPassed"] is False


def test_validation_report_fails_on_duplicate_rows(mod):
    artifact, diagnostics, lineage_manifest = _good_fixture(mod)
    artifact["rows"].append(dict(artifact["rows"][0]))
    diagnostics.append(dict(diagnostics[0]))
    report = mod.build_validation_report(artifact, diagnostics, lineage_manifest)
    assert _check(report, "no_duplicate_team_week_rows")["passed"] is False


def test_validation_report_fails_on_invalid_team_code(mod):
    artifact, diagnostics, lineage_manifest = _good_fixture(mod)
    artifact["rows"][0]["teamCode"] = "ZZZ"
    report = mod.build_validation_report(artifact, diagnostics, lineage_manifest)
    assert _check(report, "valid_team_and_opponent_codes")["passed"] is False


def test_validation_report_fails_on_bad_reciprocal(mod):
    artifact, diagnostics, lineage_manifest = _good_fixture(mod)
    current = artifact["rows"][0]["opponentCode"]
    artifact["rows"][0]["opponentCode"] = "DAL" if current != "DAL" else "ATL"
    report = mod.build_validation_report(artifact, diagnostics, lineage_manifest)
    assert _check(report, "reciprocal_opponent_consistency")["passed"] is False


def test_validation_report_fails_on_out_of_bounds_rate(mod):
    artifact, diagnostics, lineage_manifest = _good_fixture(mod)
    artifact["rows"][0]["passRate"] = 1.5
    report = mod.build_validation_report(artifact, diagnostics, lineage_manifest)
    assert _check(report, "rate_fields_bounded_0_1_or_null")["passed"] is False


def test_validation_report_fails_on_unexplained_null(mod):
    artifact, diagnostics, lineage_manifest = _good_fixture(mod)
    artifact["rows"][0]["successRate"] = None
    report = mod.build_validation_report(artifact, diagnostics, lineage_manifest)
    assert _check(report, "required_finite_numeric_fields")["passed"] is False


def test_validation_report_fails_when_pressure_rate_allowed_is_not_null(mod):
    artifact, diagnostics, lineage_manifest = _good_fixture(mod)
    artifact["rows"][0]["pressureRateAllowed"] = 0.3
    report = mod.build_validation_report(artifact, diagnostics, lineage_manifest)
    assert _check(report, "pressure_rate_allowed_null_and_deferred")["passed"] is False


def test_validation_report_fails_on_seconds_per_play_block_metadata_mismatch(mod):
    artifact, diagnostics, lineage_manifest = _good_fixture(mod)
    diagnostics[0]["paceBlocked"] = True
    report = mod.build_validation_report(artifact, diagnostics, lineage_manifest)
    assert _check(report, "seconds_per_play_block_metadata_if_applicable")["passed"] is False


def test_validation_report_fails_on_epa_split_block_metadata_mismatch(mod):
    artifact, diagnostics, lineage_manifest = _good_fixture(mod)
    diagnostics[0]["dropbackSplitBlocked"] = True
    report = mod.build_validation_report(artifact, diagnostics, lineage_manifest)
    assert _check(report, "epa_split_block_metadata_if_applicable")["passed"] is False


def test_validation_report_fails_on_missing_source_refs(mod):
    artifact, diagnostics, lineage_manifest = _good_fixture(mod)
    artifact["sourceArtifacts"] = []
    report = mod.build_validation_report(artifact, diagnostics, lineage_manifest)
    assert _check(report, "source_refs_present")["passed"] is False


def test_validation_report_fails_on_incomplete_retrieval_metadata(mod):
    artifact, diagnostics, lineage_manifest = _good_fixture(mod)
    del lineage_manifest["sources"][0]["packageVersion"]
    report = mod.build_validation_report(artifact, diagnostics, lineage_manifest)
    assert _check(report, "retrieval_metadata_complete")["passed"] is False


def test_validation_report_fails_on_governed_status_claim(mod):
    artifact, diagnostics, lineage_manifest = _good_fixture(mod)
    artifact["metadata"]["provenanceStatus"] = "governed_real_data"
    report = mod.build_validation_report(artifact, diagnostics, lineage_manifest)
    assert _check(report, "non_governed_status")["passed"] is False


def test_validation_report_fails_when_source_checksum_missing(mod):
    artifact, diagnostics, lineage_manifest = _good_fixture(mod)
    del lineage_manifest["sources"][0]["checksum"]
    report = mod.build_validation_report(artifact, diagnostics, lineage_manifest)
    assert _check(report, "source_checksums_present")["passed"] is False
    assert report["allPassed"] is False


def test_validation_report_fails_when_pressure_not_marked_deferred(mod):
    artifact, diagnostics, lineage_manifest = _good_fixture(mod)
    artifact["metadata"]["fieldReadiness"]["pressureRateAllowed"] = "available"
    report = mod.build_validation_report(artifact, diagnostics, lineage_manifest)
    assert _check(report, "pressure_field_readiness_deferred")["passed"] is False
    assert report["allPassed"] is False


def test_build_field_readiness_marks_pressure_deferred(mod):
    readiness = mod.build_field_readiness(
        [
            {
                "neutralPlaysDenominatorZero": False,
                "redZoneTripsDenominatorZero": True,
                "paceBlocked": False,
                "dropbackSplitBlocked": False,
            }
        ]
    )
    assert readiness["pressureRateAllowed"] == "deferred"
    # zero-denominator red-zone null is partial_nulls, not a deferral
    assert readiness["redZoneTdRate"] == "partial_nulls"
    assert readiness["neutralPassRate"] == "available"


def test_to_contract_input_source_carries_checksum_and_lineage(mod):
    source_info = {
        "sourceUrlOrDatasetId": "https://example.invalid/pbp.parquet",
        "retrievalTimestamp": "2024-01-01T00:00:00+00:00",
        "sourceName": "nflverse play-by-play",
        "retrievalMethod": "httpx GET ... parsed via polars.read_parquet",
        "packageVersion": "0.1.5",
        "sourceRefs": ["nflverse-data:pbp/play_by_play_2024"],
        "transformCodePath": "scripts/build_team_week_raw_v0_2024_candidate.py",
        "checksum": {"algorithm": "sha256", "value": "b" * 64},
        "immutableSourceRef": None,
    }
    contract_source = mod._to_contract_input_source(source_info)
    assert contract_source["checksum"] == {"algorithm": "sha256", "value": "b" * 64}
    assert contract_source["sourceRefs"] == ["nflverse-data:pbp/play_by_play_2024"]
    # immutableSourceRef is None (mutable upstream) and must be omitted, not null
    assert "immutableSourceRef" not in contract_source

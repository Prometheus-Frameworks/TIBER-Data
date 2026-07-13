from __future__ import annotations

import json
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import Any

import pytest


def _load_module():
    module_path = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "build_formation_summary_v0_2024_candidate.py"
    )
    spec = spec_from_file_location("build_formation_summary_v0_2024_candidate", module_path)
    assert spec is not None and spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def mod():
    return _load_module()


def play(**overrides: Any) -> dict[str, Any]:
    """One deterministic fixture pbp row; no network fetch anywhere in this file."""
    base: dict[str, Any] = {
        "posteam": "KC",
        "play_type": "pass",
        "two_point_attempt": 0.0,
        "aborted_play": 0.0,
        "shotgun": 1.0,
        "qb_dropback": 1.0,
        "epa": 0.1,
        "down": 1,
        "ydstogo": 10,
        "yards_gained": 5,
        "success": None,
    }
    base.update(overrides)
    return base


def team_fixture_plays(
    mod, team: str, *, shotgun: int = 150, non_shotgun: int = 110, unknown: int = 0
) -> list[dict[str, Any]]:
    """Deterministic qualifying plays for one team, alternating pass/run."""
    plays: list[dict[str, Any]] = []
    for count, shotgun_value in ((shotgun, 1.0), (non_shotgun, 0.0), (unknown, None)):
        for i in range(count):
            plays.append(
                play(
                    posteam=team,
                    shotgun=shotgun_value,
                    play_type="pass" if i % 2 == 0 else "run",
                    qb_dropback=1.0 if i % 2 == 0 else 0.0,
                    epa=0.05 if i % 2 == 0 else -0.05,
                    down=(i % 4) + 1,
                    ydstogo=10,
                    yards_gained=12 if i % 3 == 0 else 2,
                )
            )
    return plays


# ---------------------------------------------------------------------------
# Qualifying-play denominator (spec sections 3.1/3.1a + #214)
# ---------------------------------------------------------------------------

def test_qualifying_denominator_is_pass_run_only(mod):
    for play_type in ("qb_kneel", "qb_spike", "no_play", "punt", "field_goal",
                      "kickoff", "extra_point", None):
        assert not mod.is_qualifying_play(play(play_type=play_type)), play_type
    assert mod.is_qualifying_play(play(play_type="pass"))
    assert mod.is_qualifying_play(play(play_type="run"))


def test_null_posteam_excluded(mod):
    assert not mod.is_qualifying_play(play(posteam=None))


def test_two_point_attempt_excluded(mod):
    assert not mod.is_qualifying_play(play(two_point_attempt=1.0))
    assert not mod.is_qualifying_play(play(two_point_attempt=1))
    assert not mod.is_qualifying_play(play(two_point_attempt=True))


def test_aborted_play_excluded_even_inside_pass_run(mod):
    # The #214 live finding: aborted plays appear with play_type pass/run and a
    # naive pass/run denominator would wrongly include them.
    assert not mod.is_qualifying_play(play(play_type="pass", aborted_play=1.0))
    assert not mod.is_qualifying_play(play(play_type="run", aborted_play=1.0))


def test_null_two_point_and_aborted_are_not_exclusions(mod):
    # Null-safe guard: a null flag is NOT itself an exclusion (spec section 3.1).
    assert mod.is_qualifying_play(play(two_point_attempt=None))
    assert mod.is_qualifying_play(play(aborted_play=None))
    assert mod.is_qualifying_play(play(two_point_attempt=None, aborted_play=None))
    assert mod.is_qualifying_play(play(two_point_attempt=0.0, aborted_play=0.0))


# ---------------------------------------------------------------------------
# Alignment classification (spec section 3.3)
# ---------------------------------------------------------------------------

def test_shotgun_one_is_shotgun(mod):
    assert mod.classify_alignment(play(shotgun=1.0)) == "shotgun"
    assert mod.classify_alignment(play(shotgun=1)) == "shotgun"


def test_shotgun_zero_is_non_shotgun_never_under_center(mod):
    label = mod.classify_alignment(play(shotgun=0.0))
    assert label == "non_shotgun"
    assert "under" not in label
    assert mod.FORBIDDEN_ALIGNMENT_LABEL not in mod.ALIGNMENT_VOCABULARY


def test_null_shotgun_goes_only_to_unknown_bucket(mod):
    assert (
        mod.classify_alignment(play(shotgun=None))
        == "unknown_or_unclassified_alignment"
    )


def test_unexpected_shotgun_value_fails_closed(mod):
    with pytest.raises(ValueError):
        mod.classify_alignment(play(shotgun=2.0))


# ---------------------------------------------------------------------------
# TIBER success definition (spec section 3.2)
# ---------------------------------------------------------------------------

def test_tiber_success_matches_team_state_rule(mod):
    assert mod.is_tiber_success(play(down=1, ydstogo=10, yards_gained=4))
    assert not mod.is_tiber_success(play(down=1, ydstogo=10, yards_gained=3))
    assert mod.is_tiber_success(play(down=2, ydstogo=10, yards_gained=6))
    assert not mod.is_tiber_success(play(down=2, ydstogo=10, yards_gained=5))
    assert mod.is_tiber_success(play(down=3, ydstogo=5, yards_gained=5))
    assert not mod.is_tiber_success(play(down=3, ydstogo=5, yards_gained=4))
    assert mod.is_tiber_success(play(down=4, ydstogo=1, yards_gained=1))


def test_tiber_success_null_inputs_are_not_success(mod):
    assert not mod.is_tiber_success(play(down=None))
    assert not mod.is_tiber_success(play(ydstogo=None))
    assert not mod.is_tiber_success(play(yards_gained=None))


def test_native_success_column_is_ignored(mod):
    # nflverse's own `success` field must not leak in (spec section 3.2): a play
    # flagged successful upstream but failing the TIBER distance rule counts as
    # not-successful, and vice versa.
    rows = [play(success=1.0, down=1, ydstogo=10, yards_gained=0)]
    stats = mod.aggregate_season(rows)["KC"]
    assert stats.buckets["shotgun"].success_count == 0
    rows = [play(success=0.0, down=1, ydstogo=10, yards_gained=10)]
    stats = mod.aggregate_season(rows)["KC"]
    assert stats.buckets["shotgun"].success_count == 1


# ---------------------------------------------------------------------------
# Pass/run split via qb_dropback (spec section 3.1b)
# ---------------------------------------------------------------------------

def test_scramble_counts_as_pass_via_qb_dropback(mod):
    scramble = play(play_type="run", qb_dropback=1.0, shotgun=1.0)
    stats = mod.aggregate_season([scramble])["KC"]
    bucket = stats.buckets["shotgun"]
    assert stats.qualifying_plays == 1  # still a qualifying offensive play
    assert bucket.pass_plays == 1  # ...but a PASS in the split, not a run
    assert bucket.run_plays == 0


def test_dropback_zero_counts_as_run(mod):
    handoff = play(play_type="run", qb_dropback=0.0)
    bucket = mod.aggregate_season([handoff])["KC"].buckets["shotgun"]
    assert bucket.run_plays == 1
    assert bucket.pass_plays == 0


def test_null_dropback_blocks_split_fields_for_row(mod):
    plays = team_fixture_plays(mod, "KC", shotgun=150, non_shotgun=110)
    plays.append(play(posteam="KC", qb_dropback=None))
    rows, diagnostics, suppressed = mod.build_rows(plays, ["fixture:test"])
    assert not suppressed
    (row,) = rows
    assert row["offensive_plays"] == 261  # the null-dropback play still qualifies
    for field in ("shotgun_pass_rate", "shotgun_run_rate",
                  "non_shotgun_pass_rate", "non_shotgun_run_rate"):
        assert row[field] is None, field
    codes = {note["code"] for note in row["sample_notes"]}
    assert "dropback_split_blocked" in codes
    assert diagnostics[0]["dropbackSplitBlocked"] is True
    assert diagnostics[0]["dropbackNullRows"] == 1


def test_split_rates_emitted_when_dropback_complete(mod):
    plays = team_fixture_plays(mod, "KC", shotgun=150, non_shotgun=110)
    rows, _, _ = mod.build_rows(plays, ["fixture:test"])
    (row,) = rows
    assert row["shotgun_pass_rate"] == pytest.approx(0.5)
    assert row["shotgun_run_rate"] == pytest.approx(0.5)
    assert row["shotgun_pass_rate"] + row["shotgun_run_rate"] == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# Three-bucket reconciliation and rates
# ---------------------------------------------------------------------------

def test_three_bucket_reconciliation_exact(mod):
    plays = team_fixture_plays(mod, "KC", shotgun=140, non_shotgun=100, unknown=20)
    rows, _, _ = mod.build_rows(plays, ["fixture:test"])
    (row,) = rows
    assert row["shotgun_plays"] == 140
    assert row["non_shotgun_plays"] == 100
    assert row["unknown_or_unclassified_alignment_plays"] == 20
    assert (
        row["shotgun_plays"]
        + row["non_shotgun_plays"]
        + row["unknown_or_unclassified_alignment_plays"]
        == row["offensive_plays"]
        == 260
    )
    assert row["shotgun_rate"] == pytest.approx(140 / 260, abs=1e-6)
    assert row["non_shotgun_rate"] == pytest.approx(100 / 260, abs=1e-6)
    assert row["unknown_alignment_rate"] == pytest.approx(20 / 260, abs=1e-6)


def test_unknown_bucket_explicit_even_when_zero(mod):
    plays = team_fixture_plays(mod, "KC", shotgun=150, non_shotgun=110, unknown=0)
    rows, _, _ = mod.build_rows(plays, ["fixture:test"])
    (row,) = rows
    assert row["unknown_or_unclassified_alignment_plays"] == 0
    assert row["unknown_alignment_rate"] == 0.0
    assert row["unknown_alignment_uncertainty_flag"] is False


def test_excluded_plays_never_reach_any_bucket(mod):
    plays = team_fixture_plays(mod, "KC", shotgun=150, non_shotgun=110)
    plays.extend(
        [
            play(posteam="KC", play_type="no_play"),
            play(posteam="KC", play_type="qb_kneel"),
            play(posteam="KC", play_type="qb_spike"),
            play(posteam="KC", play_type="punt"),
            play(posteam="KC", two_point_attempt=1.0),
            play(posteam="KC", aborted_play=1.0),
            play(posteam="KC", play_type="run", aborted_play=1.0),
        ]
    )
    rows, _, _ = mod.build_rows(plays, ["fixture:test"])
    (row,) = rows
    assert row["offensive_plays"] == 260
    assert row["two_point_plays"] == 1
    assert row["aborted_plays_excluded"] == 2


def test_high_unknown_share_sets_uncertainty_flag(mod):
    plays = team_fixture_plays(mod, "KC", shotgun=150, non_shotgun=80, unknown=40)
    rows, _, _ = mod.build_rows(plays, ["fixture:test"])
    (row,) = rows
    assert row["unknown_alignment_uncertainty_flag"] is True
    codes = {note["code"] for note in row["sample_notes"]}
    assert "high_unknown_alignment_share" in codes


# ---------------------------------------------------------------------------
# Sample-threshold suppression (spec section 6.1)
# ---------------------------------------------------------------------------

def test_row_below_min_offensive_plays_is_suppressed(mod):
    plays = team_fixture_plays(mod, "KC", shotgun=100, non_shotgun=100)  # 200 < 250
    rows, diagnostics, suppressed = mod.build_rows(plays, ["fixture:test"])
    assert rows == []
    assert diagnostics == []
    (entry,) = suppressed
    assert entry["team"] == "KC"
    assert entry["offensivePlays"] == 200
    assert entry["requiredPlays"] == mod.MIN_ROW_OFFENSIVE_PLAYS


def test_bucket_below_efficiency_threshold_is_null_blocked_never_zero(mod):
    plays = team_fixture_plays(mod, "KC", shotgun=210, non_shotgun=50)
    rows, _, _ = mod.build_rows(plays, ["fixture:test"])
    (row,) = rows
    assert row["non_shotgun_epa_per_play"] is None
    assert row["non_shotgun_success_rate"] is None
    assert row["shotgun_epa_per_play"] is not None
    assert row["shotgun_success_rate"] is not None
    threshold_notes = [
        note for note in row["sample_notes"] if note["code"] == "sample_threshold_not_met"
    ]
    assert len(threshold_notes) == 1
    assert "non_shotgun_epa_per_play" in threshold_notes[0]["fields"]
    assert threshold_notes[0]["bucketPlays"] == 50
    assert threshold_notes[0]["requiredPlays"] == mod.MIN_BUCKET_PLAYS_FOR_EFFICIENCY


# ---------------------------------------------------------------------------
# Envelope, validation report, and forbidden-label guard
# ---------------------------------------------------------------------------

def fake_source_info(mod) -> dict[str, Any]:
    return {
        "sourceName": "fixture play-by-play",
        "sourceType": "fixture",
        "retrievalMethod": "in-test deterministic fixture (no network fetch)",
        "retrievalTimestamp": "2026-07-13T00:00:00+00:00",
        "packageVersion": "0.0.0-fixture",
        "sourceUrlOrDatasetId": "fixture:formation_summary_v0_unit_tests",
        "transformCodePath": mod.TRANSFORM_CODE_PATH,
        "sourceRefs": ["fixture:formation_summary_v0_unit_tests"],
        "checksum": {"algorithm": "sha256", "value": "0" * 64},
        "immutableSourceRef": None,
        "mutabilityNote": "fixture",
    }


def full_league_artifact(mod) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    plays: list[dict[str, Any]] = []
    for team in sorted(mod.CANONICAL_TEAMS):
        plays.extend(team_fixture_plays(mod, team, shotgun=150, non_shotgun=110, unknown=4))
    source_info = fake_source_info(mod)
    rows, diagnostics, suppressed = mod.build_rows(plays, list(source_info["sourceRefs"]))
    metadata = mod.build_metadata(
        rows=rows,
        diagnostics=diagnostics,
        suppressed=suppressed,
        input_sources_meta=[source_info],
        provenance_status=mod.PROVENANCE_FIXTURE,
    )
    artifact = mod.build_artifact(rows, metadata, list(source_info["sourceRefs"]))
    lineage = mod.build_lineage_manifest([source_info])
    return artifact, diagnostics, lineage


def test_full_fixture_artifact_passes_all_validation_checks(mod):
    artifact, diagnostics, lineage = full_league_artifact(mod)
    report = mod.build_validation_report(artifact, diagnostics, lineage)
    failed = [check["name"] for check in report["checks"] if not check["passed"]]
    assert report["allPassed"], failed
    assert report["teamCount"] == 32


def test_artifact_never_contains_under_center(mod):
    artifact, _, _ = full_league_artifact(mod)
    assert mod.FORBIDDEN_ALIGNMENT_LABEL not in json.dumps(artifact)


def test_validation_fails_on_broken_reconciliation(mod):
    artifact, diagnostics, lineage = full_league_artifact(mod)
    artifact["rows"][0]["shotgun_plays"] += 1
    report = mod.build_validation_report(artifact, diagnostics, lineage)
    assert not report["allPassed"]
    failing = {check["name"] for check in report["checks"] if not check["passed"]}
    assert "three_bucket_reconciliation_exact" in failing


def test_validation_fails_on_forbidden_label(mod):
    artifact, diagnostics, lineage = full_league_artifact(mod)
    artifact["metadata"]["provenanceNotes"] = [
        f"{mod.FORBIDDEN_ALIGNMENT_LABEL} tendencies are strong this season"
    ]
    report = mod.build_validation_report(artifact, diagnostics, lineage)
    failing = {check["name"] for check in report["checks"] if not check["passed"]}
    assert "alignment_vocabulary_exact_no_forbidden_label" in failing


def test_validation_fails_on_missing_checksum(mod):
    artifact, diagnostics, lineage = full_league_artifact(mod)
    del lineage["sources"][0]["checksum"]
    report = mod.build_validation_report(artifact, diagnostics, lineage)
    failing = {check["name"] for check in report["checks"] if not check["passed"]}
    assert "source_checksums_present" in failing


def test_validation_fails_on_governed_claim(mod):
    artifact, diagnostics, lineage = full_league_artifact(mod)
    artifact["metadata"]["governance"]["governanceStatus"] = "governed"
    report = mod.build_validation_report(artifact, diagnostics, lineage)
    failing = {check["name"] for check in report["checks"] if not check["passed"]}
    assert "non_governed_non_promoted_status" in failing


def test_metadata_rejects_unknown_provenance_status(mod):
    with pytest.raises(ValueError):
        mod.build_metadata(
            rows=[],
            diagnostics=[],
            suppressed=[],
            input_sources_meta=[],
            provenance_status="governed_real_data",
        )


def test_epa_average_ignores_nulls_and_notes_them(mod):
    plays = team_fixture_plays(mod, "KC", shotgun=150, non_shotgun=110)
    plays.append(play(posteam="KC", epa=None))
    rows, _, _ = mod.build_rows(plays, ["fixture:test"])
    (row,) = rows
    assert row["shotgun_epa_per_play"] is not None
    codes = {note["code"] for note in row["sample_notes"]}
    assert "epa_null_rows_ignored" in codes


def test_team_code_canonicalization(mod):
    plays = team_fixture_plays(mod, "LA", shotgun=150, non_shotgun=110)
    rows, _, _ = mod.build_rows(plays, ["fixture:test"])
    (row,) = rows
    assert row["team"] == "LAR"

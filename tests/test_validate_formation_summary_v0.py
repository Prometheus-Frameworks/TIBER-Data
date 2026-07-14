from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import Any

import pytest


def _load(script_name: str):
    module_path = Path(__file__).resolve().parents[1] / "scripts" / script_name
    spec = spec_from_file_location(script_name.removesuffix(".py"), module_path)
    assert spec is not None and spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def builder():
    return _load("build_formation_summary_v0_2024_candidate.py")


@pytest.fixture(scope="module")
def validator():
    return _load("validate_formation_summary_v0.py")


def fixture_plays(builder, team: str) -> list[dict[str, Any]]:
    plays = []
    for count, shotgun_value in ((150, 1.0), (110, 0.0), (4, None)):
        for i in range(count):
            plays.append(
                {
                    "posteam": team,
                    "play_type": "pass" if i % 2 == 0 else "run",
                    "two_point_attempt": 0.0,
                    "aborted_play": 0.0,
                    "shotgun": shotgun_value,
                    "qb_dropback": 1.0 if i % 2 == 0 else 0.0,
                    "epa": 0.05 if i % 2 == 0 else -0.05,
                    "down": (i % 4) + 1,
                    "ydstogo": 10,
                    "yards_gained": 12 if i % 3 == 0 else 2,
                }
            )
    return plays


@pytest.fixture()
def artifact(builder) -> dict[str, Any]:
    source_info = {
        "sourceName": "fixture play-by-play",
        "sourceType": "fixture",
        "retrievalMethod": "in-test deterministic fixture (no network fetch)",
        "retrievalTimestamp": "2026-07-13T00:00:00+00:00",
        "packageVersion": "0.0.0-fixture",
        "sourceUrlOrDatasetId": "fixture:formation_summary_v0_unit_tests",
        "transformCodePath": builder.TRANSFORM_CODE_PATH,
        "sourceRefs": ["fixture:formation_summary_v0_unit_tests"],
        "checksum": {"algorithm": "sha256", "value": "0" * 64},
    }
    plays: list[dict[str, Any]] = []
    for team in sorted(builder.CANONICAL_TEAMS):
        plays.extend(fixture_plays(builder, team))
    rows, diagnostics, suppressed = builder.build_rows(
        plays, list(source_info["sourceRefs"])
    )
    metadata = builder.build_metadata(
        rows=rows,
        diagnostics=diagnostics,
        suppressed=suppressed,
        input_sources_meta=[source_info],
        provenance_status=builder.PROVENANCE_FIXTURE,
    )
    return builder.build_artifact(rows, metadata, list(source_info["sourceRefs"]))


def test_valid_fixture_artifact_passes(validator, artifact):
    assert validator.validate_artifact(artifact) == []


def test_schema_rejects_under_center_row_field(validator, artifact):
    # additionalProperties: false makes an under_center field a structural
    # violation, not just a business-rule one.
    artifact["rows"][0][validator.FORBIDDEN_ALIGNMENT_LABEL + "_plays"] = 100
    errors = validator.validate_artifact(artifact)
    assert errors
    assert any("schema" in error for error in errors)


def test_business_rule_rejects_under_center_prose(validator, artifact):
    artifact["metadata"]["provenanceNotes"].append(
        f"strong {validator.FORBIDDEN_ALIGNMENT_LABEL} tendencies"
    )
    errors = validator.validate_artifact(artifact)
    assert any("forbidden alignment label" in error for error in errors)


def test_rejects_broken_reconciliation(validator, artifact):
    artifact["rows"][0]["shotgun_plays"] += 1
    errors = validator.validate_artifact(artifact)
    assert any("reconciliation" in error for error in errors)


def test_rejects_out_of_bounds_rate(validator, artifact):
    artifact["rows"][0]["shotgun_rate"] = 1.5
    errors = validator.validate_artifact(artifact)
    assert any("shotgun_rate" in error for error in errors)


def test_rejects_efficiency_below_threshold(validator, artifact):
    row = artifact["rows"][0]
    row["non_shotgun_plays"] = 50
    row["shotgun_plays"] = row["offensive_plays"] - 50 - (
        row["unknown_or_unclassified_alignment_plays"]
    )
    # keep rates consistent so only the threshold rule trips
    row["shotgun_rate"] = row["shotgun_plays"] / row["offensive_plays"]
    row["non_shotgun_rate"] = 50 / row["offensive_plays"]
    assert row["non_shotgun_epa_per_play"] is not None
    errors = validator.validate_artifact(artifact)
    assert any("threshold" in error for error in errors)


def test_rejects_null_split_without_note(validator, artifact):
    artifact["rows"][0]["shotgun_pass_rate"] = None
    errors = validator.validate_artifact(artifact)
    assert any("dropback_split_blocked" in error for error in errors)


def test_rejects_missing_checksum(validator, artifact):
    del artifact["metadata"]["inputSources"][0]["checksum"]
    errors = validator.validate_artifact(artifact)
    assert errors


def test_rejects_inconsistent_uncertainty_flag(validator, artifact):
    artifact["rows"][0]["unknown_alignment_uncertainty_flag"] = True
    errors = validator.validate_artifact(artifact)
    assert any("uncertainty_flag" in error for error in errors)


def test_rejects_governed_provenance_claim(validator, artifact):
    artifact["metadata"]["governance"]["governanceStatus"] = "governed"
    errors = validator.validate_artifact(artifact)
    assert any("ungoverned" in error for error in errors)


def test_rejects_missing_team_coverage(validator, artifact):
    # Incomplete team coverage is a hard failure even when the remaining rows
    # reconcile (Codex review finding on PR #215).
    removed = artifact["rows"].pop(0)
    errors = validator.validate_artifact(artifact)
    assert any("missing canonical team" in error for error in errors)
    assert any(removed["team"] in error for error in errors)


def test_rejects_stale_coverage_metadata(validator, artifact):
    artifact["metadata"]["coverage"]["missingTeams"] = ["KC"]
    artifact["metadata"]["coverage"]["isFullLeague"] = False
    errors = validator.validate_artifact(artifact)
    assert any("missingTeams" in error for error in errors)
    assert any("isFullLeague" in error for error in errors)


def test_rejects_wrong_alignment_vocabulary(validator, artifact):
    artifact["metadata"]["alignmentVocabulary"] = ["shotgun", "non_shotgun"]
    errors = validator.validate_artifact(artifact)
    assert any("alignmentVocabulary" in error for error in errors)

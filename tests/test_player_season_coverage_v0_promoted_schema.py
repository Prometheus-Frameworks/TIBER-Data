"""Tests for the TIBER-Data#204 generalization of promotion_review in the promoted schema.

Confirms:
- both the original TIBER-Data#192 promotion event and a later one (TIBER-Data#202) validate,
- malformed/non-TIBER-Data review references still fail closed,
- the true invariants (status, row_grain) remain untouched and still reject deviation,
- the currently-committed #192 promoted artifact still validates against the updated schema
  (no regression),
- the PR #203 promotion helper's build_promoted_payload output now passes schema validation,
  WITHOUT writing any promoted files (this test never calls main() or touches disk paths under
  exports/promoted/**).
"""

import hashlib
import json
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import jsonschema
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = REPO_ROOT / "schemas/player_season_coverage_v0_promoted.schema.json"
PROMOTED_ARTIFACT_PATH = REPO_ROOT / "exports/promoted/nfl/player_season_coverage_v0.json"


def _load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _load_module(name: str, relpath: str):
    module_path = REPO_ROOT / relpath
    spec = spec_from_file_location(name, module_path)
    assert spec is not None and spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _validate(payload: dict) -> list[str]:
    schema = _load_schema()
    validator = jsonschema.Draft202012Validator(schema)
    return [f"{'/'.join(str(p) for p in err.path)}: {err.message}" for err in validator.iter_errors(payload)]


def _base_record() -> dict:
    return {
        "player_id": "p1",
        "player_name": "Test Player",
        "position": "WR",
        "identity_confidence": "source_verified",
        "season": 2023,
        "season_type": "REG",
        "generated_at": "2026-06-30T00:00:00+00:00",
        "source_refs": [
            {
                "source_name": "nflreadpy.load_player_stats(summary_level='reg')",
                "observed_at": "2026-06-30T00:00:00+00:00",
                "confidence": "source_verified",
            }
        ],
        "teams": ["PHI"],
        "primary_team": "PHI",
        "weeks_observed": 10,
        "coverage_status": "partial_season",
        "coverage_notes": "10 of 17 REG weeks observed.",
        "missing_fields": [],
    }


def _minimal_promoted_payload(promotion_review: str = "TIBER-Data#192") -> dict:
    return {
        "artifact_id": "player_season_coverage_v0",
        "status": "promoted_governed_artifact",
        "generated_at": "2026-06-30T00:00:00+00:00",
        "promoted_at": "2026-07-03T00:00:00Z",
        "promotion_review": promotion_review,
        "source_candidate": {"path": "data/x.json", "sha256": "a" * 64},
        "approved_source_allowlist": ["nflreadpy.load_player_stats("],
        "seasons": [2023],
        "season_type_scope": ["REG"],
        "row_grain": "player_id + season + season_type",
        "consumer_safety": {"allowed": ["x"], "not_allowed": ["y"]},
        "records": [_base_record()],
    }


@pytest.mark.parametrize("review_ref", ["TIBER-Data#192", "TIBER-Data#202", "TIBER-Data#204", "TIBER-Data#1"])
def test_valid_tiber_data_references_pass(review_ref: str) -> None:
    payload = _minimal_promoted_payload(promotion_review=review_ref)
    assert _validate(payload) == []


@pytest.mark.parametrize(
    "bad_ref",
    [
        "192",
        "TIBER-Data192",
        "tiber-data#192",
        "TIBER-DATA#192",
        "TIBER-Data#",
        "TIBER-Data#19a",
        "TIBER-Data# 192",
        "TIBER-Data#192 ",
        " TIBER-Data#192",
        "",
        "TIBER-Forecast#134",
        "TIBER-Data#192\n",
        "TIBER-Data#192\n\n",
        "TIBER-Data#192\r\n",
        "\nTIBER-Data#192",
    ],
)
def test_malformed_review_references_fail(bad_ref: str) -> None:
    """Includes trailing-newline variants: Python's `re` treats a bare `$` as matching
    before a single trailing newline rather than strict end-of-string, so a naive
    `^TIBER-Data#[0-9]+$` pattern would let 'TIBER-Data#192\\n' validate. The schema
    uses `\\Z` instead, which must reject every one of these."""
    payload = _minimal_promoted_payload(promotion_review=bad_ref)
    errors = _validate(payload)
    assert errors, f"expected {bad_ref!r} to fail schema validation"
    assert any("promotion_review" in e for e in errors)


def test_pattern_uses_end_of_string_anchor_not_dollar() -> None:
    schema = _load_schema()
    pattern = schema["properties"]["promotion_review"]["pattern"]
    assert pattern.endswith("\\Z"), (
        f"pattern {pattern!r} must end with \\Z, not a bare $, to reject a trailing newline "
        "(Python's re treats $ as matching before a final \\n)"
    )


def test_status_invariant_still_rejects_deviation() -> None:
    payload = _minimal_promoted_payload()
    payload["status"] = "not_promoted"
    errors = _validate(payload)
    assert any("status" in e for e in errors)


def test_row_grain_invariant_still_rejects_deviation() -> None:
    payload = _minimal_promoted_payload()
    payload["row_grain"] = "player_id + season"
    errors = _validate(payload)
    assert any("row_grain" in e for e in errors)


def test_status_and_row_grain_remain_const_in_schema() -> None:
    schema = _load_schema()
    assert schema["properties"]["status"].get("const") == "promoted_governed_artifact"
    assert schema["properties"]["row_grain"].get("const") == "player_id + season + season_type"


def test_promotion_review_no_longer_const() -> None:
    schema = _load_schema()
    assert "const" not in schema["properties"]["promotion_review"]
    assert schema["properties"]["promotion_review"].get("pattern") == "^TIBER-Data#[0-9]+\\Z"


def test_committed_192_promoted_artifact_still_validates() -> None:
    """Regression: the generalization must not break the artifact #192 already promoted."""
    if not PROMOTED_ARTIFACT_PATH.exists():
        pytest.skip("promoted artifact not present in this environment")
    payload = json.loads(PROMOTED_ARTIFACT_PATH.read_text(encoding="utf-8"))
    errors = _validate(payload)
    assert errors == [], f"unexpected validation errors against the currently-promoted #192 artifact: {errors}"


def test_pr203_promotion_helper_payload_now_passes_schema_without_writing_promoted_files() -> None:
    """Confirms TIBER-Data#202 review question 7: the PR#203 promotion helper's output can now
    pass schema validation. This test calls build_promoted_payload directly -- the pure,
    non-writing transformation -- and never calls main() or touches exports/promoted/**."""
    merged_candidate_path = REPO_ROOT / "data/processed/evidence/player_season_coverage_2021_2025.source_backed.json"
    if not merged_candidate_path.exists():
        pytest.skip("merged 2021-2025 candidate not present in this environment")

    promote_module = _load_module(
        "promote_player_season_coverage_v0_2021_2025", "scripts/promote_player_season_coverage_v0_2021_2025.py"
    )
    validator_module = _load_module("validate_player_season_coverage_v0", "scripts/validate_player_season_coverage_v0.py")

    candidate_raw = merged_candidate_path.read_bytes()
    candidate_sha256 = hashlib.sha256(candidate_raw).hexdigest()
    candidate = json.loads(candidate_raw.decode("utf-8"))

    prior_promoted_sha256 = None
    if promote_module.PRIOR_PROMOTED_PATH.exists():
        prior_promoted_sha256 = hashlib.sha256(promote_module.PRIOR_PROMOTED_PATH.read_bytes()).hexdigest()

    promoted_payload = promote_module.build_promoted_payload(
        candidate,
        candidate_sha256,
        promote_module.PINNED_CANDIDATE_SHA256,
        validator_module,
        prior_promoted_sha256,
    )

    errors = _validate(promoted_payload)
    assert errors == [], f"PR#203 promotion payload still fails the generalized schema: {errors}"
    assert promoted_payload["promotion_review"] == "TIBER-Data#202"

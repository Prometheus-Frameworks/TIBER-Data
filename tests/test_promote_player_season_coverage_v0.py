"""Governance tests for the player_season_coverage_v0 promotion path (TIBER-Data #192)."""

from __future__ import annotations

import json
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_PATH = REPO_ROOT / "data/processed/evidence/player_season_coverage_2022_2025.source_backed.json"
PROMOTED_PATH = REPO_ROOT / "exports/promoted/nfl/player_season_coverage_v0.json"


def _load(name: str):
    module_path = REPO_ROOT / "scripts" / f"{name}.py"
    spec = spec_from_file_location(name, module_path)
    assert spec is not None and spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


validator = _load("validate_player_season_coverage_v0")
promoter = _load("promote_player_season_coverage_v0")


def _record(**overrides) -> dict:
    base = {
        "player_id": "00-0000001",
        "player_name": "Test Player",
        "position": "WR",
        "identity_confidence": "source_verified",
        "season": 2024,
        "season_type": "REG",
        "generated_at": "2026-06-30T00:00:00Z",
        "source_refs": [
            {
                "source_name": "nflreadpy.load_player_stats(summary_level='reg')",
                "observed_at": "2026-06-30T00:00:00Z",
                "confidence": "source_verified",
            }
        ],
        "teams": ["PHI"],
        "primary_team": "PHI",
        "primary_team_rule": None,
        "weeks_observed": 10,
        "coverage_status": "partial_season",
        "coverage_notes": "test",
        "missing_fields": ["games_missed"],
        "usage_summary": {"targets": 10, "snap_share": None},
        "birth_date": "1998-01-01",
        "season_age": 26.5,
        "rookie_year": 2020,
        "career_year": 4,
    }
    base.update(overrides)
    return base


def _candidate(records: list[dict]) -> dict:
    return {
        "artifact_id": "player_season_coverage_2022_2025.source_backed",
        "spec_version": "player_season_coverage_v0_candidate",
        "status": "candidate_evidence_artifact_not_promoted",
        "generated_at": "2026-06-30T00:00:00Z",
        "seasons": [2022, 2023, 2024, 2025],
        "season_type_scope": ["REG"],
        "row_grain": "player_id + season + season_type",
        "records": records,
    }


class TestValidatorGovernance:
    def test_real_candidate_artifact_passes(self):
        payload = json.loads(CANDIDATE_PATH.read_text(encoding="utf-8"))
        assert validator.validate_payload(payload) == []

    def test_duplicate_grain_fails(self):
        errors = validator.validate_payload(_candidate([_record(), _record()]))
        assert any("duplicate grain" in e for e in errors)

    def test_missing_source_refs_fails(self):
        errors = validator.validate_payload(_candidate([_record(source_refs=[])]))
        assert any("missing source_refs" in e for e in errors)

    def test_mixed_approved_and_unapproved_source_fails(self):
        record = _record(
            source_refs=[
                {"source_name": "nflreadpy.load_player_stats(summary_level='reg')", "observed_at": "2026-06-30T00:00:00Z", "confidence": "source_verified"},
                {"source_name": "manual_override_or_unknown_source", "observed_at": "2026-06-30T00:00:00Z", "confidence": "source_verified"},
            ]
        )
        errors = validator.validate_payload(_candidate([record]))
        assert any("unapproved source ref" in e for e in errors)

    def test_unapproved_only_source_fails(self):
        record = _record(source_refs=[{"source_name": "manual_spreadsheet:file.xlsx", "observed_at": "2026-06-30T00:00:00Z", "confidence": "source_verified"}])
        errors = validator.validate_payload(_candidate([record]))
        assert any("unapproved source ref" in e for e in errors)

    def test_embedded_approved_token_fails(self):
        # A free-text name that merely EMBEDS an approved token must not pass the prefix allow-list.
        record = _record(
            source_refs=[
                {"source_name": "manual_override:nflreadpy.load_players()", "observed_at": "2026-06-30T00:00:00Z", "confidence": "source_verified"}
            ]
        )
        errors = validator.validate_payload(_candidate([record]))
        assert any("unapproved source ref" in e for e in errors)

    def test_fixture_source_marker_fails(self):
        record = _record(source_refs=[{"source_name": "offline_fixture:data/raw/foo.json", "observed_at": "2026-06-30T00:00:00Z", "confidence": "source_verified"}])
        errors = validator.validate_payload(_candidate([record]))
        assert any("fixture/scaffold source" in e for e in errors)

    def test_forbidden_availability_field_fails(self):
        errors = validator.validate_payload(_candidate([_record(active_status="active")]))
        assert any("forbidden availability" in e for e in errors)

    def test_unavailable_usage_field_coerced_to_zero_fails(self):
        errors = validator.validate_payload(_candidate([_record(usage_summary={"targets": 10, "snap_share": 0})]))
        assert any("must be null/unavailable, not zero" in e for e in errors)

    def test_fabricated_age_fails(self):
        errors = validator.validate_payload(_candidate([_record(birth_date=None, season_age=26.5)]))
        assert any("possible fabrication" in e for e in errors)

    def test_non_candidate_status_fails(self):
        payload = _candidate([_record()])
        payload["status"] = "promoted_governed_artifact"
        errors = validator.validate_payload(payload)
        assert any("candidate_evidence_artifact_not_promoted" in e for e in errors)


class TestPromotionGates:
    def test_sha_mismatch_fails_closed(self):
        with pytest.raises(SystemExit, match="sha256 .* does not match the pin"):
            promoter.build_promoted_payload(_candidate([_record()]), "0" * 64, validator)

    def test_validator_errors_fail_closed(self):
        with pytest.raises(SystemExit, match="candidate validator reported"):
            promoter.build_promoted_payload(
                _candidate([_record(source_refs=[])]), promoter.PINNED_CANDIDATE_SHA256, validator
            )

    def test_non_reg_season_type_fails_promoted_scope(self):
        # POST is legal at candidate level (future expansion) but outside the promoted envelope scope.
        with pytest.raises(SystemExit, match="outside promoted scope"):
            promoter.build_promoted_payload(
                _candidate([_record(season_type="POST")]), promoter.PINNED_CANDIDATE_SHA256, validator
            )

    def test_out_of_scope_position_fails_promoted_scope(self):
        with pytest.raises(SystemExit, match="outside promoted scope"):
            promoter.build_promoted_payload(
                _candidate([_record(position="K")]), promoter.PINNED_CANDIDATE_SHA256, validator
            )

    def test_promoted_payload_shape_and_boundaries(self):
        promoted = promoter.build_promoted_payload(_candidate([_record()]), promoter.PINNED_CANDIDATE_SHA256, validator)
        assert promoted["status"] == "promoted_governed_artifact"
        assert promoted["promotion_review"] == "TIBER-Data#192"
        assert promoted["source_candidate"]["sha256"] == promoter.PINNED_CANDIDATE_SHA256
        assert "Forecast production binding without a separate Forecast issue" in " ".join(
            promoted["consumer_safety"]["not_allowed"]
        )
        assert "separate Forecast-side gate" in promoted["forecast_compatibility_note"]

    def test_decision_enum_is_governance_only(self):
        assert promoter.PROMOTION_DECISIONS == (
            "promote_player_season_coverage_v0",
            "do_not_promote_requires_fixes",
            "do_not_promote_requires_new_source_artifact",
            "promotion_review_invalid_must_not_use",
        )
        for decision in promoter.PROMOTION_DECISIONS:
            for forbidden in ("forecast", "bind", "production_signal", "may_run", "advice", "ranking"):
                assert forbidden not in decision


class TestPromotedArtifact:
    promoted = json.loads(PROMOTED_PATH.read_text(encoding="utf-8"))

    def test_promoted_artifact_validates_against_promoted_schema(self):
        import jsonschema

        schema = json.loads((REPO_ROOT / "schemas/player_season_coverage_v0_promoted.schema.json").read_text(encoding="utf-8"))
        errors = list(jsonschema.Draft202012Validator(schema).iter_errors(self.promoted))
        assert errors == []

    def test_promoted_records_match_pinned_candidate_verbatim(self):
        """Tests the #192 candidate->promoted mapping directly, independent of whatever
        currently lives at PROMOTED_PATH. TIBER-Data#202/#206 intentionally superseded
        that live file's content with a second promotion event (2021-2025), so the live
        file can no longer serve as the comparison target for a #192-only rebuild -- the
        historical mapping is still verified by rebuilding from the pinned 2022-2025
        candidate and checking the mapping is lossless/verbatim on its own terms."""
        candidate = json.loads(CANDIDATE_PATH.read_text(encoding="utf-8"))
        rebuilt = promoter.build_promoted_payload(candidate, promoter.PINNED_CANDIDATE_SHA256, validator)
        assert rebuilt["records"] == candidate["records"]
        assert rebuilt["counts"]["records"] == 2383
        # rebuilt is an in-memory payload (int season keys), unlike a JSON-round-tripped
        # dict (string keys) -- compare with int keys accordingly.
        assert rebuilt["counts"]["by_season"] == {2022: 609, 2023: 576, 2024: 588, 2025: 610}

    def test_promotion_is_deterministic(self):
        """Determinism of the pure build_promoted_payload function, verified by comparing
        two independent rebuilds against each other -- not against PROMOTED_PATH, which
        TIBER-Data#202/#206 intentionally superseded with a later 2021-2025 promotion."""
        candidate = json.loads(CANDIDATE_PATH.read_text(encoding="utf-8"))
        rebuilt_a = promoter.build_promoted_payload(candidate, promoter.PINNED_CANDIDATE_SHA256, validator)
        rebuilt_b = promoter.build_promoted_payload(candidate, promoter.PINNED_CANDIDATE_SHA256, validator)
        assert (json.dumps(rebuilt_a, indent=1) + "\n") == (json.dumps(rebuilt_b, indent=1) + "\n")

    def test_manifest_pins_the_promoted_bytes(self):
        import hashlib

        manifest = json.loads((REPO_ROOT / "exports/promoted/nfl/PLAYER_SEASON_COVERAGE_V0_PROMOTION_MANIFEST.json").read_text(encoding="utf-8"))
        assert manifest["promoted_artifact_sha256"] == hashlib.sha256(PROMOTED_PATH.read_bytes()).hexdigest()
        assert "records" not in manifest

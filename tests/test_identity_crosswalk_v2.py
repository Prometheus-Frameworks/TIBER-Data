import json
import re
from copy import deepcopy
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker, ValidationError

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_PATH = ROOT / "exports/promoted/identity_crosswalk/tiber_identity_crosswalk_v2.json"
SCHEMA_PATH = ROOT / "schemas/tiber_identity_crosswalk_v2.schema.json"
V1_ARTIFACT_PATH = ROOT / "exports/promoted/identity_crosswalk/tiber_identity_crosswalk_v1.json"
GSIS_RE = re.compile(r"^00-\d{7}$")
RFC3339_UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _is_rfc3339_utc_datetime(value: object) -> bool:
    if not isinstance(value, str):
        return True
    if not RFC3339_UTC_RE.match(value):
        return False
    from datetime import datetime

    try:
        datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return False
    return True


def _load_module():
    module_path = ROOT / "scripts" / "promote_identity_crosswalk_rows.py"
    spec = spec_from_file_location("promote_identity_crosswalk_rows", module_path)
    assert spec is not None and spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_artifact() -> dict:
    return json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))


def _validator() -> Draft202012Validator:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    format_checker = FormatChecker()
    format_checker.checks("date-time")(_is_rfc3339_utc_datetime)
    return Draft202012Validator(schema, format_checker=format_checker)


def test_v2_artifact_validates_against_schema() -> None:
    payload = _load_artifact()
    _validator().validate(payload)
    _load_module().validate_artifact(payload)


def test_v2_ids_are_gsis_not_the_v1_vocabulary() -> None:
    """The whole reason V2 exists: tiber_player_id must join FORGE's GSIS rows."""
    payload = _load_artifact()
    assert payload["id_vocabulary"] == "gsis"
    for record in payload["records"]:
        assert GSIS_RE.match(record["tiber_player_id"]), record["tiber_player_id"]
        assert not record["tiber_player_id"].startswith("tiber-data-player-")


def test_v2_rejects_the_v1_id_vocabulary() -> None:
    payload = _load_artifact()
    payload["records"][0]["tiber_player_id"] = "tiber-data-player-2025-derrick-henry"

    with pytest.raises(ValidationError):
        _validator().validate(payload)


def test_v2_provider_canonical_ids_are_unique() -> None:
    """A duplicate provider key makes the downstream consumer fail closed."""
    records = _load_artifact()["records"]
    canonical_ids = [record["provider_canonical_id"] for record in records]
    assert len(set(canonical_ids)) == len(canonical_ids)


def test_v2_source_artifacts_are_pinned_by_hash() -> None:
    """Provenance must be reproducible by someone who was not in the promoting session."""
    payload = _load_artifact()
    artifacts = {entry["artifact"]: entry for entry in payload["source_artifacts"]}
    assert "FORGE_PLAYER_STATIC_V1" in artifacts
    assert "IDENTITY_CROSSWALK_CANDIDATES_V0" in artifacts
    for entry in payload["source_artifacts"]:
        assert SHA256_RE.match(entry["sha256"]), entry
        assert "/tmp/" not in entry["path"], f"ephemeral path in promoted provenance: {entry['path']}"


def test_v2_record_count_matches_records() -> None:
    payload = _load_artifact()
    assert payload["record_count"] == len(payload["records"])
    by_method: dict[str, int] = {}
    for record in payload["records"]:
        by_method[record["match_method"]] = by_method.get(record["match_method"], 0) + 1
    assert payload["record_count_by_match_method"] == dict(sorted(by_method.items()))


def test_v2_requires_required_row_fields() -> None:
    payload = _load_artifact()
    del payload["records"][0]["source"]

    with pytest.raises(ValidationError):
        _validator().validate(payload)


def test_v2_rejects_unsupported_match_method() -> None:
    payload = _load_artifact()
    payload["records"][0]["match_method"] = "vibes"

    with pytest.raises(ValidationError):
        _validator().validate(payload)


def test_v1_artifact_is_untouched_by_the_v2_promotion() -> None:
    """Versioning, not mutation: V1 keeps its own vocabulary and stays valid."""
    v1 = json.loads(V1_ARTIFACT_PATH.read_text(encoding="utf-8"))
    assert v1["artifact_id"] == "TIBER_IDENTITY_CROSSWALK_V1"
    assert v1["schema_version"] == "v1"
    assert v1["coverage"] == "seeded_operator_verified_mappings_only_not_full_player_universe"
    for record in v1["records"]:
        assert record["tiber_player_id"].startswith("tiber-data-player-2025-")


def test_promotion_refuses_a_forge_source_whose_hash_does_not_match(tmp_path) -> None:
    """A different file at the supplied path must not silently promote a different slice."""
    module = _load_module()
    forge_copy = tmp_path / "forge.json"
    forge_copy.write_text(json.dumps({"rows": [{"player_id": "00-0033280"}]}), encoding="utf-8")

    args = type(
        "Args",
        (),
        {
            "forge_artifact": str(forge_copy),
            "forge_artifact_ref": "TIBER-FORGE:exports/promoted/forge_player_static/forge_player_static_v1.json",
            "forge_sha256": "0" * 64,
            "candidates": str(ROOT / "exports/candidates/identity_crosswalk/identity_crosswalk_candidates_v0.json"),
            "existing": str(V1_ARTIFACT_PATH),
            "out": str(tmp_path / "out.json"),
            "generated_at": "2026-08-09T00:00:00Z",
        },
    )()

    with pytest.raises(SystemExit):
        module.build(args)

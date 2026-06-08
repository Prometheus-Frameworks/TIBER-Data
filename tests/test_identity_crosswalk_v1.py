import json
import re
from copy import deepcopy
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_PATH = ROOT / "exports/promoted/identity_crosswalk/tiber_identity_crosswalk_v1.json"
SCHEMA_PATH = ROOT / "schemas/tiber_identity_crosswalk_v1.schema.json"
RFC3339_UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


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
    module_path = ROOT / "scripts" / "build_identity_crosswalk_v1.py"
    spec = spec_from_file_location("build_identity_crosswalk_v1", module_path)
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


def test_identity_crosswalk_artifact_validates_against_schema() -> None:
    payload = _load_artifact()
    _validator().validate(payload)
    _load_module().validate_artifact(payload)


def test_identity_crosswalk_requires_required_row_fields() -> None:
    payload = _load_artifact()
    del payload["records"][0]["source"]

    with pytest.raises(Exception):
        _validator().validate(payload)
    with pytest.raises(ValueError, match="missing required fields"):
        _load_module().validate_artifact(payload)


def test_identity_crosswalk_rejects_duplicate_provider_mapping() -> None:
    payload = _load_artifact()
    duplicate = deepcopy(payload["records"][0])
    duplicate["tiber_player_id"] = "tiber-data-player-2025-conflicting-player"
    duplicate["player_name"] = "Conflicting Player"
    payload["records"].append(duplicate)
    payload["record_count"] = len(payload["records"])

    with pytest.raises(ValueError, match="duplicate provider mapping"):
        _load_module().validate_artifact(payload)


def test_identity_crosswalk_rejects_duplicate_conflicting_tiber_id() -> None:
    payload = _load_artifact()
    conflicting = deepcopy(payload["records"][0])
    conflicting["provider_player_id"] = "999999"
    conflicting["provider_canonical_id"] = "sleeper:999999"
    payload["records"].append(conflicting)
    payload["record_count"] = len(payload["records"])

    with pytest.raises(ValueError, match="conflicting sleeper mappings for TIBER player"):
        _load_module().validate_artifact(payload)


def test_identity_crosswalk_output_is_deterministic() -> None:
    module = _load_module()
    assert _load_artifact() == module.build_artifact()
    records = _load_artifact()["records"]
    assert records == sorted(
        records,
        key=lambda row: (row["provider"], row["provider_player_id"], row["tiber_player_id"]),
    )


def test_identity_crosswalk_includes_known_seeded_mappings() -> None:
    records = _load_artifact()["records"]
    rows_by_provider_id = {(row["provider"], row["provider_player_id"]): row for row in records}

    assert rows_by_provider_id[("sleeper", "6797")]["tiber_player_id"] == (
        "tiber-data-player-2025-justin-herbert"
    )
    assert rows_by_provider_id[("sleeper", "9493")]["tiber_player_id"] == (
        "tiber-data-player-2025-puka-nacua"
    )
    assert rows_by_provider_id[("sleeper", "9509")]["tiber_player_id"] == (
        "tiber-data-player-2025-bijan-robinson"
    )


def test_identity_crosswalk_rejects_unsupported_provider() -> None:
    payload = _load_artifact()
    payload["records"][0]["provider"] = "espn"
    payload["records"][0]["provider_canonical_id"] = "espn:6797"

    with pytest.raises(Exception):
        _validator().validate(payload)
    with pytest.raises(ValueError, match="unsupported"):
        _load_module().validate_artifact(payload)


def test_identity_crosswalk_requires_provenance_source_fields() -> None:
    payload = _load_artifact()

    for row in payload["records"]:
        assert row["source"] == "operator_verified_management_smoke"
        assert row["source_updated_at"] == "2026-06-08T00:00:00Z"
        assert row["confidence"] == "exact"
        assert row["match_method"] == "verified_manual_seed"

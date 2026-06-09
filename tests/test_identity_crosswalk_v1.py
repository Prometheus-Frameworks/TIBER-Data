import json
import re
from copy import deepcopy
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker, ValidationError

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

    with pytest.raises(ValidationError):
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


def test_identity_crosswalk_includes_known_seeded_mappings_unchanged() -> None:
    records = _load_artifact()["records"]
    rows_by_provider_id = {(row["provider"], row["provider_player_id"]): row for row in records}

    assert rows_by_provider_id[("sleeper", "6797")] == {
        "provider": "sleeper",
        "provider_player_id": "6797",
        "provider_canonical_id": "sleeper:6797",
        "tiber_player_id": "tiber-data-player-2025-justin-herbert",
        "player_name": "Justin Herbert",
        "position": "QB",
        "team": "LAC",
        "confidence": "exact",
        "match_method": "verified_manual_seed",
        "source": "operator_verified_management_smoke",
        "source_updated_at": "2026-06-08T00:00:00Z",
    }
    assert rows_by_provider_id[("sleeper", "9493")] == {
        "provider": "sleeper",
        "provider_player_id": "9493",
        "provider_canonical_id": "sleeper:9493",
        "tiber_player_id": "tiber-data-player-2025-puka-nacua",
        "player_name": "Puka Nacua",
        "position": "WR",
        "team": "LA",
        "confidence": "exact",
        "match_method": "verified_manual_seed",
        "source": "operator_verified_management_smoke",
        "source_updated_at": "2026-06-08T00:00:00Z",
    }
    assert rows_by_provider_id[("sleeper", "9509")] == {
        "provider": "sleeper",
        "provider_player_id": "9509",
        "provider_canonical_id": "sleeper:9509",
        "tiber_player_id": "tiber-data-player-2025-bijan-robinson",
        "player_name": "Bijan Robinson",
        "position": "RB",
        "team": "ATL",
        "confidence": "exact",
        "match_method": "verified_manual_seed",
        "source": "operator_verified_management_smoke",
        "source_updated_at": "2026-06-08T00:00:00Z",
    }


def test_identity_crosswalk_rejects_unsupported_provider() -> None:
    payload = _load_artifact()
    payload["records"][0]["provider"] = "espn"
    payload["records"][0]["provider_canonical_id"] = "espn:6797"

    with pytest.raises(ValidationError):
        _validator().validate(payload)
    with pytest.raises(ValueError, match="unsupported"):
        _load_module().validate_artifact(payload)


def test_identity_crosswalk_requires_provenance_source_fields() -> None:
    payload = _load_artifact()

    for row in payload["records"]:
        assert row["source"]
        assert row["source_updated_at"]
        assert row["confidence"] in {"exact", "high"}
        assert row["match_method"] == "verified_manual_seed"


def test_identity_crosswalk_preserves_producer_owned_artifact_shape() -> None:
    payload = _load_artifact()

    assert list(payload.keys()) == [
        "artifact_id",
        "schema_version",
        "generated_at",
        "supported_providers",
        "coverage",
        "record_count",
        "records",
    ]


def test_identity_crosswalk_includes_verified_management_seed_rows() -> None:
    rows_by_provider_id = {
        (row["provider"], row["provider_player_id"]): row for row in _load_artifact()["records"]
    }

    expected_new_rows = {
        "11573": "tiber-data-player-2025-frank-gore-jr",
        "11624": "tiber-data-player-2025-xavier-worthy",
        "11635": "tiber-data-player-2025-ladd-mcconkey",
        "11783": "tiber-data-player-2025-ryan-flournoy",
        "12487": "tiber-data-player-2025-terrance-ferguson",
        "12506": "tiber-data-player-2025-harold-fannin-jr",
        "12519": "tiber-data-player-2025-luther-burden-iii",
        "12530": "tiber-data-player-2025-travis-hunter",
        "2306": "tiber-data-player-2025-jameis-winston",
        "3198": "tiber-data-player-2025-derrick-henry",
        "4034": "tiber-data-player-2025-christian-mccaffrey",
        "4454": "tiber-data-player-2025-kendrick-bourne",
        "5844": "tiber-data-player-2025-t-j-hockenson",
        "5872": "tiber-data-player-2025-deebo-samuel-sr",
        "6011": "tiber-data-player-2025-gardner-minshew",
        "7021": "tiber-data-player-2025-rico-dowdle",
        "7527": "tiber-data-player-2025-mac-jones",
        "8117": "tiber-data-player-2025-jalen-tolbert",
        "8125": "tiber-data-player-2025-calvin-austin-iii",
        "8188": "tiber-data-player-2025-tyquan-thornton",
        "8800": "tiber-data-player-2025-malik-davis",
        "9494": "tiber-data-player-2025-marvin-mims-jr",
    }

    for provider_player_id, tiber_player_id in expected_new_rows.items():
        row = rows_by_provider_id[("sleeper", provider_player_id)]
        assert row["provider_canonical_id"] == f"sleeper:{provider_player_id}"
        assert row["tiber_player_id"] == tiber_player_id
        assert row["source"].startswith("TIBER_MANAGEMENT_SNAPSHOT_EXPORT")
        assert row["source_updated_at"] == "2026-06-09T00:00:00Z"


def test_verified_management_seed_rows_are_backed_by_existing_tiber_data_records() -> None:
    module = _load_module()
    source_backed = json.loads(
        (ROOT / "data/processed/evidence/roster_player_team_map_2025.source_backed.json").read_text(
            encoding="utf-8"
        )
    )
    source_record_keys = {
        (row["player_name"], row["position"])
        for row in source_backed["records"]
        if row["source_status"] == "source_verified"
    }

    for row in module.MANAGEMENT_SEED_VERIFIED_ROWS:
        assert (row["player_name"], row["position"]) in source_record_keys


def test_identity_crosswalk_omits_management_seed_rows_without_canonical_records() -> None:
    module = _load_module()
    promoted_provider_ids = {row["provider_player_id"] for row in _load_artifact()["records"]}

    assert module.MANAGEMENT_SEED_OMITTED_PROVIDER_IDS == {
        "13299": "no existing source-backed TIBER-Data player record for Nate Boerkircher",
        "13322": "no existing source-backed TIBER-Data player record for Sam Roush",
        "13408": "no existing source-backed TIBER-Data player record for Tanner Koziol",
        "13413": "no existing source-backed TIBER-Data player record for Cyrus Allen",
        "13414": "no existing source-backed TIBER-Data player record for Kaelon Black",
    }
    assert promoted_provider_ids.isdisjoint(module.MANAGEMENT_SEED_OMITTED_PROVIDER_IDS)

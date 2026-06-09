from __future__ import annotations

import argparse
import json
import re
from copy import deepcopy
from pathlib import Path
from typing import Any

ARTIFACT_ID = "TIBER_IDENTITY_CROSSWALK_V1"
SCHEMA_VERSION = "v1"
GENERATED_AT = "2026-06-09T00:00:00Z"
EXISTING_SEED_SOURCE_UPDATED_AT = "2026-06-08T00:00:00Z"
MANAGEMENT_SEED_SOURCE_UPDATED_AT = "2026-06-09T00:00:00Z"
MANAGEMENT_SEED_SOURCE = (
    "TIBER_MANAGEMENT_SNAPSHOT_EXPORT/TIBER_MANAGEMENT_IDENTITY_SEED_REPORT;"
    "data/processed/evidence/roster_player_team_map_2025.source_backed.json"
)
SUPPORTED_PROVIDERS = ("sleeper",)
OUTPUT_PATH = Path("exports/promoted/identity_crosswalk/tiber_identity_crosswalk_v1.json")
ISO_UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")

REQUIRED_ROW_FIELDS = (
    "provider",
    "provider_player_id",
    "provider_canonical_id",
    "tiber_player_id",
    "player_name",
    "position",
    "team",
    "confidence",
    "match_method",
    "source",
    "source_updated_at",
)

SEED_ROWS: tuple[dict[str, str], ...] = (
    {
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
        "source_updated_at": EXISTING_SEED_SOURCE_UPDATED_AT,
    },
    {
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
        "source_updated_at": EXISTING_SEED_SOURCE_UPDATED_AT,
    },
    {
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
        "source_updated_at": EXISTING_SEED_SOURCE_UPDATED_AT,
    },
)


def _management_seed_row(
    provider_player_id: str,
    tiber_player_id: str,
    player_name: str,
    position: str,
    team: str,
    confidence: str = "exact",
) -> dict[str, str]:
    return {
        "provider": "sleeper",
        "provider_player_id": provider_player_id,
        "provider_canonical_id": f"sleeper:{provider_player_id}",
        "tiber_player_id": tiber_player_id,
        "player_name": player_name,
        "position": position,
        "team": team,
        "confidence": confidence,
        "match_method": "verified_manual_seed",
        "source": MANAGEMENT_SEED_SOURCE,
        "source_updated_at": MANAGEMENT_SEED_SOURCE_UPDATED_AT,
    }


MANAGEMENT_SEED_VERIFIED_ROWS: tuple[dict[str, str], ...] = tuple(
    _management_seed_row(*row)
    for row in (
        (
            "11573",
            "tiber-data-player-2025-frank-gore-jr",
            "Frank Gore Jr.",
            "RB",
            "BUF",
            "high",
        ),
        ("11624", "tiber-data-player-2025-xavier-worthy", "Xavier Worthy", "WR", "KC"),
        ("11635", "tiber-data-player-2025-ladd-mcconkey", "Ladd McConkey", "WR", "LAC"),
        ("11783", "tiber-data-player-2025-ryan-flournoy", "Ryan Flournoy", "WR", "DAL"),
        (
            "12487",
            "tiber-data-player-2025-terrance-ferguson",
            "Terrance Ferguson",
            "TE",
            "LA",
        ),
        (
            "12506",
            "tiber-data-player-2025-harold-fannin-jr",
            "Harold Fannin Jr.",
            "TE",
            "CLE",
            "high",
        ),
        (
            "12519",
            "tiber-data-player-2025-luther-burden-iii",
            "Luther Burden III",
            "WR",
            "CHI",
            "high",
        ),
        ("12530", "tiber-data-player-2025-travis-hunter", "Travis Hunter", "WR", "JAX"),
        ("2306", "tiber-data-player-2025-jameis-winston", "Jameis Winston", "QB", "NYG"),
        ("3198", "tiber-data-player-2025-derrick-henry", "Derrick Henry", "RB", "BAL"),
        (
            "4034",
            "tiber-data-player-2025-christian-mccaffrey",
            "Christian McCaffrey",
            "RB",
            "SF",
        ),
        ("4454", "tiber-data-player-2025-kendrick-bourne", "Kendrick Bourne", "WR", "NE"),
        ("5844", "tiber-data-player-2025-t-j-hockenson", "T.J. Hockenson", "TE", "MIN"),
        (
            "5872",
            "tiber-data-player-2025-deebo-samuel-sr",
            "Deebo Samuel Sr.",
            "WR",
            "WAS",
            "high",
        ),
        ("6011", "tiber-data-player-2025-gardner-minshew", "Gardner Minshew", "QB", "KC"),
        ("7021", "tiber-data-player-2025-rico-dowdle", "Rico Dowdle", "RB", "CAR"),
        ("7527", "tiber-data-player-2025-mac-jones", "Mac Jones", "QB", "SF"),
        ("8117", "tiber-data-player-2025-jalen-tolbert", "Jalen Tolbert", "WR", "DAL"),
        (
            "8125",
            "tiber-data-player-2025-calvin-austin-iii",
            "Calvin Austin III",
            "WR",
            "PIT",
            "high",
        ),
        ("8188", "tiber-data-player-2025-tyquan-thornton", "Tyquan Thornton", "WR", "KC"),
        ("8800", "tiber-data-player-2025-malik-davis", "Malik Davis", "RB", "DAL"),
        (
            "9494",
            "tiber-data-player-2025-marvin-mims-jr",
            "Marvin Mims Jr.",
            "WR",
            "DEN",
            "high",
        ),
    )
)


MANAGEMENT_SEED_OMITTED_PROVIDER_IDS: dict[str, str] = {
    "13299": "no existing source-backed TIBER-Data player record for Nate Boerkircher",
    "13322": "no existing source-backed TIBER-Data player record for Sam Roush",
    "13408": "no existing source-backed TIBER-Data player record for Tanner Koziol",
    "13413": "no existing source-backed TIBER-Data player record for Cyrus Allen",
    "13414": "no existing source-backed TIBER-Data player record for Kaelon Black",
}


def _require_non_empty_string(value: Any, field: str, row_index: int) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"records[{row_index}].{field} must be a non-empty string")
    return value


def validate_row(row: dict[str, Any], row_index: int) -> None:
    missing = [field for field in REQUIRED_ROW_FIELDS if field not in row]
    if missing:
        raise ValueError(f"records[{row_index}] is missing required fields: {', '.join(missing)}")

    provider = _require_non_empty_string(row["provider"], "provider", row_index)
    provider_player_id = _require_non_empty_string(
        row["provider_player_id"], "provider_player_id", row_index
    )
    provider_canonical_id = _require_non_empty_string(
        row["provider_canonical_id"], "provider_canonical_id", row_index
    )

    if provider not in SUPPORTED_PROVIDERS:
        raise ValueError(
            f"records[{row_index}].provider {provider!r} is unsupported; "
            f"supported providers: {', '.join(SUPPORTED_PROVIDERS)}"
        )
    if provider_canonical_id != f"{provider}:{provider_player_id}":
        raise ValueError(
            f"records[{row_index}].provider_canonical_id must equal "
            f"{provider}:{provider_player_id}"
        )

    for field in REQUIRED_ROW_FIELDS:
        _require_non_empty_string(row[field], field, row_index)

    if row["confidence"] not in {"exact", "high", "provisional"}:
        raise ValueError(f"records[{row_index}].confidence has unsupported value")
    if row["match_method"] not in {"verified_manual_seed"}:
        raise ValueError(f"records[{row_index}].match_method has unsupported value")
    if not ISO_UTC_RE.match(row["source_updated_at"]):
        raise ValueError(f"records[{row_index}].source_updated_at must be UTC ISO timestamp")


def validate_artifact(artifact: dict[str, Any]) -> None:
    if artifact.get("artifact_id") != ARTIFACT_ID:
        raise ValueError(f"artifact_id must be {ARTIFACT_ID}")
    if artifact.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"schema_version must be {SCHEMA_VERSION}")
    if list(artifact.get("supported_providers", [])) != list(SUPPORTED_PROVIDERS):
        raise ValueError("supported_providers must be deterministic and limited to sleeper")

    records = artifact.get("records")
    if not isinstance(records, list) or not records:
        raise ValueError("records must be a non-empty list")
    if artifact.get("record_count") != len(records):
        raise ValueError("record_count must equal records length")

    provider_keys: dict[tuple[str, str], str] = {}
    tiber_keys: dict[tuple[str, str], str] = {}
    for index, row in enumerate(records):
        if not isinstance(row, dict):
            raise ValueError(f"records[{index}] must be an object")
        validate_row(row, index)
        provider_key = (row["provider"], row["provider_player_id"])
        canonical_key = (row["provider"], row["provider_canonical_id"])
        if provider_key in provider_keys:
            raise ValueError(
                f"duplicate provider mapping for {row['provider']}:{row['provider_player_id']}"
            )
        if canonical_key in provider_keys:
            raise ValueError(
                f"duplicate provider canonical mapping for {row['provider_canonical_id']}"
            )
        provider_keys[provider_key] = row["tiber_player_id"]
        provider_keys[canonical_key] = row["tiber_player_id"]

        tiber_key = (row["provider"], row["tiber_player_id"])
        previous_provider_id = tiber_keys.get(tiber_key)
        if previous_provider_id is not None and previous_provider_id != row["provider_player_id"]:
            raise ValueError(
                f"conflicting {row['provider']} mappings for TIBER player {row['tiber_player_id']}"
            )
        tiber_keys[tiber_key] = row["provider_player_id"]

    expected_order = sorted(
        records,
        key=lambda row: (row["provider"], row["provider_player_id"], row["tiber_player_id"]),
    )
    if records != expected_order:
        raise ValueError("records must be sorted by provider, provider_player_id, tiber_player_id")


def build_artifact() -> dict[str, Any]:
    records = sorted(
        (deepcopy(row) for row in (*SEED_ROWS, *MANAGEMENT_SEED_VERIFIED_ROWS)),
        key=lambda row: (row["provider"], row["provider_player_id"], row["tiber_player_id"]),
    )
    artifact: dict[str, Any] = {
        "artifact_id": ARTIFACT_ID,
        "schema_version": SCHEMA_VERSION,
        "generated_at": GENERATED_AT,
        "supported_providers": list(SUPPORTED_PROVIDERS),
        "coverage": "seeded_operator_verified_mappings_only_not_full_player_universe",
        "record_count": len(records),
        "records": records,
    }
    validate_artifact(artifact)
    return artifact


def write_artifact(output_path: Path = OUTPUT_PATH) -> Path:
    artifact = build_artifact()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(artifact, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Build TIBER_IDENTITY_CROSSWALK_V1.")
    parser.add_argument(
        "--check", action="store_true", help="Validate existing output without writing."
    )
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    args = parser.parse_args()

    if args.check:
        payload = json.loads(args.output.read_text(encoding="utf-8"))
        validate_artifact(payload)
        if payload != build_artifact():
            raise SystemExit(
                "Existing identity crosswalk differs from deterministic builder output"
            )
        print(f"Validated {args.output}")
        return

    path = write_artifact(args.output)
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()

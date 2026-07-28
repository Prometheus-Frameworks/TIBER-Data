"""Build the governed bounded 2026 population census v0 candidate.

This builder implements TIBER-Data #227.  It consumes exactly two source
cohorts, both by immutable git commit and content hash:

* every 2025 row in TIBER-Data's promoted player_season_coverage_v0; and
* every row in TIBER-Rookies' promoted 2026 rookie-transition profile v0.2.

It deliberately does not join the two namespaces by player name.  Historical
rows carry their source-verified TIBER-Data identifier; rookie rows retain the
TIBER-Rookies source identifier and an unresolved canonical identity state.
The output is a population census candidate, not a forecast, roster, active
player list, ranking, or promotion.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ARTIFACT_ID = "bounded_2026_population_census_v0"
SCHEMA_VERSION = "bounded_2026_population_census_v0.1.0"
STATUS = "candidate_governed_artifact_not_promoted"
SCOPE_ID = "historical_offense_plus_2026_rookies_v0"
DEFAULT_GENERATED_AT = "2026-07-27T14:00:00Z"
DEFAULT_OUTPUT_PATH = Path(
    "exports/candidates/population_census/bounded_2026_population_census_v0.json"
)

BOUNDED_OFFENSE_POSITIONS = {"QB", "RB", "WR", "TE"}
FREE_AGENT_TOKENS = {"FA", "FREE_AGENT", "FREE AGENT"}


@dataclass(frozen=True)
class SourcePin:
    source_artifact_key: str
    repository: str
    commit: str
    path: str
    sha256: str
    governance_path: str
    governance_sha256: str
    expected_included_rows: int


@dataclass(frozen=True)
class IndexedSourceRow:
    """A source row paired with its index in the unfiltered source array."""

    source_row_index: int
    row: dict[str, Any]


DATA_SOURCE_PIN = SourcePin(
    source_artifact_key="tiber_data_player_season_coverage_v0_2025",
    repository="Prometheus-Frameworks/TIBER-Data",
    commit="31c0c8e751816d262cf79ffef1a4ae9b6c9b70d5",
    path="exports/promoted/nfl/player_season_coverage_v0.json",
    sha256="d45f612b207085df00b4b080e4f55ce1abbd060dcbf30b0bee777ff833ddd8ac",
    governance_path="exports/promoted/nfl/PLAYER_SEASON_COVERAGE_V0_PROMOTION_MANIFEST.json",
    governance_sha256="5e9a382db0681e7a808a1d5fdf4334653cf2f0b26314c45425b333aa2024d154",
    expected_included_rows=610,
)

ROOKIE_SOURCE_PIN = SourcePin(
    source_artifact_key="tiber_rookies_transition_profile_v0_2_2026",
    repository="Prometheus-Frameworks/TIBER-Rookies",
    commit="a825431402f89f7ec4fe69e72de073ca4b301ea3",
    path="exports/promoted/rookie-transition-profile/2026_rookie_transition_profile_v0.json",
    sha256="c95b941c7855612daccfc2226fc51e0e34dbb2ebe8a2487596675d2522a22f37",
    governance_path="exports/promoted/rookie-transition-profile/2026_manifest.json",
    governance_sha256="0acf361c6d2d8cc6f684026481a5aa279e9f7fa718256fad78da0366d5804413",
    expected_included_rows=48,
)


class BuildFailure(RuntimeError):
    """Raised when an immutable source or row-preservation invariant fails."""


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def serialize_artifact(payload: dict[str, Any]) -> bytes:
    return (
        json.dumps(
            payload,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            indent=2,
        )
        + "\n"
    ).encode("utf-8")


def read_git_blob(repo_root: Path, commit: str, path: str) -> bytes:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "show", f"{commit}:{path}"],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise BuildFailure(f"cannot reproduce {path!r} at commit {commit} in {repo_root}: {detail}")
    return result.stdout


def verify_blob(raw: bytes, pin: SourcePin, *, role: str) -> None:
    actual = sha256_bytes(raw)
    if actual != pin.sha256:
        raise BuildFailure(
            f"{role} content hash mismatch for {pin.repository}@{pin.commit}:{pin.path}: "
            f"expected {pin.sha256}, got {actual}"
        )


def verify_governance_blob(raw: bytes, pin: SourcePin) -> dict[str, Any]:
    actual = sha256_bytes(raw)
    if actual != pin.governance_sha256:
        raise BuildFailure(
            f"governance evidence hash mismatch for "
            f"{pin.repository}@{pin.commit}:{pin.governance_path}: "
            f"expected {pin.governance_sha256}, got {actual}"
        )
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise BuildFailure(
            f"governance evidence is not valid JSON: {pin.governance_path}: {exc}"
        ) from exc
    if not isinstance(payload, dict):
        raise BuildFailure(f"governance evidence must be an object: {pin.governance_path}")
    return payload


def parse_source_json(raw: bytes, pin: SourcePin) -> dict[str, Any]:
    verify_blob(raw, pin, role="source artifact")
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise BuildFailure(f"source artifact is not valid JSON: {pin.path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise BuildFailure(f"source artifact must be a JSON object: {pin.path}")
    return payload


def _source_row_hash(row: dict[str, Any]) -> str:
    return sha256_bytes(canonical_json_bytes(row))


def _source_identity_key(
    source_artifact_key: str,
    row: dict[str, Any],
    *,
    source_kind: str,
) -> tuple[str, str | None]:
    player_id = row.get("player_id")
    source_player_id = player_id if isinstance(player_id, str) and player_id.strip() else None
    if source_kind == "historical":
        key_parts = [
            source_artifact_key,
            source_player_id or f"missing:{_source_row_hash(row)}",
            str(row.get("season")),
            str(row.get("season_type")),
        ]
    else:
        key_parts = [
            source_artifact_key,
            source_player_id or f"missing:{_source_row_hash(row)}",
            str(row.get("class_year")),
        ]
    return "\x1f".join(key_parts), source_player_id


def _population_row_id(identity_key: str, occurrence: int) -> str:
    identity_material = f"{SCOPE_ID}\x1f{identity_key}\x1f{occurrence}".encode("utf-8")
    return f"pop2026v0-{hashlib.sha256(identity_material).hexdigest()[:32]}"


def _position_state(value: Any) -> tuple[str | None, str]:
    if not isinstance(value, str) or not value.strip():
        return None, "source_position_missing"
    position = value.strip().upper()
    if position in BOUNDED_OFFENSE_POSITIONS:
        return position, "source_declared_bounded_offense_position"
    return position, "source_declared_outside_bounded_offense_position"


def _clean_string_values(values: list[Any]) -> list[str]:
    return sorted({value for value in values if isinstance(value, str) and value.strip()})


def _historical_team_assignment(row: dict[str, Any]) -> dict[str, Any]:
    raw_teams = row.get("teams")
    teams = _clean_string_values(raw_teams if isinstance(raw_teams, list) else [])
    primary = row.get("primary_team")
    primary_team = primary.strip() if isinstance(primary, str) and primary.strip() else None

    if primary_team and primary_team.upper() in FREE_AGENT_TOKENS:
        status = "source_explicit_free_agent"
    elif row.get("team_unknown") is True or (not teams and primary_team is None):
        status = "source_unknown"
    else:
        status = "source_backed_historical_team"

    if primary_team and primary_team not in teams:
        teams = sorted([*teams, primary_team])
    return {
        "teams": teams,
        "primary_team": primary_team,
        "team_status": status,
        "source_season": 2025,
    }


def _rookie_team_assignment(row: dict[str, Any]) -> dict[str, Any]:
    outcome = row.get("official_postdraft_outcome")
    value = outcome.get("value") if isinstance(outcome, dict) else None
    value = value if isinstance(value, dict) else {}
    source_status = value.get("status")
    team = value.get("nfl_team")
    primary_team = team.strip() if isinstance(team, str) and team.strip() else None

    if isinstance(source_status, str) and source_status.lower() == "unsigned":
        status = "source_explicit_unsigned"
    elif primary_team and primary_team.upper() in FREE_AGENT_TOKENS:
        status = "source_explicit_free_agent"
    elif source_status == "drafted" and primary_team:
        status = "source_backed_2026_drafted_team"
    elif source_status == "udfa_signed" and primary_team:
        status = "source_backed_2026_udfa_team"
    else:
        status = "source_unknown"

    return {
        "teams": [primary_team] if primary_team else [],
        "primary_team": primary_team,
        "team_status": status,
        "source_season": 2026,
    }


def _historical_availability(row: dict[str, Any], artifact: dict[str, Any]) -> dict[str, Any]:
    refs = row.get("source_refs")
    refs = refs if isinstance(refs, list) else []
    provenance_records = [
        {
            "evidence_field": "record_envelope",
            "value_status": "present",
            "source_type": "record_envelope",
            "source_name": None,
            "source_url": None,
            "observed_at": row.get("observed_at"),
            "source_updated_at": row.get("source_updated_at"),
            "last_verified_at": None,
            "confidence": None,
            "confidence_band": None,
            "notes": None,
        }
    ]
    for index, ref in enumerate(refs):
        if not isinstance(ref, dict):
            raise BuildFailure(f"historical source_refs[{index}] is not an object")
        provenance_records.append(
            {
                "evidence_field": f"source_refs[{index}]",
                "value_status": "present",
                "source_type": "historical_source_ref",
                "source_name": ref.get("source_name"),
                "source_url": ref.get("source_url"),
                "observed_at": ref.get("observed_at"),
                "source_updated_at": ref.get("source_updated_at"),
                "last_verified_at": None,
                "confidence": ref.get("confidence"),
                "confidence_band": None,
                "notes": ref.get("notes"),
            }
        )
    return {
        "source_artifact_generated_at": artifact.get("generated_at"),
        "provenance_records": provenance_records,
        "has_unresolved_timestamp": any(
            record["source_updated_at"] is None and record["last_verified_at"] is None
            for record in provenance_records
        ),
    }


def _rookie_availability(row: dict[str, Any], artifact: dict[str, Any]) -> dict[str, Any]:
    field_names = (
        "draft_capital",
        "age_at_entry",
        "athletic_testing",
        "college_production",
        "official_postdraft_outcome",
    )
    provenance_records: list[dict[str, Any]] = []
    for field_name in field_names:
        field = row.get(field_name)
        provenance = field.get("provenance") if isinstance(field, dict) else None
        if not isinstance(field, dict) or not isinstance(provenance, dict):
            raise BuildFailure(f"rookie field {field_name!r} is missing its provenance object")
        provenance_records.append(
            {
                "evidence_field": field_name,
                "value_status": ("present" if field.get("value") is not None else "unavailable"),
                "source_type": provenance.get("source_type"),
                "source_name": provenance.get("source_name"),
                "source_url": provenance.get("source_url"),
                "observed_at": None,
                "source_updated_at": None,
                "last_verified_at": provenance.get("last_verified_at"),
                "confidence": provenance.get("confidence"),
                "confidence_band": provenance.get("confidence_band"),
                "notes": provenance.get("notes"),
            }
        )
    return {
        "source_artifact_generated_at": artifact.get("generated_at"),
        "provenance_records": provenance_records,
        "has_unresolved_timestamp": any(
            record["last_verified_at"] is None for record in provenance_records
        ),
    }


def _prepare_source_rows(
    rows: list[IndexedSourceRow],
    *,
    pin: SourcePin,
    source_kind: str,
) -> list[tuple[dict[str, Any], str, str | None, str, int, int]]:
    prepared: list[tuple[dict[str, Any], str, str | None, str, int]] = []
    for indexed_row in rows:
        source_index = indexed_row.source_row_index
        row = indexed_row.row
        if not isinstance(row, dict):
            raise BuildFailure(
                f"{pin.source_artifact_key} source row {source_index} is not an object"
            )
        identity_key, source_player_id = _source_identity_key(
            pin.source_artifact_key,
            row,
            source_kind=source_kind,
        )
        prepared.append((row, identity_key, source_player_id, _source_row_hash(row), source_index))

    prepared.sort(key=lambda item: (item[1], item[3], item[4]))
    occurrences: Counter[str] = Counter()
    with_occurrence: list[tuple[dict[str, Any], str, str | None, str, int, int]] = []
    for row, identity_key, source_player_id, row_hash, source_index in prepared:
        occurrence = occurrences[identity_key]
        occurrences[identity_key] += 1
        with_occurrence.append(
            (row, identity_key, source_player_id, row_hash, source_index, occurrence)
        )
    return with_occurrence


def _historical_population_rows(
    source_rows: list[IndexedSourceRow],
    artifact: dict[str, Any],
    pin: SourcePin,
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for (
        row,
        identity_key,
        source_player_id,
        row_hash,
        source_index,
        occurrence,
    ) in _prepare_source_rows(source_rows, pin=pin, source_kind="historical"):
        position, position_status = _position_state(row.get("position"))
        source_identity_confidence = row.get("identity_confidence")
        if source_player_id and source_identity_confidence == "source_verified":
            canonical_player_id = source_player_id
            identity_status = "canonical_id_source_verified"
        elif source_player_id:
            canonical_player_id = None
            identity_status = "source_id_present_canonical_unresolved"
        else:
            canonical_player_id = None
            identity_status = "source_id_missing_canonical_unresolved"
        output.append(
            {
                "population_row_id": _population_row_id(identity_key, occurrence),
                "population_kind": "historical_offense_2025",
                "source_identity_ref": {
                    "source_artifact_key": pin.source_artifact_key,
                    "source_namespace": "tiber_data_player_id",
                    "source_player_id": source_player_id,
                    "source_identity_confidence": source_identity_confidence,
                    "source_row_key": identity_key.replace("\x1f", "|"),
                    "source_row_index": source_index,
                    "source_row_sha256": row_hash,
                },
                "canonical_player_id": canonical_player_id,
                "identity_status": identity_status,
                "player_name": row.get("player_name"),
                "position": position,
                "position_status": position_status,
                "history_status": "source_backed_2025_player_season",
                "team_assignment": _historical_team_assignment(row),
                "availability_evidence": _historical_availability(row, artifact),
            }
        )
    return output


def _rookie_population_rows(
    source_rows: list[IndexedSourceRow],
    artifact: dict[str, Any],
    pin: SourcePin,
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for (
        row,
        identity_key,
        source_player_id,
        row_hash,
        source_index,
        occurrence,
    ) in _prepare_source_rows(source_rows, pin=pin, source_kind="rookie"):
        position, position_status = _position_state(row.get("position"))
        identity_status = (
            "source_id_present_canonical_unresolved"
            if source_player_id
            else "source_id_missing_canonical_unresolved"
        )
        output.append(
            {
                "population_row_id": _population_row_id(identity_key, occurrence),
                "population_kind": "rookie_transition_2026",
                "source_identity_ref": {
                    "source_artifact_key": pin.source_artifact_key,
                    "source_namespace": "tiber_rookies_player_id",
                    "source_player_id": source_player_id,
                    "source_identity_confidence": None,
                    "source_row_key": identity_key.replace("\x1f", "|"),
                    "source_row_index": source_index,
                    "source_row_sha256": row_hash,
                },
                "canonical_player_id": None,
                "identity_status": identity_status,
                "player_name": row.get("player_name"),
                "position": position,
                "position_status": position_status,
                "history_status": "history_unresolved_no_exact_crosswalk",
                "team_assignment": _rookie_team_assignment(row),
                "availability_evidence": _rookie_availability(row, artifact),
            }
        )
    return output


def _count_rows(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts = Counter(str(row.get(key)) for row in rows)
    return dict(sorted(counts.items()))


def _mark_duplicate_canonical_conflicts(rows: list[dict[str, Any]]) -> None:
    by_canonical_id: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        canonical_player_id = row.get("canonical_player_id")
        if isinstance(canonical_player_id, str):
            by_canonical_id[canonical_player_id].append(row)
    for duplicate_rows in by_canonical_id.values():
        if len(duplicate_rows) > 1:
            for row in duplicate_rows:
                row["identity_status"] = "canonical_id_duplicate_conflict"


def _build_reconciliation(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_source_id: defaultdict[tuple[str, str], list[str]] = defaultdict(list)
    by_canonical_id: defaultdict[str, list[str]] = defaultdict(list)
    by_exact_identity: defaultdict[str, list[tuple[str, str]]] = defaultdict(list)
    by_row_hash: defaultdict[tuple[str, str], list[str]] = defaultdict(list)
    unresolved: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []

    for row in rows:
        row_id = row["population_row_id"]
        ref = row["source_identity_ref"]
        source_key = ref["source_artifact_key"]
        source_player_id = ref["source_player_id"]
        identity_status = row["identity_status"]

        if source_player_id is not None:
            by_source_id[(source_key, source_player_id)].append(row_id)
            by_exact_identity[source_player_id].append((source_key, row_id))
        canonical_player_id = row["canonical_player_id"]
        if canonical_player_id is not None:
            by_canonical_id[canonical_player_id].append(row_id)
        if "unresolved" in identity_status:
            item = {
                "population_row_id": row_id,
                "source_artifact_key": source_key,
                "source_player_id": source_player_id,
                "identity_status": identity_status,
            }
            unresolved.append(item)
            if source_player_id is None:
                missing.append(item)
        by_row_hash[(source_key, ref["source_row_sha256"])].append(row_id)

    duplicate_source_ids = [
        {
            "source_artifact_key": source_key,
            "source_player_id": source_player_id,
            "population_row_ids": sorted(row_ids),
        }
        for (source_key, source_player_id), row_ids in sorted(by_source_id.items())
        if len(row_ids) > 1
    ]
    duplicate_canonical_ids = [
        {
            "canonical_player_id": canonical_id,
            "population_row_ids": sorted(row_ids),
        }
        for canonical_id, row_ids in sorted(by_canonical_id.items())
        if len(row_ids) > 1
    ]
    cross_source_source_id_reuse: list[dict[str, Any]] = []
    for source_identity_value, matches in sorted(by_exact_identity.items()):
        source_keys = sorted({source_key for source_key, _ in matches})
        if len(source_keys) > 1:
            cross_source_source_id_reuse.append(
                {
                    "source_identity_value": source_identity_value,
                    "source_artifact_keys": source_keys,
                    "population_row_ids": sorted(row_id for _, row_id in matches),
                }
            )
    duplicate_row_hashes = [
        {
            "source_artifact_key": source_key,
            "source_row_sha256": row_hash,
            "population_row_ids": sorted(row_ids),
        }
        for (source_key, row_hash), row_ids in sorted(by_row_hash.items())
        if len(row_ids) > 1
    ]

    return {
        "duplicate_source_ids": duplicate_source_ids,
        "duplicate_resolved_canonical_ids": duplicate_canonical_ids,
        "unresolved_identity_rows": sorted(unresolved, key=lambda item: item["population_row_id"]),
        "missing_identity_rows": sorted(missing, key=lambda item: item["population_row_id"]),
        "cross_source_canonical_identity_reconciliation": {
            "status": "unevaluable_no_exact_cross_namespace_contract",
            "collision_groups": None,
            "items": [],
            "reason": (
                "TIBER-Data player IDs and TIBER-Rookies player IDs are distinct "
                "source namespaces; no exact governed cross-namespace identity "
                "contract is admitted by this census."
            ),
        },
        "cross_source_source_id_reuse": cross_source_source_id_reuse,
        "duplicate_source_row_hashes": duplicate_row_hashes,
        "counts": {
            "duplicate_source_id_groups": len(duplicate_source_ids),
            "duplicate_resolved_canonical_id_groups": len(duplicate_canonical_ids),
            "unresolved_identity_rows": len(unresolved),
            "missing_identity_rows": len(missing),
            "cross_source_canonical_identity_collision_groups": None,
            "cross_source_source_id_reuse_groups": len(cross_source_source_id_reuse),
            "duplicate_source_row_hash_groups": len(duplicate_row_hashes),
        },
    }


def _source_artifact_descriptor(
    *,
    pin: SourcePin,
    artifact: dict[str, Any],
    source_row_count: int,
    included_row_count: int,
    inclusion_rule: str,
    artifact_version: str,
    artifact_status: str,
) -> dict[str, Any]:
    return {
        "source_artifact_key": pin.source_artifact_key,
        "repository": pin.repository,
        "commit": pin.commit,
        "path": pin.path,
        "sha256": pin.sha256,
        "artifact_version": artifact_version,
        "artifact_status": artifact_status,
        "artifact_generated_at": artifact.get("generated_at"),
        "source_row_count": source_row_count,
        "included_row_count": included_row_count,
        "inclusion_rule": inclusion_rule,
        "governance_evidence": {
            "path": pin.governance_path,
            "sha256": pin.governance_sha256,
        },
    }


def _validate_source_envelopes(
    data_artifact: dict[str, Any],
    data_governance: dict[str, Any],
    rookie_artifact: dict[str, Any],
    rookie_governance: dict[str, Any],
    *,
    data_pin: SourcePin,
    rookie_pin: SourcePin,
) -> tuple[list[IndexedSourceRow], list[IndexedSourceRow]]:
    if data_artifact.get("artifact_id") != "player_season_coverage_v0":
        raise BuildFailure("TIBER-Data source artifact_id is not player_season_coverage_v0")
    if data_artifact.get("status") != "promoted_governed_artifact":
        raise BuildFailure("TIBER-Data player-season source is not promoted_governed_artifact")
    if data_artifact.get("spec_version") != "player_season_coverage_v0_promoted_v1":
        raise BuildFailure("TIBER-Data player-season source spec_version drifted")
    data_records = data_artifact.get("records")
    if not isinstance(data_records, list):
        raise BuildFailure("TIBER-Data player-season source records must be an array")
    for index, row in enumerate(data_records):
        if not isinstance(row, dict):
            raise BuildFailure(f"TIBER-Data player-season source row {index} is not an object")
    historical_rows = [
        IndexedSourceRow(source_row_index=index, row=row)
        for index, row in enumerate(data_records)
        if row.get("season") == 2025
    ]
    if len(historical_rows) != data_pin.expected_included_rows:
        raise BuildFailure(
            f"expected {data_pin.expected_included_rows} 2025 player-season rows, "
            f"found {len(historical_rows)}"
        )
    if data_governance.get("promoted_artifact_sha256") != data_pin.sha256:
        raise BuildFailure("TIBER-Data promotion manifest does not bind the pinned artifact hash")

    if rookie_artifact.get("artifact_type") != "rookie_transition_profile":
        raise BuildFailure("TIBER-Rookies source artifact_type is not rookie_transition_profile")
    if rookie_artifact.get("schema_version") != "rookie-transition-profile-v0.2.0":
        raise BuildFailure("TIBER-Rookies source schema_version drifted from v0.2.0")
    if rookie_artifact.get("season") != 2026:
        raise BuildFailure("TIBER-Rookies source season is not 2026")
    raw_rookie_rows = rookie_artifact.get("rows")
    if not isinstance(raw_rookie_rows, list):
        raise BuildFailure("TIBER-Rookies source rows must be an array")
    rookie_rows = [
        IndexedSourceRow(source_row_index=index, row=row)
        for index, row in enumerate(raw_rookie_rows)
        if isinstance(row, dict)
    ]
    if len(rookie_rows) != len(raw_rookie_rows):
        raise BuildFailure("TIBER-Rookies source contains a non-object row")
    if len(rookie_rows) != rookie_pin.expected_included_rows:
        raise BuildFailure(
            f"expected {rookie_pin.expected_included_rows} rookie rows, found {len(rookie_rows)}"
        )
    governed_output_hashes = {
        item.get("path"): item.get("sha256")
        for item in rookie_governance.get("output_files", [])
        if isinstance(item, dict)
    }
    if governed_output_hashes.get(rookie_pin.path) != rookie_pin.sha256:
        raise BuildFailure("TIBER-Rookies promoted manifest does not bind the pinned artifact hash")

    return historical_rows, rookie_rows


def build_artifact(
    *,
    data_raw: bytes,
    data_governance_raw: bytes,
    rookie_raw: bytes,
    rookie_governance_raw: bytes,
    data_pin: SourcePin = DATA_SOURCE_PIN,
    rookie_pin: SourcePin = ROOKIE_SOURCE_PIN,
    generated_at: str = DEFAULT_GENERATED_AT,
) -> dict[str, Any]:
    data_artifact = parse_source_json(data_raw, data_pin)
    rookie_artifact = parse_source_json(rookie_raw, rookie_pin)
    data_governance = verify_governance_blob(data_governance_raw, data_pin)
    rookie_governance = verify_governance_blob(rookie_governance_raw, rookie_pin)
    historical_rows, rookie_rows = _validate_source_envelopes(
        data_artifact,
        data_governance,
        rookie_artifact,
        rookie_governance,
        data_pin=data_pin,
        rookie_pin=rookie_pin,
    )

    population_rows = [
        *_historical_population_rows(historical_rows, data_artifact, data_pin),
        *_rookie_population_rows(rookie_rows, rookie_artifact, rookie_pin),
    ]
    _mark_duplicate_canonical_conflicts(population_rows)
    population_rows.sort(key=lambda row: row["population_row_id"])
    expected_total = data_pin.expected_included_rows + rookie_pin.expected_included_rows
    if len(population_rows) != expected_total:
        raise BuildFailure(
            f"row-preservation invariant failed: expected {expected_total}, "
            f"built {len(population_rows)}"
        )
    population_ids = [row["population_row_id"] for row in population_rows]
    if len(population_ids) != len(set(population_ids)):
        raise BuildFailure("population_row_id collision detected")

    source_artifacts = [
        _source_artifact_descriptor(
            pin=data_pin,
            artifact=data_artifact,
            source_row_count=len(data_artifact["records"]),
            included_row_count=len(historical_rows),
            inclusion_rule="include every record where season == 2025",
            artifact_version=str(data_artifact["spec_version"]),
            artifact_status=str(data_artifact["status"]),
        ),
        _source_artifact_descriptor(
            pin=rookie_pin,
            artifact=rookie_artifact,
            source_row_count=len(rookie_artifact["rows"]),
            included_row_count=len(rookie_rows),
            inclusion_rule="include every row in the promoted 2026 v0.2 artifact",
            artifact_version=str(rookie_artifact["schema_version"]),
            artifact_status="promoted_governed_source_artifact",
        ),
    ]

    coverage_summary = {
        "by_source": _count_rows(
            [
                {
                    "source": row["source_identity_ref"]["source_artifact_key"],
                }
                for row in population_rows
            ],
            "source",
        ),
        "by_population_kind": _count_rows(population_rows, "population_kind"),
        "by_identity_status": _count_rows(population_rows, "identity_status"),
        "by_position_status": _count_rows(population_rows, "position_status"),
        "by_team_status": _count_rows(
            [{"team_status": row["team_assignment"]["team_status"]} for row in population_rows],
            "team_status",
        ),
        "by_history_status": _count_rows(population_rows, "history_status"),
    }

    return {
        "artifact_id": ARTIFACT_ID,
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "generated_at": generated_at,
        "scope_id": SCOPE_ID,
        "scope_definition": {
            "description": (
                "Bounded union of every 2025 player row in TIBER-Data's promoted "
                "player_season_coverage_v0 and every row in TIBER-Rookies' promoted "
                "2026 rookie-transition profile v0.2."
            ),
            "included_cohorts": [
                "TIBER-Data promoted player_season_coverage_v0 rows where season == 2025",
                "TIBER-Rookies promoted 2026 rookie-transition profile v0.2 rows",
            ],
            "outside_scope": [
                "players absent from both declared source cohorts",
                "a complete current or active NFL player universe",
                "IDP full-universe coverage",
                "kickers, punters, long snappers, and other non-declared domains",
                "active, inactive, injured, rostered, or free-agent inference beyond source fields",
                "Forecast model admission, scoring, ranking, advice, or promotion",
            ],
            "full_universe_claim": False,
            "idp_full_universe_available": False,
            "activity_inference_performed": False,
            "identity_join_policy": "exact_source_identity_only_no_cross_namespace_join",
        },
        "source_artifacts": source_artifacts,
        "population_row_count": len(population_rows),
        "population_rows": population_rows,
        "coverage_summary": coverage_summary,
        "reconciliation": _build_reconciliation(population_rows),
        "limitations": [
            (
                "This is a bounded two-cohort census, not a complete active NFL "
                "or fantasy-player universe."
            ),
            (
                "The 2025 historical cohort contains source-backed player-season "
                "rows, not 2026 roster or activity assertions."
            ),
            (
                "Rookie source identifiers are preserved but remain canonically "
                "unresolved because no exact governed cross-namespace identity "
                "contract is used."
            ),
            "IDP full-universe coverage is unavailable and outside this census.",
            (
                "Source timestamps and null timestamp states are preserved as "
                "evidence; this artifact does not certify a Forecast cutoff."
            ),
            "No fuzzy, display-name, alias, or heuristic identity join is performed.",
        ],
        "consumer_safety": {
            "allowed": [
                "inspect the bounded declared population and its source provenance",
                "perform a separate downstream exact-cutoff admission review",
            ],
            "not_authorized": [
                "claim complete or current-active player coverage",
                "treat unresolved rookie source IDs as canonical TIBER IDs",
                "execute or authorize a Forecast run",
                "emit rankings, advice, projections, promotion, or production activation",
            ],
        },
    }


def build_from_git(
    *,
    data_repo_root: Path,
    rookie_repo_root: Path,
    generated_at: str = DEFAULT_GENERATED_AT,
) -> dict[str, Any]:
    return build_artifact(
        data_raw=read_git_blob(data_repo_root, DATA_SOURCE_PIN.commit, DATA_SOURCE_PIN.path),
        data_governance_raw=read_git_blob(
            data_repo_root,
            DATA_SOURCE_PIN.commit,
            DATA_SOURCE_PIN.governance_path,
        ),
        rookie_raw=read_git_blob(
            rookie_repo_root,
            ROOKIE_SOURCE_PIN.commit,
            ROOKIE_SOURCE_PIN.path,
        ),
        rookie_governance_raw=read_git_blob(
            rookie_repo_root,
            ROOKIE_SOURCE_PIN.commit,
            ROOKIE_SOURCE_PIN.governance_path,
        ),
        generated_at=generated_at,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-repo-root",
        type=Path,
        default=Path("."),
        help="TIBER-Data git worktree containing the pinned commit (default: current directory)",
    )
    parser.add_argument(
        "--rookie-repo-root",
        type=Path,
        required=True,
        help="Read-only TIBER-Rookies git worktree containing the pinned commit",
    )
    parser.add_argument(
        "--generated-at",
        default=DEFAULT_GENERATED_AT,
        help=f"Deterministic artifact timestamp (default: {DEFAULT_GENERATED_AT})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help=f"Candidate output path (default: {DEFAULT_OUTPUT_PATH})",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = build_from_git(
        data_repo_root=args.data_repo_root.resolve(),
        rookie_repo_root=args.rookie_repo_root.resolve(),
        generated_at=args.generated_at,
    )
    output_path = args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    raw = serialize_artifact(payload)
    output_path.write_bytes(raw)
    print(
        f"Wrote {output_path} ({payload['population_row_count']} rows, sha256={sha256_bytes(raw)})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

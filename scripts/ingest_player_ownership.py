from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
PLAYER_OWNERSHIP_SCHEMA_PATH = ROOT / "schemas/player_ownership_v0.schema.json"
PLAYER_OWNERSHIP_EVENT_SCHEMA_PATH = ROOT / "schemas/player_ownership_change_event_v0.schema.json"
DEFAULT_EVENTS_DIR = ROOT / "exports/promoted/player_ownership/events"
DEFAULT_MANIFEST_PATH = (
    ROOT / "exports/promoted/player_ownership/manifests/player_ownership_ingestion_runs.json"
)

OWNERSHIP_CONFIDENCE_VALUES = {
    "source_verified",
    "multi_source_verified",
    "provisional",
    "unverified",
}
VERIFIED_CONFIDENCE_VALUES = {"source_verified", "multi_source_verified"}
TEAM_FIELDS = ("current_team_id", "current_team_abbr", "current_team_name")
DIFF_FIELDS = (*TEAM_FIELDS, "ownership_status", "football_level")
RFC3339_UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _run_id(started_at: str) -> str:
    compact = started_at.replace("-", "").replace(":", "")
    return f"player-ownership-ingest-{compact}"


def _is_rfc3339_utc_datetime(value: object) -> bool:
    if not isinstance(value, str):
        return True
    if not RFC3339_UTC_RE.match(value):
        return False
    try:
        datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return False
    return True


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _clean_string(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        cleaned = " ".join(value.strip().split())
        return cleaned or None
    return str(value)


def _upper_string(value: Any) -> str | None:
    cleaned = _clean_string(value)
    return cleaned.upper() if cleaned is not None else None


def _lower_id(value: Any) -> str | None:
    cleaned = _clean_string(value)
    return cleaned.lower() if cleaned is not None else None


def _ownership_status(value: Any) -> str:
    cleaned = _clean_string(value)
    if cleaned is None:
        return "unknown"
    return cleaned.lower().replace(" ", "_").replace("-", "_")


def _ownership_confidence(row: dict[str, Any], source_meta: dict[str, Any]) -> str:
    value = _clean_string(
        row.get("ownership_confidence")
        or row.get("confidence")
        or source_meta.get("ownership_confidence")
        or source_meta.get("confidence")
    )
    if value in OWNERSHIP_CONFIDENCE_VALUES:
        return value
    return "unverified"


def _source_ref(
    row: dict[str, Any],
    source_meta: dict[str, Any],
    source_path: Path,
) -> dict[str, Any]:
    return {
        "source_name": _clean_string(
            row.get("source_name") or source_meta.get("source_name") or source_path.stem
        ),
        "source_url": _clean_string(row.get("source_url") or source_meta.get("source_url")),
        "observed_at": _clean_string(
            row.get("observed_at") or source_meta.get("observed_at") or row.get("last_verified_at")
        ),
        "source_updated_at": _clean_string(
            row.get("source_updated_at") or source_meta.get("source_updated_at")
        ),
        "confidence": _clean_string(
            row.get("source_confidence") or source_meta.get("source_confidence")
        ),
        "notes": _clean_string(row.get("notes") or source_meta.get("notes")),
    }


def _load_source(path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    payload = _load_json(path)
    if isinstance(payload, list):
        return payload, {}
    if not isinstance(payload, dict):
        raise ValueError(f"Source payload must be an object or array: {path}")

    records = payload.get("players", payload.get("records"))
    if not isinstance(records, list):
        raise ValueError(f"Source payload must include a players or records array: {path}")
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise ValueError(f"Source record at index {index} must be an object: {path}")

    source_meta = {
        key: value
        for key, value in payload.items()
        if key not in {"players", "records"} and not isinstance(value, (dict, list))
    }
    return records, source_meta


def normalize_source_player(
    row: dict[str, Any],
    *,
    source_meta: dict[str, Any],
    source_path: Path,
) -> dict[str, Any]:
    observed_at = _clean_string(
        row.get("last_verified_at") or row.get("observed_at") or source_meta.get("observed_at")
    )
    return {
        "player_id": _lower_id(row.get("player_id")),
        "player_name": _clean_string(
            row.get("player_name") or row.get("full_name") or row.get("name")
        ),
        "position": _upper_string(row.get("position")),
        "football_level": _upper_string(row.get("football_level")),
        "current_team_id": _lower_id(row.get("current_team_id") or row.get("team_id")),
        "current_team_abbr": _upper_string(
            row.get("current_team_abbr") or row.get("team_abbr") or row.get("team")
        ),
        "current_team_name": _clean_string(row.get("current_team_name") or row.get("team_name")),
        "ownership_status": _ownership_status(row.get("ownership_status") or row.get("status")),
        "valid_from": _clean_string(row.get("valid_from")),
        "valid_to": _clean_string(row.get("valid_to")),
        "last_verified_at": observed_at,
        "confidence": _ownership_confidence(row, source_meta),
        "source_refs": [_source_ref(row, source_meta, source_path)],
    }


def _validator(schema_path: Path) -> Draft202012Validator:
    schema = _load_json(schema_path)
    format_checker = FormatChecker()
    format_checker.checks("date-time")(_is_rfc3339_utc_datetime)
    return Draft202012Validator(schema, format_checker=format_checker)


def _format_path(parts: Any) -> str:
    path = [str(part) for part in parts]
    return ".".join(path) if path else "$"


def _validate_payload(
    payload: dict[str, Any],
    *,
    scope: str,
) -> tuple[list[dict[str, str]], set[int]]:
    errors: list[dict[str, str]] = []
    invalid_source_indexes: set[int] = set()
    validator = _validator(PLAYER_OWNERSHIP_SCHEMA_PATH)

    for error in sorted(validator.iter_errors(payload), key=lambda item: list(item.absolute_path)):
        path_parts = list(error.absolute_path)
        if len(path_parts) >= 2 and path_parts[0] == "players" and isinstance(path_parts[1], int):
            invalid_source_indexes.add(path_parts[1])
        errors.append(
            {
                "scope": scope,
                "path": _format_path(path_parts),
                "message": error.message,
            }
        )
    return errors, invalid_source_indexes


def _validate_events(events: list[dict[str, Any]]) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    validator = _validator(PLAYER_OWNERSHIP_EVENT_SCHEMA_PATH)

    for index, event in enumerate(events):
        event_errors = sorted(
            validator.iter_errors(event),
            key=lambda item: list(item.absolute_path),
        )
        for error in event_errors:
            path_parts = ["events", index, *list(error.absolute_path)]
            errors.append(
                {
                    "scope": "change_events",
                    "path": _format_path(path_parts),
                    "message": error.message,
                }
            )
    return errors


def _identity_key(record: dict[str, Any]) -> str | None:
    player_id = record.get("player_id")
    return str(player_id) if player_id else None


def _summary_player(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "player_id": record.get("player_id"),
        "player_name": record.get("player_name"),
        "position": record.get("position"),
        "football_level": record.get("football_level"),
        "current_team_id": record.get("current_team_id"),
        "current_team_abbr": record.get("current_team_abbr"),
        "current_team_name": record.get("current_team_name"),
        "ownership_status": record.get("ownership_status"),
        "source_refs": record.get("source_refs", []),
    }


def _changed_fields(records: list[dict[str, Any]]) -> list[str]:
    changed: list[str] = []
    for field in DIFF_FIELDS:
        values = {record.get(field) for record in records}
        if len(values) > 1:
            changed.append(field)
    return changed


def _field_snapshot(record: dict[str, Any], fields: tuple[str, ...]) -> dict[str, Any]:
    return {field: record.get(field) for field in fields}


def _date_part(value: object) -> str | None:
    if isinstance(value, str) and _is_rfc3339_utc_datetime(value):
        return value[:10]
    return None


def _effective_date(record: dict[str, Any]) -> str | None:
    source_refs = record.get("source_refs", [])
    source_observed_at = None
    if source_refs and isinstance(source_refs[0], dict):
        source_observed_at = source_refs[0].get("observed_at")
    return (
        _date_part(record.get("valid_from"))
        or _date_part(record.get("last_verified_at"))
        or _date_part(source_observed_at)
    )


def _verification_status(confidence: object) -> str:
    if confidence in VERIFIED_CONFIDENCE_VALUES:
        return "verified"
    if confidence == "provisional":
        return "provisional"
    return "unverified"


def _change_entry(
    *,
    previous: dict[str, Any],
    current: dict[str, Any],
    fields: tuple[str, ...],
) -> dict[str, Any]:
    return {
        "player_id": current.get("player_id") or previous.get("player_id"),
        "player_name": current.get("player_name") or previous.get("player_name"),
        "position": current.get("position") or previous.get("position"),
        "previous": _field_snapshot(previous, fields),
        "current": _field_snapshot(current, fields),
        "previous_team": _field_snapshot(previous, TEAM_FIELDS),
        "current_team": _field_snapshot(current, TEAM_FIELDS),
        "confidence": current.get("confidence"),
        "verification_status": _verification_status(current.get("confidence")),
        "effective_date": _effective_date(current),
        "source_refs": current.get("source_refs", []),
    }


def _missing_entry(previous: dict[str, Any]) -> dict[str, Any]:
    return {
        "player_id": previous.get("player_id"),
        "player_name": previous.get("player_name"),
        "position": previous.get("position"),
        "previous": _field_snapshot(previous, DIFF_FIELDS),
        "reason": "missing_source_row_is_uncertainty_not_release",
    }


def _diff_records(
    *,
    previous_players: list[dict[str, Any]],
    normalized_players: list[dict[str, Any]],
    invalid_source_indexes: set[int],
    previous_is_valid: bool,
) -> dict[str, Any]:
    previous_by_id = {
        str(player["player_id"]): player for player in previous_players if player.get("player_id")
    }
    all_source_ids = {
        str(player["player_id"]) for player in normalized_players if player.get("player_id")
    }

    unresolved = [
        {
            "player_name": player.get("player_name"),
            "position": player.get("position"),
            "reason": "missing_player_id",
            "source_refs": player.get("source_refs", []),
        }
        for index, player in enumerate(normalized_players)
        if index not in invalid_source_indexes and not player.get("player_id")
    ]

    if not previous_is_valid:
        return {
            "unchanged": [],
            "new_players": [],
            "team_changes": [],
            "status_changes": [],
            "football_level_changes": [],
            "identity_unresolved": unresolved,
            "source_conflicts": [],
            "removed_or_missing_from_source": [],
        }

    grouped: dict[str, list[tuple[int, dict[str, Any]]]] = defaultdict(list)
    for index, player in enumerate(normalized_players):
        key = _identity_key(player)
        if key and index not in invalid_source_indexes:
            grouped[key].append((index, player))

    source_conflicts: list[dict[str, Any]] = []
    comparable_by_id: dict[str, dict[str, Any]] = {}
    for player_id, indexed_records in grouped.items():
        records = [record for _, record in indexed_records]
        changed_fields = _changed_fields(records)
        if changed_fields:
            source_conflicts.append(
                {
                    "player_id": player_id,
                    "player_name": records[0].get("player_name"),
                    "conflict_fields": changed_fields,
                    "source_records": [_summary_player(record) for record in records],
                }
            )
            continue
        comparable_by_id[player_id] = records[0]

    unchanged: list[dict[str, Any]] = []
    new_players: list[dict[str, Any]] = []
    team_changes: list[dict[str, Any]] = []
    status_changes: list[dict[str, Any]] = []
    football_level_changes: list[dict[str, Any]] = []

    for player_id, current in sorted(comparable_by_id.items()):
        previous = previous_by_id.get(player_id)
        if previous is None:
            new_players.append(_summary_player(current))
            continue

        changed = False
        if any(previous.get(field) != current.get(field) for field in TEAM_FIELDS):
            team_changes.append(
                _change_entry(previous=previous, current=current, fields=TEAM_FIELDS)
            )
            changed = True
        if previous.get("ownership_status") != current.get("ownership_status"):
            status_changes.append(
                _change_entry(previous=previous, current=current, fields=("ownership_status",))
            )
            changed = True
        if previous.get("football_level") != current.get("football_level"):
            football_level_changes.append(
                _change_entry(previous=previous, current=current, fields=("football_level",))
            )
            changed = True
        if not changed:
            unchanged.append(_summary_player(current))

    removed_or_missing = [
        _missing_entry(previous)
        for player_id, previous in sorted(previous_by_id.items())
        if player_id not in all_source_ids
    ]

    return {
        "unchanged": unchanged,
        "new_players": new_players,
        "team_changes": team_changes,
        "status_changes": status_changes,
        "football_level_changes": football_level_changes,
        "identity_unresolved": unresolved,
        "source_conflicts": source_conflicts,
        "removed_or_missing_from_source": removed_or_missing,
    }


def _change_count(diffs: dict[str, Any]) -> int:
    return (
        len(diffs["new_players"])
        + len(diffs["team_changes"])
        + len(diffs["status_changes"])
        + len(diffs["football_level_changes"])
    )


def _verified_change_events(
    *,
    diffs: dict[str, Any],
    detected_at: str,
) -> tuple[list[dict[str, Any]], list[str]]:
    events: list[dict[str, Any]] = []
    blocked_reasons: list[str] = []

    promotable_changes = [
        ("team_change", change) for change in diffs["team_changes"]
    ] + [("status_change", change) for change in diffs["status_changes"]]

    for event_type, change in promotable_changes:
        if change.get("confidence") not in VERIFIED_CONFIDENCE_VALUES:
            blocked_reasons.append("change_not_verified")
            continue
        effective_date = change.get("effective_date")
        if not effective_date:
            blocked_reasons.append("missing_effective_date")
            continue

        previous_team = change.get("previous_team", {})
        current_team = change.get("current_team", {})
        event_suffix = ""
        if event_type == "status_change":
            current_status = change.get("current", {}).get("ownership_status")
            event_suffix = f"-{current_status}" if current_status else ""

        events.append(
            {
                "event_id": (
                    f"player-{event_type.replace('_', '-')}-"
                    f"{change.get('player_id')}-{effective_date}{event_suffix}"
                ),
                "event_type": event_type,
                "player_id": change.get("player_id"),
                "player_name": change.get("player_name"),
                "position": change.get("position"),
                "from_team_id": previous_team.get("current_team_id"),
                "from_team_abbr": previous_team.get("current_team_abbr"),
                "from_team_name": previous_team.get("current_team_name"),
                "to_team_id": current_team.get("current_team_id"),
                "to_team_abbr": current_team.get("current_team_abbr"),
                "to_team_name": current_team.get("current_team_name"),
                "detected_at": detected_at,
                "effective_date": effective_date,
                "verification_status": change.get("verification_status", "verified"),
                "confidence": change.get("confidence"),
                "source_refs": change.get("source_refs", []),
            }
        )

    if diffs["new_players"]:
        blocked_reasons.append("new_player_requires_operator_review")
    if diffs["football_level_changes"]:
        blocked_reasons.append("football_level_change_requires_operator_review")

    return events, sorted(set(blocked_reasons))


def _validation_block_reasons(validation_errors: list[dict[str, str]]) -> list[str]:
    reasons: set[str] = set()
    for error in validation_errors:
        path = error.get("path", "")
        message = error.get("message", "")
        timestamp_fields = ("valid_from", "valid_to", "last_verified_at", "observed_at")
        if any(field in path for field in timestamp_fields):
            reasons.add("invalid_timestamp")
        elif "ownership_status" in path:
            reasons.add("invalid_status")
        elif "source_refs" in path:
            reasons.add("missing_required_source_ref")
        else:
            reasons.add("schema_validation_failed")
        if "date-time" in message or "date" in message:
            reasons.add("invalid_timestamp")
    return sorted(reasons)


def _promotion_block_reasons(
    *,
    validation_errors: list[dict[str, str]],
    diffs: dict[str, Any],
    event_block_reasons: list[str],
) -> list[str]:
    reasons = set(_validation_block_reasons(validation_errors))
    reasons.update(event_block_reasons)
    if diffs["identity_unresolved"]:
        reasons.add("identity_unresolved")
    if diffs["source_conflicts"]:
        reasons.add("source_conflict")
    return sorted(reasons)


def _player_sort_key(record: dict[str, Any]) -> tuple[str, str]:
    return (str(record.get("player_id") or ""), str(record.get("player_name") or ""))


def _source_conflict_ids(diffs: dict[str, Any]) -> set[str]:
    return {
        str(conflict["player_id"])
        for conflict in diffs["source_conflicts"]
        if conflict.get("player_id")
    }


def _latest_payload_for_promotion(
    *,
    previous_payload: dict[str, Any],
    normalized_players: list[dict[str, Any]],
    invalid_source_indexes: set[int],
    diffs: dict[str, Any],
    generated_at: str,
) -> dict[str, Any]:
    previous_players = (
        previous_payload.get("players", []) if isinstance(previous_payload, dict) else []
    )
    merged_by_id = {
        str(player["player_id"]): player for player in previous_players if player.get("player_id")
    }
    conflict_ids = _source_conflict_ids(diffs)

    for index, player in enumerate(normalized_players):
        player_id = player.get("player_id")
        if not player_id or index in invalid_source_indexes or str(player_id) in conflict_ids:
            continue
        merged_by_id[str(player_id)] = player

    return {
        "contract_version": "player_ownership_v0",
        "generated_at": generated_at,
        "players": sorted(merged_by_id.values(), key=_player_sort_key),
    }


def _relative_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def _json_text(payload: dict[str, Any]) -> str:
    return f"{json.dumps(payload, indent=2)}\n"


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_name(f".{path.name}.tmp")
    temporary_path.write_text(text, encoding="utf-8")
    temporary_path.replace(path)


def _event_ledger_path(events_dir: Path, detected_at: str) -> Path:
    return events_dir / f"player_ownership_events_{detected_at[:4]}.jsonl"


def _append_event_records(path: Path, events: list[dict[str, Any]]) -> None:
    existing_text = path.read_text(encoding="utf-8") if path.exists() else ""
    event_lines = [json.dumps(event, sort_keys=True, separators=(",", ":")) for event in events]
    combined = existing_text
    if combined and not combined.endswith("\n"):
        combined += "\n"
    combined += "\n".join(event_lines)
    if combined and not combined.endswith("\n"):
        combined += "\n"
    _atomic_write_text(path, combined)


def _base_report(
    *,
    source_path: Path,
    previous_path: Path,
    mode: str,
    started_at: str | None = None,
    completed_at: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]], set[int], dict[str, Any]]:
    started_at = started_at or _utc_now()
    source_records, source_meta = _load_source(source_path)
    normalized_players = [
        normalize_source_player(record, source_meta=source_meta, source_path=source_path)
        for record in source_records
    ]
    normalized_payload = {
        "contract_version": "player_ownership_v0",
        "generated_at": started_at,
        "players": normalized_players,
    }

    previous_payload = _load_json(previous_path)
    previous_players = (
        previous_payload.get("players", []) if isinstance(previous_payload, dict) else []
    )

    source_validation_errors, invalid_source_indexes = _validate_payload(
        normalized_payload,
        scope="normalized_source",
    )
    previous_validation_errors, _ = _validate_payload(previous_payload, scope="previous_latest")
    validation_errors = [*source_validation_errors, *previous_validation_errors]

    diffs = _diff_records(
        previous_players=previous_players,
        normalized_players=normalized_players,
        invalid_source_indexes=invalid_source_indexes,
        previous_is_valid=not previous_validation_errors,
    )

    completed_at = completed_at or _utc_now()
    report = {
        "run_id": _run_id(started_at),
        "started_at": started_at,
        "completed_at": completed_at,
        "mode": mode,
        "source_count": 1,
        "players_checked": len(source_records),
        "normalized_record_count": len(normalized_players),
        "skipped_invalid_source_count": len(invalid_source_indexes),
        "unchanged_count": len(diffs["unchanged"]),
        "new_player_count": len(diffs["new_players"]),
        "new_players": diffs["new_players"],
        "team_change_count": len(diffs["team_changes"]),
        "team_changes": diffs["team_changes"],
        "status_change_count": len(diffs["status_changes"]),
        "status_changes": diffs["status_changes"],
        "football_level_change_count": len(diffs["football_level_changes"]),
        "football_level_changes": diffs["football_level_changes"],
        "changes_detected": _change_count(diffs),
        "unresolved_identity_count": len(diffs["identity_unresolved"]),
        "identity_unresolved": diffs["identity_unresolved"],
        "source_conflict_count": len(diffs["source_conflicts"]),
        "source_conflicts": diffs["source_conflicts"],
        "removed_or_missing_from_source_count": len(diffs["removed_or_missing_from_source"]),
        "removed_or_missing_from_source": diffs["removed_or_missing_from_source"],
        "validation_error_count": len(validation_errors),
        "validation_errors": validation_errors,
        "would_write_latest_artifact": False,
        "would_append_change_events": False,
    }
    return report, previous_payload, normalized_players, invalid_source_indexes, diffs


def build_dry_run_report(
    *,
    source_path: Path,
    previous_path: Path,
    started_at: str | None = None,
    completed_at: str | None = None,
) -> dict[str, Any]:
    report, _, _, _, _ = _base_report(
        source_path=source_path,
        previous_path=previous_path,
        mode="dry_run",
        started_at=started_at,
        completed_at=completed_at,
    )
    return report


def run_player_ownership_ingestion(
    *,
    source_path: Path,
    previous_path: Path,
    mode: str = "dry_run",
    latest_output_path: Path | None = None,
    events_dir: Path | None = None,
    manifest_path: Path | None = None,
    started_at: str | None = None,
    completed_at: str | None = None,
) -> dict[str, Any]:
    if mode == "dry_run":
        return build_dry_run_report(
            source_path=source_path,
            previous_path=previous_path,
            started_at=started_at,
            completed_at=completed_at,
        )
    if mode != "write":
        raise ValueError(f"Unsupported ingestion mode: {mode}")

    latest_output_path = latest_output_path or previous_path
    events_dir = events_dir or DEFAULT_EVENTS_DIR
    manifest_path = manifest_path or DEFAULT_MANIFEST_PATH

    report, previous_payload, normalized_players, invalid_source_indexes, diffs = _base_report(
        source_path=source_path,
        previous_path=previous_path,
        mode="write",
        started_at=started_at,
        completed_at=completed_at,
    )

    events, event_block_reasons = _verified_change_events(
        diffs=diffs,
        detected_at=report["started_at"],
    )
    event_validation_errors = _validate_events(events)
    if event_validation_errors:
        report["validation_errors"].extend(event_validation_errors)
        report["validation_error_count"] = len(report["validation_errors"])

    latest_payload = _latest_payload_for_promotion(
        previous_payload=previous_payload,
        normalized_players=normalized_players,
        invalid_source_indexes=invalid_source_indexes,
        diffs=diffs,
        generated_at=report["started_at"],
    )
    latest_validation_errors: list[dict[str, str]] = []
    if report["changes_detected"]:
        latest_validation_errors, _ = _validate_payload(latest_payload, scope="promotion_latest")
        if latest_validation_errors:
            report["validation_errors"].extend(latest_validation_errors)
            report["validation_error_count"] = len(report["validation_errors"])

    blocked_reasons = _promotion_block_reasons(
        validation_errors=report["validation_errors"],
        diffs=diffs,
        event_block_reasons=event_block_reasons,
    )

    event_ledger_path = _event_ledger_path(events_dir, report["started_at"])
    report.update(
        {
            "latest_artifact_written": False,
            "events_appended": 0,
            "manifest_written": True,
            "blocked_reasons": blocked_reasons,
            "promotion_status": "blocked" if blocked_reasons else "no_changes",
            "artifact_written": False,
            "artifact_paths": {
                "latest": _relative_path(latest_output_path),
                "events": _relative_path(event_ledger_path),
                "manifest": _relative_path(manifest_path),
            },
        }
    )

    if report["changes_detected"] and not blocked_reasons:
        report["promotion_status"] = "promoted"
        report["latest_artifact_written"] = True
        report["artifact_written"] = True
        report["events_appended"] = len(events)
        _atomic_write_text(latest_output_path, _json_text(latest_payload))
        if events:
            _append_event_records(event_ledger_path, events)

    _atomic_write_text(manifest_path, _json_text(report))
    return report


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ingest player ownership source rows against player_ownership_v0."
    )
    parser.add_argument(
        "--source",
        type=Path,
        required=True,
        help="Source roster or ownership JSON file.",
    )
    parser.add_argument(
        "--previous",
        type=Path,
        required=True,
        help="Previous player_ownership_latest.json artifact.",
    )
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--dry-run",
        action="store_true",
        help="Print a report without writing promoted artifacts. This is the default.",
    )
    mode_group.add_argument(
        "--write",
        action="store_true",
        help="Promote verified changes, append events, and write a run manifest.",
    )
    parser.add_argument(
        "--latest-output",
        type=Path,
        help="Path for the promoted latest-state artifact. Defaults to --previous.",
    )
    parser.add_argument(
        "--events-dir",
        type=Path,
        default=DEFAULT_EVENTS_DIR,
        help="Directory for yearly player ownership event ledgers.",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_MANIFEST_PATH,
        help="Path for the ingestion run manifest JSON.",
    )
    args = parser.parse_args(argv)
    return args


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    mode = "write" if args.write else "dry_run"
    report = run_player_ownership_ingestion(
        source_path=args.source,
        previous_path=args.previous,
        mode=mode,
        latest_output_path=args.latest_output,
        events_dir=args.events_dir,
        manifest_path=args.manifest,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    if report["validation_errors"] or report.get("promotion_status") == "blocked":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

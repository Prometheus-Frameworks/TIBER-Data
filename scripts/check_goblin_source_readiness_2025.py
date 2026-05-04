from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

IDENTITY_PATH = Path("data/processed/evidence/roster_player_team_map_2025.source_backed.json")
PPR_PATH = Path("data/processed/evidence/player_weekly_ppr_outcomes_2025.computed_source_backed.json")
USAGE_PATH = Path("data/processed/evidence/player_weekly_usage_2025.source_backed.json")

WRAPPER_FIELDS = ("provenance", "source_path", "records")
KEY_FIELDS = ("season", "week", "player_id")

IDENTITY_REQUIRED_FIELDS = (*KEY_FIELDS, "player_name", "team", "position")
PPR_REQUIRED_FIELDS = (*KEY_FIELDS, "player_name", "team", "position", "ppr_points", "receiving_tds", "rushing_tds", "passing_tds")
USAGE_REQUIRED_FIELDS = (
    *KEY_FIELDS,
    "player_name",
    "team",
    "position",
    "targets",
    "receptions",
    "target_share",
    "air_yards",
    "air_yards_share",
    "rushing_attempts",
)

USAGE_NULL_COUNT_FIELDS = (
    "target_share",
    "air_yards_share",
    "routes_run",
    "route_participation",
    "snap_share",
    "red_zone_targets",
    "red_zone_carries",
)

COMPUTABLE_FLAGS = {
    "low_ppr_high_targets": ("ppr_points", "targets"),
    "low_ppr_high_target_share": ("ppr_points", "target_share"),
    "air_yards_without_output": ("air_yards", "ppr_points"),
    "negative_air_yards_share_context": ("air_yards_share",),
    "carries_without_points": ("rushing_attempts", "ppr_points"),
    "target_share_without_touchdown": ("target_share", "receiving_tds", "rushing_tds", "passing_tds"),
    "usage_spike_without_box_score": ("targets", "air_yards", "rushing_attempts", "ppr_points"),
}

BLOCKED_FLAGS = {
    "high_route_participation_low_output": ("routes_run", "route_participation"),
    "snap_share_jump_without_points": ("snap_share",),
    "red_zone_usage_without_td": ("red_zone_targets", "red_zone_carries", "receiving_tds", "rushing_tds"),
    "end_zone_targets_without_td": ("end_zone_targets", "receiving_tds"),
    "goal_line_carries_without_td": ("goal_line_carries", "rushing_tds"),
    "backup_role_one_injury_away": ("depth_chart_role",),
    "slot_role_without_box_score": ("slot_rate", "ppr_points"),
    "market_lag / usage_spike_without_market_reaction": ("market_line",),
    "wopr_without_ppr_output": ("wopr",),
    "rookie_ramp_hidden_by_low_volume": ("rookie_class",),
}


class ReadinessError(ValueError):
    pass


def _load_wrapped_payload(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ReadinessError(f"Missing required artifact: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ReadinessError(f"Invalid JSON artifact: {path} ({exc})") from exc
    if not isinstance(payload, dict):
        raise ReadinessError(f"Artifact payload must be an object: {path}")
    missing_wrapper = [field for field in WRAPPER_FIELDS if field not in payload]
    if missing_wrapper:
        raise ReadinessError(f"Artifact missing wrapper fields {missing_wrapper}: {path}")
    records = payload.get("records")
    if not isinstance(records, list):
        raise ReadinessError(f"Artifact records must be an array: {path}")
    if not records:
        raise ReadinessError(f"Artifact records are empty (fails closed): {path}")
    return payload


def _load_records_payload(path: Path, *, allow_array: bool = False) -> tuple[list[dict[str, Any]], str, str]:
    if not path.exists():
        raise ReadinessError(f"Missing required artifact: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ReadinessError(f"Invalid JSON artifact: {path} ({exc})") from exc

    if isinstance(payload, list):
        if not allow_array:
            raise ReadinessError(f"Artifact payload must be an object: {path}")
        if not payload:
            raise ReadinessError(f"Artifact records are empty (fails closed): {path}")
        first_source = payload[0].get("source") if isinstance(payload[0], dict) else None
        if first_source and all(isinstance(row, dict) and row.get("source") == first_source for row in payload):
            provenance = str(first_source)
            source_path = str(first_source)
        else:
            provenance = "computed_source_backed_ppr"
            source_path = str(path)
        return payload, provenance, source_path

    if not isinstance(payload, dict):
        raise ReadinessError(f"Artifact payload must be an object: {path}")
    missing_wrapper = [field for field in WRAPPER_FIELDS if field not in payload]
    if missing_wrapper:
        raise ReadinessError(f"Artifact missing wrapper fields {missing_wrapper}: {path}")
    records = payload.get("records")
    if not isinstance(records, list):
        raise ReadinessError(f"Artifact records must be an array: {path}")
    if not records:
        raise ReadinessError(f"Artifact records are empty (fails closed): {path}")
    return records, str(payload["provenance"]), str(payload["source_path"])


def _collect_missing_fields(records: list[dict[str, Any]], required_fields: tuple[str, ...]) -> set[str]:
    missing: set[str] = set()
    for row in records:
        for field in required_fields:
            if field not in row:
                missing.add(field)
    return missing


def _row_key(row: dict[str, Any]) -> tuple[int, int, str]:
    return (int(row["season"]), int(row["week"]), str(row["player_id"]).strip())


def _duplicate_count(records: list[dict[str, Any]]) -> int:
    seen = set()
    duplicates = 0
    for row in records:
        key = _row_key(row)
        if key in seen:
            duplicates += 1
        else:
            seen.add(key)
    return duplicates


def generate_readiness_report(
    identity_path: Path = IDENTITY_PATH,
    ppr_path: Path = PPR_PATH,
    usage_path: Path = USAGE_PATH,
) -> tuple[str, bool]:
    identity = _load_wrapped_payload(identity_path)
    usage = _load_wrapped_payload(usage_path)
    ppr_records, ppr_provenance, ppr_source_path = _load_records_payload(ppr_path, allow_array=True)

    identity_records = identity["records"]
    usage_records = usage["records"]

    identity_missing = _collect_missing_fields(identity_records, IDENTITY_REQUIRED_FIELDS)
    ppr_missing = _collect_missing_fields(ppr_records, PPR_REQUIRED_FIELDS)
    usage_missing = _collect_missing_fields(usage_records, USAGE_REQUIRED_FIELDS)

    if identity_missing:
        raise ReadinessError(f"Identity rows missing required fields: {sorted(identity_missing)}")
    if ppr_missing:
        raise ReadinessError(f"PPR rows missing required fields: {sorted(ppr_missing)}")
    if usage_missing:
        raise ReadinessError(f"Usage rows missing required fields: {sorted(usage_missing)}")

    ppr_duplicates = _duplicate_count(ppr_records)
    usage_duplicates = _duplicate_count(usage_records)
    if ppr_duplicates > 0:
        raise ReadinessError(f"PPR duplicate key rows detected: {ppr_duplicates}")
    if usage_duplicates > 0:
        raise ReadinessError(f"Usage duplicate key rows detected: {usage_duplicates}")

    ppr_keys = {_row_key(r) for r in ppr_records}
    usage_keys = {_row_key(r) for r in usage_records}
    identity_keys = {_row_key(r) for r in identity_records}

    joined_keys = ppr_keys & usage_keys
    if not joined_keys:
        raise ReadinessError("PPR and usage join is empty on season/week/player_id")

    usage_without_ppr = usage_keys - ppr_keys
    if usage_without_ppr:
        raise ReadinessError(
            f"PPR and usage join coverage incomplete: ppr={len(joined_keys)}/{len(ppr_keys)}, "
            f"usage={len(joined_keys)}/{len(usage_keys)}"
        )

    ppr_only = ppr_keys - usage_keys

    identity_join = joined_keys & identity_keys
    if identity_join != joined_keys:
        missing_identity = len(joined_keys - identity_keys)
        raise ReadinessError(
            f"Identity join coverage incomplete for candidate rows: "
            f"{len(identity_join)}/{len(joined_keys)} (missing={missing_identity})"
        )

    usage_null_counts = {
        field: sum(1 for row in usage_records if field not in row or row.get(field) is None)
        for field in USAGE_NULL_COUNT_FIELDS
    }
    negative_air_yards_share_count = sum(
        1
        for row in usage_records
        if isinstance(row.get("air_yards_share"), (int, float)) and row["air_yards_share"] < 0
    )

    available_fields = set().union(*(row.keys() for row in identity_records + ppr_records + usage_records))

    computable_lines = []
    for flag, required in COMPUTABLE_FLAGS.items():
        missing = sorted(set(required) - available_fields)
        if missing:
            raise ReadinessError(f"Computable GOBLIN flag '{flag}' unavailable due to missing fields: {missing}")
        computable_lines.append(f"- {flag}: ready")

    blocked_lines = []
    for flag, blocked_on in BLOCKED_FLAGS.items():
        if flag == "wopr_without_ppr_output" and "wopr" in available_fields:
            blocked_lines.append(f"- {flag}: ready (wopr available)")
            continue
        if flag == "rookie_ramp_hidden_by_low_volume" and "rookie_class" in available_fields:
            blocked_lines.append(f"- {flag}: ready (rookie_class available)")
            continue
        missing = sorted(set(blocked_on) - available_fields)
        if missing:
            blocked_lines.append(f"- {flag}: blocked, missing {'/'.join(missing)}")
        else:
            blocked_lines.append(f"- {flag}: blocked")

    report_lines = [
        "GOBLIN Source Readiness 2025",
        "Status: READY",
        "",
        "Artifacts:",
        f"- identity: available, path={identity_path}, provenance={identity['provenance']}, records={len(identity_records)}, required_fields=ok",
        f"- ppr: available, path={ppr_path}, provenance={ppr_provenance}, source_path={ppr_source_path}, records={len(ppr_records)}, required_fields=ok, duplicates={ppr_duplicates}",
        f"- usage: available, path={usage_path}, provenance={usage['provenance']}, records={len(usage_records)}, required_fields=ok, duplicates={usage_duplicates}",
        "",
        "Joins:",
        f"- ppr_usage_join_coverage: joined usage rows {len(joined_keys)}/{len(usage_keys)}, joined ppr rows {len(joined_keys)}/{len(ppr_keys)}, ppr_only_rows={len(ppr_only)}, usage_without_ppr_rows={len(usage_without_ppr)}",
        f"- candidate_eligible_rows: {len(joined_keys)}",
        f"- identity_join_coverage: {len(identity_join)}/{len(joined_keys)}",
        "",
        "Field coverage:",
    ]

    for field in USAGE_NULL_COUNT_FIELDS:
        report_lines.append(f"- {field} null count: {usage_null_counts[field]}")
    report_lines.append(f"- negative air_yards_share count: {negative_air_yards_share_count}")
    report_lines.extend(["", "Computable flags:"])
    report_lines.extend(computable_lines)
    report_lines.extend(["", "Blocked flags:"])
    report_lines.extend(blocked_lines)

    return "\n".join(report_lines), True


def main() -> int:
    try:
        report, _ = generate_readiness_report()
        print(report)
        return 0
    except Exception as exc:
        print("GOBLIN Source Readiness 2025")
        print("Status: NOT READY")
        print(f"ERROR: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

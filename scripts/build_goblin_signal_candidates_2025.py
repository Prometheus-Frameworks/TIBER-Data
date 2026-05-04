from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

IDENTITY_PATH = Path("data/processed/evidence/roster_player_team_map_2025.source_backed.json")
USAGE_PATH = Path("data/processed/evidence/player_weekly_usage_2025.source_backed.json")
PPR_PATH = Path("data/processed/evidence/player_weekly_ppr_outcomes_2025.computed_source_backed.json")
OUTPUT_PATH = Path("data/processed/research/goblin_signal_candidates_2025.source_backed.json")

WRAPPER_FIELDS = ("provenance", "source_path", "records")
KEY_FIELDS = ("season", "week", "player_id")

IDENTITY_REQUIRED = (*KEY_FIELDS, "player_name", "team", "position")
USAGE_REQUIRED = (*KEY_FIELDS, "targets", "receptions", "target_share", "air_yards", "air_yards_share", "rushing_attempts")
PPR_REQUIRED = (
    *KEY_FIELDS,
    "ppr_points",
    "receptions",
    "targets",
    "receiving_yards",
    "receiving_tds",
    "rushing_attempts",
    "rushing_yards",
    "rushing_tds",
    "passing_yards",
    "passing_tds",
    "interceptions",
    "rolling_3_week_ppr",
    "rolling_5_week_ppr",
    "season_ppr",
    "games_played",
)

BLOCKED_FIELDS = [
    "routes_run",
    "route_participation",
    "snap_share",
    "red_zone_targets",
    "red_zone_carries",
    "end_zone_targets",
    "goal_line_carries",
    "slot_rate",
    "market_line",
    "wopr",
    "rookie_class",
]

SOURCE_ARTIFACTS = [str(IDENTITY_PATH), str(USAGE_PATH), str(PPR_PATH)]


class GoblinBuildError(ValueError):
    pass


def _load_wrapper(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise GoblinBuildError(f"Missing required artifact: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise GoblinBuildError(f"Invalid JSON artifact: {path} ({exc})") from exc
    if not isinstance(payload, dict):
        raise GoblinBuildError(f"Artifact payload must be an object: {path}")
    missing = [field for field in WRAPPER_FIELDS if field not in payload]
    if missing:
        raise GoblinBuildError(f"Artifact missing wrapper fields {missing}: {path}")
    records = payload.get("records")
    if not isinstance(records, list) or not records:
        raise GoblinBuildError(f"Artifact records are empty (fails closed): {path}")
    return records


def _load_array(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise GoblinBuildError(f"Missing required artifact: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise GoblinBuildError(f"Invalid JSON artifact: {path} ({exc})") from exc
    if not isinstance(payload, list) or not payload:
        raise GoblinBuildError(f"Artifact records are empty (fails closed): {path}")
    for row in payload:
        if not isinstance(row, dict):
            raise GoblinBuildError(f"Artifact records must be object rows: {path}")
    return payload


def _row_key(row: dict[str, Any]) -> tuple[int, int, str]:
    return (int(row["season"]), int(row["week"]), str(row["player_id"]).strip())


def _ensure_required(records: list[dict[str, Any]], required: tuple[str, ...], label: str) -> None:
    missing = set()
    for row in records:
        for field in required:
            if field not in row:
                missing.add(field)
    if missing:
        raise GoblinBuildError(f"{label} rows missing required fields: {sorted(missing)}")


def _ensure_no_duplicates(records: list[dict[str, Any]], label: str) -> None:
    seen = set()
    dupes = 0
    for row in records:
        key = _row_key(row)
        if key in seen:
            dupes += 1
        else:
            seen.add(key)
    if dupes:
        raise GoblinBuildError(f"{label} duplicate key rows detected: {dupes}")


def _num(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def build_goblin_signal_candidates(
    identity_path: Path = IDENTITY_PATH,
    usage_path: Path = USAGE_PATH,
    ppr_path: Path = PPR_PATH,
    output_path: Path | None = None,
) -> dict[str, Any]:
    identity = _load_wrapper(identity_path)
    usage = _load_wrapper(usage_path)
    ppr = _load_array(ppr_path)

    _ensure_required(identity, IDENTITY_REQUIRED, "Identity")
    _ensure_required(usage, USAGE_REQUIRED, "Usage")
    _ensure_required(ppr, PPR_REQUIRED, "PPR")

    _ensure_no_duplicates(usage, "Usage")
    _ensure_no_duplicates(ppr, "PPR")

    identity_map = {_row_key(r): r for r in identity}
    usage_map = {_row_key(r): r for r in usage}
    ppr_map = {_row_key(r): r for r in ppr}

    usage_keys = set(usage_map)
    ppr_keys = set(ppr_map)
    joined_keys = usage_keys & ppr_keys
    if not joined_keys:
        raise GoblinBuildError("Usage and PPR join is empty on season/week/player_id")

    usage_without_ppr = usage_keys - ppr_keys
    if usage_without_ppr:
        raise GoblinBuildError(f"Usage rows cannot join to PPR on season/week/player_id: {len(usage_without_ppr)}")

    candidate_keys = sorted(joined_keys)
    missing_identity = [key for key in candidate_keys if key not in identity_map]
    if missing_identity:
        raise GoblinBuildError(f"Joined candidate rows cannot join to identity: {len(missing_identity)}")

    player_history: dict[str, list[tuple[int, dict[str, Any], dict[str, Any]]]] = {}
    for season, week, player_id in candidate_keys:
        player_history.setdefault(player_id, []).append((week, usage_map[(season, week, player_id)], ppr_map[(season, week, player_id)]))

    prior_by_key: dict[tuple[int, int, str], tuple[dict[str, Any], dict[str, Any]] | None] = {}
    for player_id, rows in player_history.items():
        rows_sorted = sorted(rows, key=lambda x: x[0])
        prior = None
        for week, usage_row, ppr_row in rows_sorted:
            key = (int(usage_row["season"]), int(week), player_id)
            prior_by_key[key] = prior
            prior = (usage_row, ppr_row)

    records: list[dict[str, Any]] = []
    generated_at = datetime.now(timezone.utc).isoformat()

    for key in candidate_keys:
        season, week, player_id = key
        irow = identity_map[key]
        urow = usage_map[key]
        prow = ppr_map[key]

        ppr_points = _num(prow.get("ppr_points"))
        targets = _num(urow.get("targets"))
        target_share = _num(urow.get("target_share"))
        air_yards = _num(urow.get("air_yards"))
        air_yards_share = _num(urow.get("air_yards_share"))
        rushing_attempts_usage = _num(urow.get("rushing_attempts"))

        td_total = (
            int(prow.get("receiving_tds", 0) or 0)
            + int(prow.get("rushing_tds", 0) or 0)
            + int(prow.get("passing_tds", 0) or 0)
        )

        legitimate_flags: list[str] = []
        if ppr_points is not None and targets is not None and ppr_points <= 8.0 and targets >= 6:
            legitimate_flags.append("low_ppr_high_targets")
        if ppr_points is not None and target_share is not None and ppr_points <= 8.0 and target_share >= 0.20:
            legitimate_flags.append("low_ppr_high_target_share")
        if ppr_points is not None and air_yards is not None and ppr_points <= 8.0 and air_yards >= 70:
            legitimate_flags.append("air_yards_without_output")
        if ppr_points is not None and air_yards_share is not None and targets is not None and ppr_points <= 8.0 and air_yards_share < 0 and targets >= 3:
            legitimate_flags.append("negative_air_yards_share_context")
        if ppr_points is not None and rushing_attempts_usage is not None and ppr_points <= 8.0 and rushing_attempts_usage >= 10:
            legitimate_flags.append("carries_without_points")
        if ppr_points is not None and target_share is not None and ppr_points <= 10.0 and target_share >= 0.20 and td_total == 0:
            legitimate_flags.append("target_share_without_touchdown")

        prior = prior_by_key.get(key)
        if prior is not None and ppr_points is not None and ppr_points <= 8.0:
            prior_usage = prior[0]
            deltas = [
                (_num(urow.get("targets")), _num(prior_usage.get("targets")), 3.0),
                (_num(urow.get("target_share")), _num(prior_usage.get("target_share")), 0.08),
                (_num(urow.get("air_yards")), _num(prior_usage.get("air_yards")), 40.0),
                (_num(urow.get("rushing_attempts")), _num(prior_usage.get("rushing_attempts")), 5.0),
            ]
            if any(curr is not None and prev is not None and (curr - prev) >= thresh for curr, prev, thresh in deltas):
                legitimate_flags.append("usage_spike_without_box_score")

        if not legitimate_flags:
            continue

        gross_flags: list[str] = []
        if ppr_points is not None and ppr_points <= 8.0:
            gross_flags.append("low_ppr_output")
        if td_total == 0:
            gross_flags.append("no_touchdown")
        if str(irow.get("position")) in {"WR", "TE"} and _num(prow.get("receiving_yards")) is not None and _num(prow.get("receiving_yards")) <= 40:
            gross_flags.append("low_receiving_yardage")
        if str(irow.get("position")) in {"WR", "TE"} and _num(prow.get("receptions")) is not None and _num(prow.get("receptions")) <= 3:
            gross_flags.append("low_reception_output")

        records.append(
            {
                "season": season,
                "week": week,
                "player_id": player_id,
                "player_name": irow["player_name"],
                "team": irow["team"],
                "position": irow["position"],
                "ppr_points": prow["ppr_points"],
                "gross_output_flags": sorted(gross_flags),
                "legitimate_indicator_flags": sorted(set(legitimate_flags)),
                "blocked_or_missing_fields": BLOCKED_FIELDS,
                "usage_snapshot": {
                    "targets": urow.get("targets"),
                    "receptions": urow.get("receptions"),
                    "target_share": urow.get("target_share"),
                    "air_yards": urow.get("air_yards"),
                    "air_yards_share": urow.get("air_yards_share"),
                    "rushing_attempts": urow.get("rushing_attempts"),
                },
                "output_snapshot": {
                    "receptions": prow.get("receptions"),
                    "targets": prow.get("targets"),
                    "receiving_yards": prow.get("receiving_yards"),
                    "receiving_tds": prow.get("receiving_tds"),
                    "rushing_attempts": prow.get("rushing_attempts"),
                    "rushing_yards": prow.get("rushing_yards"),
                    "rushing_tds": prow.get("rushing_tds"),
                    "passing_yards": prow.get("passing_yards"),
                    "passing_tds": prow.get("passing_tds"),
                    "interceptions": prow.get("interceptions"),
                    "rolling_3_week_ppr": prow.get("rolling_3_week_ppr"),
                    "rolling_5_week_ppr": prow.get("rolling_5_week_ppr"),
                    "season_ppr": prow.get("season_ppr"),
                    "games_played": prow.get("games_played"),
                },
                "candidate_score": None,
                "candidate_score_component_notes": {
                    "grossness_summary": ", ".join(sorted(gross_flags)) if gross_flags else "none",
                    "legitimacy_summary": ", ".join(sorted(set(legitimate_flags))),
                    "caveats": [
                        "research-only candidate scanner",
                        "negative_air_yards_share_context is contextual, not standalone recommendation",
                        "candidate_score not implemented",
                    ],
                },
                "evidence_status": "source_backed_research_candidate",
                "source_artifacts": SOURCE_ARTIFACTS,
                "generated_at": generated_at,
            }
        )

    records.sort(key=lambda r: (r["season"], r["week"], r["team"], r["position"], r["player_id"]))

    payload = {
        "provenance": "goblin_signal_candidates_v0",
        "source_type": "source_backed_research",
        "generated_from": ["scripts/build_goblin_signal_candidates_2025.py", *SOURCE_ARTIFACTS],
        "mode": "research_candidate_scanner",
        "season": 2025,
        "records": records,
    }

    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    return payload


def main() -> int:
    try:
        build_goblin_signal_candidates(output_path=OUTPUT_PATH)
    except GoblinBuildError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"Wrote {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

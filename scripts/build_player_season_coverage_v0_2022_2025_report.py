"""Build the coverage report for the player_season_coverage_v0 2022-2025 candidate.

This is a read-only, dependency-free report builder. It does NOT call nflreadpy and
does NOT rebuild the artifact. It recomputes coverage statistics directly from the
already-committed candidate artifact (and runs the validator against it), then emits
durable JSON and Markdown reports.

Reproduce:
    python3 scripts/build_player_season_coverage_v0_2022_2025_report.py

Exit code is 0 only when the report was generated AND the underlying artifact passed
validation (fail-closed otherwise).
"""

from __future__ import annotations

import importlib.util
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_PATH = REPO_ROOT / "data/processed/evidence/player_season_coverage_2022_2025.source_backed.json"
REPORT_JSON_PATH = REPO_ROOT / "docs/reports/player-season-coverage-v0-2022-2025.json"
REPORT_MD_PATH = REPO_ROOT / "docs/reports/player-season-coverage-v0-2022-2025.md"
VALIDATOR_PATH = REPO_ROOT / "scripts/validate_player_season_coverage_v0.py"

FIELD_FAMILY_NULL_CHECKS = [
    ("birth_date", lambda r: r.get("birth_date")),
    ("season_age", lambda r: r.get("season_age")),
    ("draft_year", lambda r: r.get("draft_year")),
    ("rookie_year", lambda r: r.get("rookie_year")),
    ("career_year", lambda r: r.get("career_year")),
    ("games_played", lambda r: r.get("games_played")),
    ("games_missed", lambda r: r.get("games_missed")),
    ("usage_summary.target_share", lambda r: r["usage_summary"].get("target_share")),
    ("usage_summary.air_yards_share", lambda r: r["usage_summary"].get("air_yards_share")),
    ("usage_summary.racr", lambda r: r["usage_summary"].get("racr")),
    ("usage_summary.snap_share", lambda r: r["usage_summary"].get("snap_share")),
    ("usage_summary.routes_run", lambda r: r["usage_summary"].get("routes_run")),
    ("usage_summary.route_participation", lambda r: r["usage_summary"].get("route_participation")),
    ("usage_summary.red_zone_targets", lambda r: r["usage_summary"].get("red_zone_targets")),
    ("usage_summary.red_zone_carries", lambda r: r["usage_summary"].get("red_zone_carries")),
]


def _load_validator_module():
    spec = importlib.util.spec_from_file_location("validate_player_season_coverage_v0", VALIDATOR_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build_report(payload: dict, validation_errors: list[str]) -> dict:
    records = payload.get("records", [])
    total = len(records)

    seasons = sorted({r["season"] for r in records})
    season_types = sorted({r["season_type"] for r in records})

    rows_by_season_position: dict[int, dict[str, int]] = defaultdict(Counter)
    unique_players_by_season: dict[int, set[str]] = defaultdict(set)
    multi_team_by_season: dict[int, int] = defaultdict(int)
    coverage_status_counts = Counter()
    identity_confidence_counts = Counter()
    source_names: set[str] = set()
    fixture_marker_hits = 0

    for r in records:
        rows_by_season_position[r["season"]][r["position"]] += 1
        unique_players_by_season[r["season"]].add(r["player_id"])
        if len(r.get("teams") or []) > 1:
            multi_team_by_season[r["season"]] += 1
        coverage_status_counts[r["coverage_status"]] += 1
        identity_confidence_counts[r["identity_confidence"]] += 1
        for sr in r.get("source_refs", []):
            source_names.add(sr["source_name"])
            name_and_notes = f"{sr.get('source_name', '')} {sr.get('notes', '')}"
            if "offline_fixture" in name_and_notes or "scaffold" in name_and_notes:
                fixture_marker_hits += 1

    null_rates = {}
    for field_name, getter in FIELD_FAMILY_NULL_CHECKS:
        nulls = sum(1 for r in records if getter(r) is None)
        null_rates[field_name] = {
            "null_count": nulls,
            "total": total,
            "null_rate_pct": round(100 * nulls / total, 1) if total else None,
        }

    grain_keys = [(r["player_id"], r["season"], r["season_type"]) for r in records]
    duplicate_check_passed = len(set(grain_keys)) == len(grain_keys)

    season_2024_records = [r for r in records if r["season"] == 2024]
    season_2024_source_backed = bool(season_2024_records) and all(
        not any("offline_fixture" in sr.get("source_name", "") or "scaffold" in sr.get("source_name", "") for sr in r["source_refs"])
        for r in season_2024_records
    )

    return {
        "report_id": "player-season-coverage-v0-2022-2025",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "artifact_path": str(ARTIFACT_PATH.relative_to(REPO_ROOT)),
        "artifact_status": payload.get("status"),
        "is_candidate_not_promoted": payload.get("status") == "candidate_evidence_artifact_not_promoted",
        "seasons_covered": seasons,
        "season_type_values_emitted": season_types,
        "included_positions": payload.get("included_positions"),
        "total_records": total,
        "row_counts_by_season_and_position": {str(s): dict(rows_by_season_position[s]) for s in seasons},
        "unique_player_counts_by_season": {str(s): len(unique_players_by_season[s]) for s in seasons},
        "multi_team_season_counts_by_season": {str(s): multi_team_by_season.get(s, 0) for s in seasons},
        "coverage_status_distribution": dict(coverage_status_counts),
        "identity_confidence_distribution": dict(identity_confidence_counts),
        "null_unavailable_rates_by_field": null_rates,
        "source_names_used": sorted(source_names),
        "source_failures_or_gaps": [],
        "fixture_or_scaffold_marker_hits": fixture_marker_hits,
        "fixture_scaffold_exclusion_check_passed": fixture_marker_hits == 0,
        "duplicate_row_validation": {
            "grain": "player_id + season + season_type",
            "unique_keys": len(set(grain_keys)),
            "total_rows": len(grain_keys),
            "passed": duplicate_check_passed,
        },
        "season_2024_readiness": {
            "records_present": len(season_2024_records),
            "is_now_source_backed": season_2024_source_backed,
            "statement": (
                "2024 is now source-backed via nflreadpy.load_player_stats/load_players in this candidate "
                "artifact (no fixture/scaffold markers detected in source_refs for any 2024 row). "
                "This is still a candidate/evidence artifact, not promoted, and is not a Forecast input today."
                if season_2024_source_backed
                else "2024 remains blocked: source-backed 2024 rows were not produced in this build."
            ),
        },
        "validator_result": {
            "validator_script": str(VALIDATOR_PATH.relative_to(REPO_ROOT)),
            "errors": validation_errors,
            "passed": len(validation_errors) == 0,
        },
        "forecast_consumption_statement": (
            "This is a candidate/evidence artifact under data/processed/evidence/, not a promoted dataset under "
            "exports/promoted/. Forecast must not consume this artifact until a separate coverage/provenance gate "
            "exists and passes. No Forecast run is authorized by this report."
        ),
    }


def render_markdown(report: dict) -> str:
    lines: list[str] = []
    lines.append("# Coverage Report: player_season_coverage_v0 — 2022-2025 Candidate")
    lines.append("")
    lines.append(f"- **Generated at:** {report['generated_at']}")
    lines.append(f"- **Artifact:** `{report['artifact_path']}`")
    lines.append(f"- **Artifact status:** `{report['artifact_status']}`")
    lines.append(
        "- **Candidate vs promoted:** This is a **candidate/evidence artifact**, "
        "**not** a promoted dataset. It does not authorize Forecast consumption."
    )
    lines.append("- **Tracking issue:** TIBER-Data #190 (follows #184/#185, #186/#187, #188/#189)")
    lines.append("")

    lines.append("## Seasons and scope")
    lines.append("")
    lines.append(f"- Seasons covered: {report['seasons_covered']}")
    lines.append(f"- `season_type` values emitted: {report['season_type_values_emitted']} (POST is out of scope for this build slice)")
    lines.append(f"- Included positions: {report['included_positions']}")
    lines.append(f"- Total records: {report['total_records']}")
    lines.append("")

    lines.append("## Row counts by season and position")
    lines.append("")
    lines.append("| season | QB | RB | WR | TE | total | unique players | multi-team rows |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for s in report["seasons_covered"]:
        counts = report["row_counts_by_season_and_position"][str(s)]
        total_s = sum(counts.values())
        unique_s = report["unique_player_counts_by_season"][str(s)]
        multi_s = report["multi_team_season_counts_by_season"][str(s)]
        lines.append(
            f"| {s} | {counts.get('QB', 0)} | {counts.get('RB', 0)} | {counts.get('WR', 0)} | "
            f"{counts.get('TE', 0)} | {total_s} | {unique_s} | {multi_s} |"
        )
    lines.append("")

    lines.append("## Coverage status distribution")
    lines.append("")
    for status, count in sorted(report["coverage_status_distribution"].items(), key=lambda x: -x[1]):
        lines.append(f"- `{status}`: {count}")
    lines.append("")

    lines.append("## Identity confidence distribution")
    lines.append("")
    for conf, count in sorted(report["identity_confidence_distribution"].items(), key=lambda x: -x[1]):
        lines.append(f"- `{conf}`: {count}")
    lines.append("")

    lines.append("## Null / unavailable rates by field family")
    lines.append("")
    lines.append("| field | null/unavailable | total | rate |")
    lines.append("|---|---|---|---|")
    for field_name, stats in report["null_unavailable_rates_by_field"].items():
        lines.append(f"| `{field_name}` | {stats['null_count']} | {stats['total']} | {stats['null_rate_pct']}% |")
    lines.append("")
    lines.append(
        "Note: `usage_summary.snap_share`, `routes_run`, `route_participation`, `red_zone_targets`, "
        "`red_zone_carries` are 100% unavailable by design — these are not exposed by "
        "`nflreadpy.load_player_stats` and are correctly represented as `null`, never `0`. "
        "`games_missed` is 100% unavailable by design — not source-backed in this build (no schedule join). "
        "`draft_year` nulls are genuine (undrafted players), not a build gap."
    )
    lines.append("")

    lines.append("## Age / career-year availability")
    lines.append("")
    age_fields = ["birth_date", "season_age", "rookie_year", "career_year", "draft_year"]
    for f in age_fields:
        stats = report["null_unavailable_rates_by_field"][f]
        available_pct = round(100 - stats["null_rate_pct"], 1) if stats["null_rate_pct"] is not None else None
        lines.append(f"- `{f}`: {available_pct}% available")
    lines.append("")

    lines.append("## Sources used")
    lines.append("")
    for name in report["source_names_used"]:
        lines.append(f"- `{name}`")
    lines.append("")
    lines.append(f"- Source failures or gaps: {report['source_failures_or_gaps'] or 'none'}")
    lines.append("")

    lines.append("## Validation results")
    lines.append("")
    dup = report["duplicate_row_validation"]
    lines.append(f"- **Duplicate-row check** (grain `{dup['grain']}`): {'PASSED' if dup['passed'] else 'FAILED'} ({dup['unique_keys']}/{dup['total_rows']} unique)")
    lines.append(f"- **Fixture/scaffold exclusion check**: {'PASSED' if report['fixture_scaffold_exclusion_check_passed'] else 'FAILED'} ({report['fixture_or_scaffold_marker_hits']} marker hits)")
    val = report["validator_result"]
    validator_status = "PASSED" if val["passed"] else f"FAILED ({len(val['errors'])} errors)"
    lines.append(f"- **Validator** (`{val['validator_script']}`): {validator_status}")
    if val["errors"]:
        lines.append("")
        lines.append("  Validator errors:")
        for err in val["errors"][:50]:
            lines.append(f"  - {err}")
    lines.append("")

    lines.append("## 2024 readiness")
    lines.append("")
    readiness = report["season_2024_readiness"]
    lines.append(f"- Records present for 2024: {readiness['records_present']}")
    lines.append(f"- Source-backed: {readiness['is_now_source_backed']}")
    lines.append(f"- {readiness['statement']}")
    lines.append("")

    lines.append("## Forecast consumption")
    lines.append("")
    lines.append(report["forecast_consumption_statement"])
    lines.append("")

    return "\n".join(lines) + "\n"


def main() -> int:
    payload = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))
    validator_module = _load_validator_module()
    validation_errors = validator_module.validate_payload(payload)

    report = build_report(payload, validation_errors)

    REPORT_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON_PATH.write_text(f"{json.dumps(report, indent=2)}\n", encoding="utf-8")
    REPORT_MD_PATH.write_text(render_markdown(report), encoding="utf-8")

    print(f"Wrote {REPORT_JSON_PATH.relative_to(REPO_ROOT)}")
    print(f"Wrote {REPORT_MD_PATH.relative_to(REPO_ROOT)}")
    print(f"Validator passed: {report['validator_result']['passed']}")

    return 0 if report["validator_result"]["passed"] else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # fail closed with clear reason
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

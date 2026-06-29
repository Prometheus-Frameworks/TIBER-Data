"""Audit governed `team_week_raw_v0` 2024 Teamstate-source coverage for the Forecast gate.

This is a read-only, dependency-free audit. It does NOT retrieve sources, does NOT
rebuild, does NOT mutate the governed artifact, and does NOT zero-fill, estimate, or
launder any deferred/unavailable field. It recomputes the coverage/governance state
directly from the already-committed governed artifact, its validation report, and its
lineage manifest, then emits a durable JSON audit report.

It exists so the answer to TIBER-Data #181 ("does complete governed 2024 Teamstate
coverage already exist?") is reproducible by anyone, in any environment, without the
nflverse/polars build dependencies needed to *produce* the artifact.

Reproduce:
    python3 scripts/audit_team_week_raw_v0_2024_teamstate_coverage.py

Exit code is 0 only when every audit check passes (fail-closed otherwise).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]

ARTIFACT_PATH = REPO_ROOT / (
    "exports/candidates/team_week_raw/"
    "team_week_raw_v0_2024_real_source_candidate.json"
)
VALIDATION_REPORT_PATH = REPO_ROOT / (
    "exports/candidates/team_week_raw/"
    "team_week_raw_v0_2024_real_source_candidate.validation.json"
)
LINEAGE_MANIFEST_PATH = REPO_ROOT / (
    "data/manifests/team_week_raw_v0_2024_real_source_candidate.manifest.json"
)
AUDIT_REPORT_PATH = REPO_ROOT / (
    "exports/candidates/team_week_raw/"
    "team_week_raw_v0_2024_teamstate_coverage_audit.json"
)

SEASON = 2024
# 32 NFL teams, with the source 'LA' canonicalized to 'LAR' and Washington as 'WAS'
# (per docs/contracts/team-week-raw-v0.md team-code canonicalization).
CANONICAL_NFL_TEAMS = frozenset(
    {
        "ARI", "ATL", "BAL", "BUF", "CAR", "CHI", "CIN", "CLE",
        "DAL", "DEN", "DET", "GB", "HOU", "IND", "JAX", "KC",
        "LAC", "LAR", "LV", "MIA", "MIN", "NE", "NO", "NYG",
        "NYJ", "PHI", "PIT", "SEA", "SF", "TB", "TEN", "WAS",
    }
)
# 32 teams x 17 played games each (byes are non-game weeks, not missing truth).
EXPECTED_TEAM_GAME_ROWS = 544
EXPECTED_GAMES_PER_TEAM = 17

# Fields the downstream Teamstate/Forecast path consumes from a team-week row.
DOWNSTREAM_CONSUMED_FIELDS = (
    "teamCode", "season", "week", "opponentCode",
    "epaPerPlay", "successRate", "redZoneTdRate",
    "passRate", "rushRate", "neutralPassRate",
    "passEpaPerPlay", "rushEpaPerPlay", "explosivePlayRate",
    "secondsPerPlay", "pointsPerDrive", "pointsFor", "pointsAgainst",
    "drives", "redZoneTrips", "sacksAllowed", "turnovers",
    "offensivePlays", "neutralPlays",
    "pressureRateAllowed",
    "fantasyPointsForQB", "fantasyPointsForRB",
    "fantasyPointsForWR", "fantasyPointsForTE",
    "fantasyPointsAllowedQB", "fantasyPointsAllowedRB",
    "fantasyPointsAllowedWR", "fantasyPointsAllowedTE",
)


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _check(name: str, passed: bool, details: dict[str, Any]) -> dict[str, Any]:
    return {"name": name, "passed": bool(passed), "details": details}


def run_audit() -> dict[str, Any]:
    artifact = _load_json(ARTIFACT_PATH)
    validation = _load_json(VALIDATION_REPORT_PATH)
    manifest = _load_json(LINEAGE_MANIFEST_PATH)

    rows: list[dict[str, Any]] = artifact["rows"]
    metadata: dict[str, Any] = artifact.get("metadata", {})
    coverage: dict[str, Any] = metadata.get("coverage", {})
    governance: dict[str, Any] = metadata.get("governance", {})
    field_readiness: dict[str, Any] = metadata.get("fieldReadiness", {})
    deferred_fields = list(metadata.get("deferredFields", []))

    checks: list[dict[str, Any]] = []

    # --- Section 1/2: coverage verification -------------------------------
    present_teams = sorted({r["teamCode"] for r in rows})
    missing_teams = sorted(CANONICAL_NFL_TEAMS - set(present_teams))
    unexpected_teams = sorted(set(present_teams) - CANONICAL_NFL_TEAMS)
    checks.append(
        _check(
            "all_32_nfl_teams_present",
            len(present_teams) == 32 and not missing_teams and not unexpected_teams,
            {
                "teamCount": len(present_teams),
                "missingTeams": missing_teams,
                "unexpectedTeams": unexpected_teams,
            },
        )
    )

    checks.append(
        _check(
            "expected_team_game_row_count",
            len(rows) == EXPECTED_TEAM_GAME_ROWS,
            {"expected": EXPECTED_TEAM_GAME_ROWS, "actual": len(rows)},
        )
    )

    rows_per_team: dict[str, int] = {}
    for r in rows:
        rows_per_team[r["teamCode"]] = rows_per_team.get(r["teamCode"], 0) + 1
    teams_off_17 = {t: c for t, c in rows_per_team.items() if c != EXPECTED_GAMES_PER_TEAM}
    checks.append(
        _check(
            "every_team_has_17_played_games",
            not teams_off_17,
            {"expectedGamesPerTeam": EXPECTED_GAMES_PER_TEAM, "teamsOffExpected": teams_off_17},
        )
    )

    seen: set[tuple[str, int]] = set()
    duplicate_keys: list[list[Any]] = []
    for r in rows:
        key = (r["teamCode"], r["week"])
        if key in seen:
            duplicate_keys.append([r["teamCode"], r["week"]])
        seen.add(key)
    checks.append(
        _check("no_duplicate_team_week_rows", not duplicate_keys, {"duplicateKeys": duplicate_keys})
    )

    bad_season = sorted({r["week"] for r in rows if r["season"] != SEASON})
    checks.append(
        _check("all_rows_season_2024", not bad_season, {"season": SEASON, "nonSeasonRows": bad_season})
    )

    invalid_team_codes = sorted({r["teamCode"] for r in rows if r["teamCode"] not in CANONICAL_NFL_TEAMS})
    invalid_opp_codes = sorted(
        {r["opponentCode"] for r in rows if r.get("opponentCode") not in CANONICAL_NFL_TEAMS}
    )
    checks.append(
        _check(
            "team_codes_normalized_to_nfl_set",
            not invalid_team_codes and not invalid_opp_codes,
            {"invalidTeamCodes": invalid_team_codes, "invalidOpponentCodes": invalid_opp_codes},
        )
    )

    # --- Section: deterministic ordering ----------------------------------
    order_keys = [(r["week"], r["teamCode"]) for r in rows]
    checks.append(
        _check(
            "deterministic_ordering_week_then_teamcode",
            order_keys == sorted(order_keys),
            {"orderKey": "(week, teamCode)"},
        )
    )

    # --- Section 4: null semantics ----------------------------------------
    null_report: dict[str, Any] = {}
    for field in DOWNSTREAM_CONSUMED_FIELDS:
        non_null = sum(1 for r in rows if r.get(field) is not None)
        null_count = len(rows) - non_null
        readiness = field_readiness.get(field)
        if field in deferred_fields:
            classification = "deferred"
        elif readiness:
            classification = readiness
        elif null_count == 0:
            classification = "available"
        elif null_count == len(rows):
            classification = "absent_or_deferred"
        else:
            classification = "partial_nulls"
        null_report[field] = {
            "nonNull": non_null,
            "null": null_count,
            "classification": classification,
        }

    # No deferred field may carry a value on any row (null-to-zero laundering guard).
    deferred_value_violations = [
        [r["teamCode"], r["week"], f]
        for r in rows
        for f in deferred_fields
        if r.get(f) is not None
    ]
    checks.append(
        _check(
            "deferred_fields_never_zero_filled",
            not deferred_value_violations,
            {"deferredFields": deferred_fields, "violations": deferred_value_violations[:10]},
        )
    )

    # redZoneTdRate nulls must be exactly the zero-redZoneTrips rows (legitimate partial null).
    rz_null_nonzero_trips = [
        [r["teamCode"], r["week"], r.get("redZoneTrips")]
        for r in rows
        if r.get("redZoneTdRate") is None and r.get("redZoneTrips") not in (0, None)
    ]
    checks.append(
        _check(
            "redzone_td_rate_nulls_are_zero_trip_rows",
            not rz_null_nonzero_trips,
            {"unexplainedNullRows": rz_null_nonzero_trips},
        )
    )

    # --- Section 5: governance / provenance -------------------------------
    governed_marker_ok = (
        governance.get("governanceStatus") == "governed"
        and governance.get("governanceSource") == "explicit_marker"
        and metadata.get("provenanceStatus") == "governed_real_data"
    )
    checks.append(
        _check(
            "explicit_governance_marker_agrees_with_provenance",
            governed_marker_ok,
            {
                "governanceStatus": governance.get("governanceStatus"),
                "governanceSource": governance.get("governanceSource"),
                "provenanceStatus": metadata.get("provenanceStatus"),
            },
        )
    )

    source_refs = [
        ref
        for src in manifest.get("sources", [])
        for ref in src.get("sourceRefs", [])
    ]
    checks.append(
        _check(
            "source_refs_present",
            len(source_refs) >= 1,
            {"sourceRefs": source_refs},
        )
    )

    checksums = [src.get("checksum", {}).get("value") for src in manifest.get("sources", [])]
    checks.append(
        _check(
            "source_checksums_present",
            all(bool(c) for c in checksums) and len(checksums) >= 1,
            {"checksumCount": len([c for c in checksums if c])},
        )
    )

    validation_ref_ok = (
        metadata.get("validationReportPath") == manifest.get("validationReportPath")
        and bool(validation.get("allPassed"))
    )
    checks.append(
        _check(
            "validation_refs_present_and_passing",
            validation_ref_ok,
            {
                "validationReportPath": metadata.get("validationReportPath"),
                "validationAllPassed": validation.get("allPassed"),
            },
        )
    )

    lineage_ref_ok = bool(metadata.get("lineageManifestPath")) and bool(
        manifest.get("lineageManifestPath")
    )
    checks.append(
        _check(
            "lineage_refs_present",
            lineage_ref_ok,
            {"lineageManifestPath": metadata.get("lineageManifestPath")},
        )
    )

    promotion = manifest.get("promotion", {})
    checks.append(
        _check(
            "promotion_recorded",
            promotion.get("decision") == "governed_real_data" and bool(promotion.get("reviewRefs")),
            {
                "decision": promotion.get("decision"),
                "reviewedAt": promotion.get("reviewedAt"),
                "reviewRefs": promotion.get("reviewRefs"),
            },
        )
    )

    checks.append(
        _check(
            "generated_at_present",
            bool(artifact.get("generatedAt")) and bool(manifest.get("generatedAt")),
            {
                "artifactGeneratedAt": artifact.get("generatedAt"),
                "manifestGeneratedAt": manifest.get("generatedAt"),
            },
        )
    )

    all_passed = all(c["passed"] for c in checks)

    return {
        "report": "team_week_raw_v0_2024_teamstate_coverage_audit",
        "season": SEASON,
        "issue": "TIBER-Data#181",
        "artifactPath": str(ARTIFACT_PATH.relative_to(REPO_ROOT)),
        "validationReportPath": str(VALIDATION_REPORT_PATH.relative_to(REPO_ROOT)),
        "lineageManifestPath": str(LINEAGE_MANIFEST_PATH.relative_to(REPO_ROOT)),
        "rowCount": len(rows),
        "teamCount": len(present_teams),
        "expectedTeamGameRows": EXPECTED_TEAM_GAME_ROWS,
        "weeksPresent": sorted({r["week"] for r in rows}),
        "coverageMetadata": {
            "isFullLeague": coverage.get("isFullLeague"),
            "isFullRegularSeasonCalendar": coverage.get("isFullRegularSeasonCalendar"),
            "byeWeeksHandled": coverage.get("byeWeeksHandled"),
            "missingTeams": coverage.get("missingTeams"),
        },
        "deferredFields": deferred_fields,
        "fieldNullReport": null_report,
        "checks": checks,
        "allPassed": all_passed,
    }


def main() -> int:
    report = run_audit()
    AUDIT_REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    for c in report["checks"]:
        status = "PASS" if c["passed"] else "FAIL"
        print(f"  [{status}] {c['name']}")
    print(
        f"\n{report['teamCount']}/32 teams, {report['rowCount']}/"
        f"{report['expectedTeamGameRows']} team-game rows, allPassed={report['allPassed']}"
    )
    print(f"Audit report written to {AUDIT_REPORT_PATH.relative_to(REPO_ROOT)}")
    return 0 if report["allPassed"] else 1


if __name__ == "__main__":
    sys.exit(main())

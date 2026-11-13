"""Offline design study, not a canonical catalog, data adapter, or MCP server.

All ``study.*`` identifiers belong to this demonstration only. Source meaning
stays in the pinned producer files. No command fetches data or writes files.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
from pathlib import Path
from typing import Any

DATA_REPO = "Prometheus-Frameworks/TIBER-Data"
DATA_REF = "c46e9c34fd355bf922bc14eaeeb88fc9c3e77adc"
FOOTBALL_REF = "5027a0946bced5e8e4e843f885d1c4bb93b0a421"
STUDY_VERSION = "0.1.0"
ROOT = Path(__file__).resolve().parents[3]

DATA_PATHS = (
    "AGENTS.md",
    "docs/TIBER_DOCTRINE.md",
    "docs/repo-boundaries-and-feedback-loops.md",
    "docs/projection-input-semantics.md",
    "data/semantics/projection_input_semantics.json",
    "src/contracts/v1/roleOpportunity.ts",
    "src/contracts/v1/rbContactEvasionObservationsV0.ts",
    "src/derive/gold.py",
    "src/utils/frames.py",
    "src/transform/silver.py",
    "docs/schemas/player_role_inputs_weekly.md",
    "scripts/build_player_weekly_usage_source_backed_2025.py",
    "src/export/playerWeeklyUsageArtifact.ts",
    "docs/data/player-weekly-usage-source-backed-2025.md",
    "docs/data/receiving-role-integrity-route-participation-proxy.md",
    "docs/audits/offensive-participation-evidence-readiness-audit-2026-08-10.md",
    "data/processed/evidence/player_weekly_usage_2025.source_backed.json",
    "exports/promoted/nfl/player_weekly_usage_v1.json",
    "exports/promoted/nfl/player_season_coverage_v0.json",
)
EXTERNAL_SOURCES = {
    "STRATEGY.md": "feb3e711f48e2de6c4bfcb83cd9c915d13706903",
    "src/metrics.ts": "870af3ec4499ab0d3c9c8907ba2b6e2470083e1b",
    "src/tools.ts": "4dae4418c7ea3dc58b03f7d9ce31352059785163",
    "src/__tests__/metrics.test.ts": "31e29713a813c4cffa1e87667ddbb37e950589b8",
    "src/__tests__/search-coverage.test.ts": "c6be01c7c3d6ec622fc024ffebf63dd1fa505e7c",
    "src/data-update.ts": "181084e0f11dcbc55d25fab02444a406bb3fc4e6",
    "package.json": "ecbf46c3ae8c6218491da70018bc603635610e8d",
}


def source(path: str) -> str:
    return f"https://github.com/{DATA_REPO}/blob/{DATA_REF}/{path}"


def envelope(status: str, **payload: Any) -> dict[str, Any]:
    return {
        "study_version": STUDY_VERSION,
        "status": status,
        "consumer_authorized": False,
        "scope": "offline_design_study; no current player evidence",
        **payload,
    }


def definitions() -> list[dict[str, Any]]:
    """Inspection views and proposals; never alternate owners of field meaning."""
    common = {
        "namespace": "study_only",
        "unit": "fraction",
        "scope_requirement": "same player/team/window and eligible event population",
        "runtime_binding": None,
        "consumer_authorized": False,
    }
    cards = [
        {
            "id": "study.target_share.gold_team_targets.v0",
            "family": "target_share",
            "definition_status": "existing_code_inspection",
            "numerator": "player_targets",
            "denominator": "sum_player_targets_in_silver_team_week",
            "formula": "player_targets / team_targets when team_targets > 0; otherwise 0.0",
            "missing_behavior": (
                "Existing gold code returns 0.0 for zero, negative, or null team_targets."
                " Policy concern; unchanged by study."
            ),
            "unresolved": [
                "Input-population completeness; observed code behavior is not source admission."
            ],
            "sources": [source("src/derive/gold.py"), source("src/transform/silver.py")],
        },
        {
            "id": "study.target_share.weekly_source_passthrough.v0",
            "family": "target_share",
            "definition_status": "existing_mapping_inspection",
            "numerator": None,
            "denominator": None,
            "formula": None,
            "missing_behavior": (
                "Preserve upstream target_share or null. No denominator is reconstructed."
            ),
            "unresolved": [
                (
                    "Exact upstream formula/version is not pinned by the inspected weekly "
                    "artifact; cannot bind gold formula retroactively."
                )
            ],
            "sources": [source("scripts/build_player_weekly_usage_source_backed_2025.py")],
        },
        {
            "id": "study.route_share.sum_player_routes.v0",
            "family": "route_share",
            "definition_status": "existing_code_inspection",
            "numerator": "actual_player_routes_run",
            "denominator": "sum_player_routes_in_input_team_week",
            "formula": "player_routes / sum(input_player_routes for team, season, week)",
            "missing_behavior": (
                "No route column or nonpositive sum: null. Partial player/route coverage "
                "requires separate qualification."
            ),
            "unresolved": [
                (
                    "True routes and complete input-player coverage are not established for a"
                    " live lane."
                )
            ],
            "sources": [
                source("src/derive/gold.py"),
                source("docs/schemas/player_role_inputs_weekly.md"),
            ],
        },
        {
            "id": "study.route_participation.team_dropbacks.v0",
            "family": "route_participation",
            "definition_status": "proposed_ratio_only",
            "numerator": "actual_player_routes_run",
            "denominator": "eligible_team_dropbacks",
            "formula": "actual_player_routes_run / eligible_team_dropbacks",
            "missing_behavior": (
                "Unavailable if either count, matched scope, or event rules are "
                "unavailable; zero denominator has no value."
            ),
            "unresolved": [
                (
                    "Provider route definition and sack/scramble/spike/penalty eligibility "
                    "are not frozen; no canonical binding is proposed as ready."
                )
            ],
            "sources": [
                source("docs/projection-input-semantics.md"),
                source(
                    "docs/audits/offensive-participation-evidence-readiness-audit-2026-08-10.md"
                ),
            ],
        },
        {
            "id": "study.targets_per_route.actual_routes.v0",
            "family": "targets_per_route",
            "definition_status": "existing_code_inspection",
            "numerator": "player_targets",
            "denominator": "actual_player_routes_run",
            "formula": (
                "player_targets / actual_player_routes_run when routes_run > 0; otherwise null"
            ),
            "missing_behavior": (
                "No routes, null routes, or zero routes: null. On-field participation "
                "cannot substitute for routes."
            ),
            "unresolved": [
                "Requires admitted actual routes on the same eligible plays as targets."
            ],
            "sources": [
                source("src/derive/gold.py"),
                source("data/semantics/projection_input_semantics.json"),
            ],
        },
        {
            "id": "study.pass_play_participation_proxy.eligible_pass_plays.v0",
            "family": "pass_play_participation_proxy",
            "definition_status": "existing_scaffold_inspection",
            "numerator": "on_field_eligible_pass_plays",
            "denominator": "eligible_team_pass_plays",
            "formula": "on_field_eligible_pass_plays / eligible_team_pass_plays",
            "missing_behavior": (
                "Missing participation, denominator, identity, or event policy: "
                "unavailable. Never relabel as routes."
            ),
            "unresolved": [
                (
                    "Scaffold and historical source audit do not establish current-season "
                    "source admission."
                )
            ],
            "sources": [source("docs/data/receiving-role-integrity-route-participation-proxy.md")],
        },
    ]
    return [{**common, **card} for card in cards]


def catalog_digest() -> str:
    return hashlib.sha256(
        json.dumps(definitions(), sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def catalog() -> dict[str, Any]:
    return envelope(
        "inspection_catalog", catalog_sha256=catalog_digest(), definitions=definitions()
    )


def get_definition(query: str) -> dict[str, Any]:
    """Exact IDs and a few declared aliases only; no silent semantic guessing."""
    key = query.strip().lower()
    aliases = {"tprr": "targets_per_route", "route %": "route_ambiguity"}
    key = aliases.get(key, key)
    matches = [c for c in definitions() if c["id"] == key]
    if not matches:
        families = {"route_share", "route_participation"} if key == "route_ambiguity" else {key}
        matches = [c for c in definitions() if c["family"] in families]
    if not matches:
        return envelope("not_indexed", query=query, matches=[])
    if len(matches) > 1:
        return envelope(
            "ambiguous",
            query=query,
            matches=matches,
            reason="Choose the source and denominator explicitly; no default variant.",
        )
    return envelope("definition_view", definition=matches[0], catalog_sha256=catalog_digest())


def compare(left: str, right: str) -> dict[str, Any]:
    by_id = {c["id"]: c for c in definitions()}
    if left not in by_id or right not in by_id:
        return envelope("not_indexed", reason="compare requires two exact study IDs")
    a, b = by_id[left], by_id[right]
    dimensions = ("numerator", "denominator", "formula", "missing_behavior", "definition_status")
    return envelope(
        "definition_comparison",
        left=left,
        right=right,
        interchangeable=left == right,
        differing_dimensions=[k for k in dimensions if a[k] != b[k]],
        observation_comparability=(
            "not_assessed; also requires matched scope, sources, and eligibility"
        ),
    )


def synthetic_ratio(numerator: Any, denominator: Any) -> dict[str, Any]:
    """Arithmetic illustration only. It cannot validate a source or event policy."""
    for count in (numerator, denominator):
        if count is None:
            continue
        if (
            isinstance(count, bool)
            or not isinstance(count, (int, float))
            or not math.isfinite(count)
            or count < 0
        ):
            raise ValueError("synthetic counts must be finite nonnegative numbers or null")
    if numerator is None or denominator is None:
        return {"status": "missing_input", "value": None, "evidence_kind": "synthetic_demo"}
    if denominator == 0:
        return {"status": "undefined_denominator", "value": None, "evidence_kind": "synthetic_demo"}
    return {
        "status": "synthetic_arithmetic",
        "value": numerator / denominator,
        "evidence_kind": "synthetic_demo",
    }


def demo() -> dict[str, Any]:
    counts = {
        "actual_player_routes": 21,
        "team_dropbacks": 30,
        "sum_input_player_routes": 105,
        "team_pass_attempts": 24,
        "on_field_pass_plays": 24,
        "player_targets": 6,
        "team_targets": 22,
    }
    examples = [
        ("route_share", "actual_player_routes", "sum_input_player_routes"),
        ("proposed_route_participation", "actual_player_routes", "team_dropbacks"),
        ("pass_attempt_denominator_counterexample", "actual_player_routes", "team_pass_attempts"),
        ("pass_play_participation_proxy", "on_field_pass_plays", "team_dropbacks"),
        ("targets_per_route", "player_targets", "actual_player_routes"),
        ("target_share_gold_formula", "player_targets", "team_targets"),
    ]
    return envelope(
        "synthetic_demo",
        player_identity=None,
        counts=counts,
        caveat=(
            "Independent arithmetic examples, not a reconciled event ledger or a real"
            " player/game. No source or eligibility rule is validated."
        ),
        examples=[
            {
                "label": label,
                "numerator": n,
                "denominator": d,
                **synthetic_ratio(counts[n], counts[d]),
            }
            for label, n, d in examples
        ],
        missing_routes_example=synthetic_ratio(6, None),
        zero_routes_example=synthetic_ratio(6, 0),
        aggregation_example={
            "evidence_kind": "synthetic_demo",
            "game_counts": [[1, 2], [9, 30]],
            "ratio_of_sums": 10 / 32,
            "mean_of_game_ratios": ((1 / 2) + (9 / 30)) / 2,
            "meaning": "31.25% and 40% answer different aggregation questions; no default chosen.",
        },
    )


def git_bytes(path: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{DATA_REF}:{path}"], cwd=ROOT)


def git_blob_sha(path: str) -> str:
    return subprocess.check_output(
        ["git", "rev-parse", f"{DATA_REF}:{path}"], cwd=ROOT, text=True
    ).strip()


def audit() -> dict[str, Any]:
    """Census committed artifacts at the pinned baseline, never current feeds."""
    weekly_path = "data/processed/evidence/player_weekly_usage_2025.source_backed.json"
    fixture_path = "exports/promoted/nfl/player_weekly_usage_v1.json"
    season_path = "exports/promoted/nfl/player_season_coverage_v0.json"
    weekly = json.loads(git_bytes(weekly_path))["records"]
    fixtures = json.loads(git_bytes(fixture_path))
    seasons = json.loads(git_bytes(season_path))["records"]
    wr = [r for r in seasons if r["position"] == "WR"]
    fields = ("routes_run", "route_participation", "snap_share", "target_share")

    def counts(rows):
        return {k: sum(row.get(k) is not None for row in rows) for k in fields}

    inventory = [
        {
            "path": p,
            "git_blob_sha": git_blob_sha(p),
            "sha256": hashlib.sha256(git_bytes(p)).hexdigest(),
            "url": source(p),
        }
        for p in DATA_PATHS
    ]
    return envelope(
        "pinned_repository_inspection",
        inspection_date="2026-11-04",
        task_classification=[
            "provenance_source_audit",
            "documentation_and_offline_design_demonstration",
        ],
        data_ref=DATA_REF,
        external_ref=FOOTBALL_REF,
        external_classification=(
            "schema_reference_only; source code and documentation patterns, no "
            "upstream data admitted"
        ),
        external_sources=[
            {
                "path": p,
                "git_blob_sha": sha,
                "url": f"https://github.com/withqwerty/football-docs/blob/{FOOTBALL_REF}/{p}",
            }
            for p, sha in EXTERNAL_SOURCES.items()
        ],
        data_sources=inventory,
        artifact_coverage=[
            {
                "path": weekly_path,
                "rows": len(weekly),
                "seasons": sorted({r["season"] for r in weekly}),
                "weeks": sorted({r["week"] for r in weekly}),
                "non_null": counts(weekly),
                "meaning": (
                    "Repo-held source-backed input; non-null is not new admission, formula "
                    "qualification, or current coverage."
                ),
            },
            {
                "path": fixture_path,
                "rows": len(fixtures),
                "non_null": counts(fixtures),
                "source_labels": sorted({r["source"] for r in fixtures}),
                "meaning": "Fixture only, including all populated route values.",
            },
            {
                "path": season_path,
                "rows": len(seasons),
                "WR_rows": len(wr),
                "WR_non_null": counts([r["usage_summary"] for r in wr]),
                "meaning": (
                    "Bounded 2021-2025 historical WR census; not all TIBER lanes or current "
                    "2026 evidence."
                ),
            },
        ],
        catalog_sha256=catalog_digest(),
        terminal_recommendation="prepare_a_small_definition_inspection_layer_over_existing_Data_authority",
        independent_review="pending; builder checks are not independent review",
        prohibited_assumptions=[
            "A documented metric is not available player evidence.",
            "Non-null is not source admission or population completeness.",
            "route_share is not route_participation.",
            "Pass-play participation is not actual routes.",
            (
                "An authentic or signed document is not an admitted observation or "
                "validated hypothesis."
            ),
            (
                "Study IDs, synthetic arithmetic, and draft presence authorize no "
                "consumer or promotion."
            ),
        ],
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("list", "get", "compare", "demo", "audit"))
    parser.add_argument("identifiers", nargs="*")
    args = parser.parse_args()
    arity = {"list": 0, "get": 1, "compare": 2, "demo": 0, "audit": 0}[args.command]
    if len(args.identifiers) != arity:
        parser.error(f"{args.command} requires {arity} identifier(s)")
    result = {
        "list": lambda: catalog(),
        "get": lambda: get_definition(args.identifiers[0]),
        "compare": lambda: compare(*args.identifiers),
        "demo": lambda: demo(),
        "audit": lambda: audit(),
    }[args.command]()
    print(json.dumps(result, indent=2, allow_nan=False))
    return 2 if result["status"] in {"not_indexed", "ambiguous"} else 0


if __name__ == "__main__":
    raise SystemExit(main())

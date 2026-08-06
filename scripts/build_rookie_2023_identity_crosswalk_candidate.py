"""Build the candidate 2023 rookie identity crosswalk for TIBER-Data #237.

The builder is intentionally narrow and fail-closed:

* class membership, GSIS assertions, and Rookies slugs are copied from a
  pinned draft census snapshot;
* TIBER-Data identities are joined only by exact GSIS/player_id equality;
* Forecast rows are attached only through explicit, locator-pinned audit
  assertions and all known edges remain unresolved conflicts; and
* display names and team aliases are never player-identity join keys.

The outputs are candidates.  This module never writes a promoted path and
never reads or mutates a Forecast checkout.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ARTIFACT_ID = "rookie_2023_identity_crosswalk_candidate"
CONFLICT_ARTIFACT_ID = "rookie_2023_identity_conflicts_candidate"
MANIFEST_ARTIFACT_ID = "rookie_2023_identity_crosswalk_candidate_manifest"
SCHEMA_VERSION = "rookie_2023_identity_crosswalk_candidate_v0.1.0"
CONFLICT_SCHEMA_VERSION = "rookie_2023_identity_conflicts_candidate_v0.1.0"
VERSION = "0.1.0"
GENERATED_AT = "2026-08-05T00:00:00Z"

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ASSERTIONS_PATH = ROOT / "data/candidate/identity/rookie_2023_identity_source_assertions_v0.json"
DATA_COVERAGE_PATH = ROOT / "exports/promoted/nfl/player_season_coverage_v0.json"
TIBER_IDENTITY_V1_PATH = ROOT / "exports/promoted/identity_crosswalk/tiber_identity_crosswalk_v1.json"
OUTPUT_DIR = ROOT / "exports/candidates/identity_crosswalk"
CROSSWALK_PATH = OUTPUT_DIR / f"rookie_2023_identity_crosswalk_v{VERSION}.json"
CONFLICT_PATH = OUTPUT_DIR / f"rookie_2023_identity_conflicts_v{VERSION}.json"
MANIFEST_PATH = OUTPUT_DIR / f"rookie_2023_identity_crosswalk_v{VERSION}.manifest.json"

DATA_COVERAGE_SHA256 = "d45f612b207085df00b4b080e4f55ce1abbd060dcbf30b0bee777ff833ddd8ac"
SOURCE_ASSERTIONS_SHA256 = "4c60962d5397b86acd13ed333d155ac9278ec04c3cc6e77c1527064bb3e26084"
DATA_COVERAGE_COMMIT = "711d6ee158d4e3bd116d1df4d76dea282200454d"
DATA_COVERAGE_BLOB = "f7b2918b978d842cd8753a7f3dedd3836934859b"
TIBER_IDENTITY_V1_SHA256 = "5ce5cd3f5dc8fd27c28c5a5fb283431ac648f764c3f8f2b645f6ad924338f263"
TIBER_IDENTITY_V1_COMMIT = "3df598a43e6af41ccf0bbd9db206bc4504b5a8b2"
TIBER_IDENTITY_V1_BLOB = "6d7422b0cd706bac0f42da875fff134702e87e5e"
EXPECTED_POSITION_COUNTS = {"QB": 14, "RB": 18, "TE": 15, "WR": 33}
EXPECTED_MISSING_DATA_IDS = {
    "00-0038406",  # Zack Kuntz
    "00-0038637",  # Max Duggan
    "00-0039046",  # DeWayne McBride
    "00-0039107",  # Stetson Bennett
}

CANONICAL_TEAMS = {
    "ARI", "ATL", "BAL", "BUF", "CAR", "CHI", "CIN", "CLE",
    "DAL", "DEN", "DET", "GB", "HOU", "IND", "JAX", "KC", "LAC",
    "LAR", "LV", "MIA", "MIN", "NE", "NO", "NYG", "NYJ", "PHI",
    "PIT", "SEA", "SF", "TB", "TEN", "WAS",
}

# These rules are directional and source/season scoped.  They are not a
# general string-replacement table and cannot be used for player identity.
DRAFT_TEAM_ALIASES_2023 = {
    "GNB": ("GB", "nflverse-draft-2023-gnb-to-gb"),
    "KAN": ("KC", "nflverse-draft-2023-kan-to-kc"),
    "LVR": ("LV", "nflverse-draft-2023-lvr-to-lv"),
    "NOR": ("NO", "nflverse-draft-2023-nor-to-no"),
    "NWE": ("NE", "nflverse-draft-2023-nwe-to-ne"),
    "SFO": ("SF", "nflverse-draft-2023-sfo-to-sf"),
    "TAM": ("TB", "nflverse-draft-2023-tam-to-tb"),
}

FORECAST_IMPACTED_ARTIFACTS = [
    {
        "path": "src/datasets/seasonal/fixtures/seasonalPprSeedSnapshot.ts",
        "git_blob": "cfbd61f069287b721d660ebd774930de5a0d7c0f",
        "sha256": "3f9862b7b5d1b92bbb777399617c501328fcc00358e665c74c84cf368856f4f2",
        "impact": "primary_scaffold_seed_identity_claims_conflict",
    },
    {
        "path": "data/backtests/seasonal-ppr/seasonal_ppr_predictions.jsonl",
        "git_blob": "53f0152d21164d7bfb3dc463a755bbec1da347d9",
        "sha256": "0955ffbeb750dff5659fbaa115eba4dcc208223a6b3a2859a7256a989ad34c09",
        "impact": "emitted_rows_inherit_conflicting_identity_claims",
    },
    {
        "path": "data/backtests/seasonal-ppr/seasonal_ppr_prediction_explanations.jsonl",
        "git_blob": "be03bdeb6183a1b51e5455197a7b1963d63a01cf",
        "sha256": "f9bf5dac9a6c7be4c65e2f6513b0f590b5a1463ecdf485dea83ccc2042acf323",
        "impact": "derived_explanations_inherit_conflicting_identity_claims",
    },
    {
        "path": "data/backtests/seasonal-ppr/seasonal_ppr_backtest_report.json",
        "git_blob": "0fe175ae72c53a15fb16387e6d05deb7014c6580",
        "sha256": "d7ebadf7f16f8a37de4626c8bb7a9c2a28152e424553caadb1b1184937703bfa",
        "impact": "derived_report_inherits_conflicting_identity_claims",
    },
    {
        "path": "data/fixtures/seasonalPpr/pre_143_baseline_predictions.jsonl",
        "git_blob": "bdfafc6f421c8601033f9d25d8a5bf46b62a35f8",
        "sha256": "d447fe62f910388ec4dbfb4abe58188d02faeef1f09634315f52a1aca40e4c7c",
        "impact": "baseline_fixture_inherits_conflicting_identity_claims",
    },
    {
        "path": "data/fixtures/seasonalPpr/pre_143_baseline_report.json",
        "git_blob": "27aa03928d92044721f713c2d91b6bffaf6726e5",
        "sha256": "01682d6824cb9a28080d45057e8bd9b4cb4c8d32894649ea4c6eade750a9378f",
        "impact": "baseline_report_inherits_conflicting_identity_claims",
    },
    {
        "path": "docs/reports/player-history-experiment-dry-run-matrix-2026-07-02.json",
        "git_blob": "eb00f8aecba21078b5bff1e7a89cfa88fd3f6462",
        "sha256": "b49892b2e4df0de1931a8abb86fe02ae333de14c6858ecfaff389fd03db9b1fa",
        "impact": "limitation_reference_requires_identity_caveat",
    },
    {
        "path": "docs/reports/teamstate-run2-coverage-gate-evaluation-2026-06-29.json",
        "git_blob": "c6c40f8affea9ca0c4228a56d297777f6b2be172",
        "sha256": "2be103540d1e9d40a1633923e8d11a73be994e012facbd9a16965c9933c8eec2",
        "impact": "limitation_reference_requires_identity_caveat",
    },
    {
        "path": "docs/reports/player-history-experiment-dry-run-matrix-2026-07-02.md",
        "git_blob": "891f44e784036987c4c737103b72416f25f5941d",
        "sha256": "4838a23ccad81c744bd3191d3b86b94fa56530723d12cdbdaf1414a56bc7e47f",
        "impact": "lineage_reference_requires_identity_caveat",
    },
    {
        "path": "docs/reports/player-history-production-binding-activation-verification-2026-07-08.json",
        "git_blob": "b1898040cfc1e639571fc0f4e928fb261932ffbf",
        "sha256": "33b5d11940af40a37ffe203e52590ef8743b6ef929e0a5c53c30d1cf1637e0b9",
        "impact": "evaluates_conflicting_raw_ids_requires_limitation",
    },
    {
        "path": "docs/reports/player-history-production-binding-activation-verification-2026-07-08.md",
        "git_blob": "331697eb3e3202aff0582c0a8fa0382ed82d723d",
        "sha256": "648bcec403b5b12098712bd79435c9083a72dc5e01e0a3da1f196ef7b5c0eb06",
        "impact": "evaluates_conflicting_raw_ids_requires_limitation",
    },
    {
        "path": "docs/reports/player-history-production-binding-implementation-2026-07-08.md",
        "git_blob": "987beb736eb69304b95c0f49f54c3de28ab42fa9",
        "sha256": "f6a414e6028a4fddacdc1e8836adf679feef93a0d3b18c28e440c8ac6b06f5e7",
        "impact": "seed_lineage_reference_requires_identity_caveat",
    },
    {
        "path": "docs/reports/player-history-production-binding-review-2026-07-08.json",
        "git_blob": "b57db4f04ad21aee029a7cce5a56a31efd3e36b7",
        "sha256": "a0f156fbd0c567dcaa023012381ab4e095e67b8134bb2a8a0b913fc58f7df96a",
        "impact": "pins_contaminated_seed_lineage_requires_limitation",
    },
    {
        "path": "docs/reports/player-history-production-binding-review-2026-07-08.md",
        "git_blob": "90533da036a6908f906099c87abf20d9a8c47b1e",
        "sha256": "03ff37a67a0f365205323c2f56b7d627e92e887adbbdfbc73fe8e379cfb8a248",
        "impact": "pins_contaminated_seed_lineage_requires_limitation",
    },
    {
        "path": "src/datasets/seasonal/fixtures/tiberDataWeeklyPprScaffold.ts",
        "git_blob": "a49eab995f6cf825ea75b0abdadf21131e496a9c",
        "sha256": "4e75305f9ab4a52ac218aeaecba08fafa746cded369412ece9c94e0cf8b68e89",
        "impact": "direct_seed_consumer_code_review_boundary",
    },
    {
        "path": "src/datasets/seasonal/tiberDataSeasonalPprDataset.ts",
        "git_blob": "ee846d226d3cd395c151c2609a8a56acbc9742ae",
        "sha256": "5f2b843dc3fc763807df6786066ff5e78aaf1c321ff9998cb5c11d829fedc763",
        "impact": "scaffold_consumer_code_review_boundary",
    },
]


class BuildFailure(RuntimeError):
    """Raised when a source pin or fail-closed invariant is violated."""


def serialize(payload: Any) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, allow_nan=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def canonical_bytes(payload: Any) -> bytes:
    return json.dumps(payload, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def load_json(path: Path) -> tuple[dict[str, Any], bytes]:
    raw = path.read_bytes()
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise BuildFailure(f"invalid JSON at {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise BuildFailure(f"expected object at {path}")
    return payload, raw


def normalize_team_code(raw_code: str, *, source_namespace: str, season: int) -> tuple[str, str]:
    """Return canonical team and applied rule, rejecting unscoped aliases."""

    if not isinstance(raw_code, str) or not raw_code:
        raise BuildFailure("team code must be a non-empty string")
    if raw_code in CANONICAL_TEAMS:
        return raw_code, "canonical-code-idempotent"
    if (
        source_namespace == "tiber_data_player_season"
        and raw_code == "LA"
        and season in {2023, 2024, 2025}
    ):
        return "LAR", "tiber-data-candidate-la-to-lar-supported-2023-2025"
    if source_namespace == "nflverse_draft_results" and season == 2023:
        mapped = DRAFT_TEAM_ALIASES_2023.get(raw_code)
        if mapped:
            return mapped
    raise BuildFailure(
        f"unrecognized or unscoped team alias {raw_code!r} for {source_namespace!r}, season {season}"
    )


def _data_index(data_payload: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    records = data_payload.get("records")
    if not isinstance(records, list):
        raise BuildFailure("promoted Data coverage records must be an array")
    result: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in records:
        if not isinstance(row, dict):
            raise BuildFailure("promoted Data coverage contains a non-object row")
        player_id = row.get("player_id")
        if isinstance(player_id, str) and row.get("identity_confidence") == "source_verified":
            result[player_id].append(row)
    return result


def _team_contexts(data_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    contexts: list[dict[str, Any]] = []
    for row in sorted(data_rows, key=lambda value: int(value["season"])):
        season = int(row["season"])
        raw_teams = sorted({value for value in row.get("teams", []) if isinstance(value, str)})
        canonical_teams = sorted(
            {normalize_team_code(value, source_namespace="tiber_data_player_season", season=season)[0] for value in raw_teams}
        )
        raw_primary = row.get("primary_team") if isinstance(row.get("primary_team"), str) else None
        canonical_primary = (
            normalize_team_code(raw_primary, source_namespace="tiber_data_player_season", season=season)[0]
            if raw_primary
            else None
        )
        contexts.append(
            {
                "season": season,
                "season_type": row.get("season_type"),
                "raw_teams": raw_teams,
                "canonical_teams": canonical_teams,
                "raw_primary_team": raw_primary,
                "canonical_primary_team": canonical_primary,
                "source_ref": "tiber-data-player-season-coverage-v0",
            }
        )
    return contexts


def _source_assertion_ref(assertion: dict[str, Any], forecast_refs: dict[str, Any]) -> dict[str, Any]:
    result = {
        "assertion_id": assertion["assertion_id"],
        "assertion_kind": assertion["assertion_kind"],
        "source_repository": forecast_refs["repository"],
        "source_commit": forecast_refs["git_commit"],
        "seed_path": forecast_refs["seed"]["path"],
        "seed_row_index_zero_based": assertion["seed_row_index_zero_based"],
        "seed_source_line_sha256": assertion["seed_source_line_sha256"],
        "prediction_path": forecast_refs["emitted_predictions"]["path"],
        "prediction_jsonl_line_one_based": assertion["prediction_jsonl_line_one_based"],
        "prediction_source_line_sha256": assertion["prediction_source_line_sha256"],
        "forecast_raw_player_id": assertion["forecast_raw_player_id"],
        "forecast_display_name_audit_only": assertion["forecast_display_name_audit_only"],
        "forecast_position_audit_only": assertion["forecast_position_audit_only"],
        "association_method": assertion["association_method"],
        "resolution_effect": "none",
    }
    if "association_status" in assertion:
        result["association_status"] = assertion["association_status"]
    if "non_name_fingerprint" in assertion:
        result["non_name_fingerprint"] = assertion["non_name_fingerprint"]
    return result


def _data_non_name_fingerprint(row: dict[str, Any]) -> dict[str, Any]:
    season = int(row["season"])
    primary_team = row.get("primary_team")
    if not isinstance(primary_team, str):
        raise BuildFailure("fingerprint source row lacks a primary team")
    usage = row.get("usage_summary")
    if not isinstance(usage, dict):
        raise BuildFailure("fingerprint source row lacks a usage summary")
    return {
        "season": season,
        "position": row.get("position"),
        "canonical_team": normalize_team_code(
            primary_team,
            source_namespace="tiber_data_player_season",
            season=season,
        )[0],
        "games_played": row.get("games_played"),
        "receptions": usage.get("receptions"),
        "targets": usage.get("targets"),
    }


def _forecast_indexes(
    assertions: list[dict[str, Any]],
    census_ids: set[str],
    forecast_refs: dict[str, Any],
    data_by_id: dict[str, list[dict[str, Any]]],
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, list[dict[str, Any]]], list[dict[str, Any]]]:
    subject_by_target: dict[str, list[dict[str, Any]]] = defaultdict(list)
    collision_by_target: dict[str, list[dict[str, Any]]] = defaultdict(list)
    conflict_findings: list[dict[str, Any]] = []
    seen_assertions: set[str] = set()

    for assertion in assertions:
        assertion_id = assertion.get("assertion_id")
        if not isinstance(assertion_id, str) or assertion_id in seen_assertions:
            raise BuildFailure(f"duplicate or invalid Forecast assertion_id: {assertion_id!r}")
        seen_assertions.add(assertion_id)
        target = assertion.get("target_gsis_id")
        if target not in census_ids:
            raise BuildFailure(f"Forecast assertion {assertion_id} targets unknown census GSIS {target!r}")
        ref = _source_assertion_ref(assertion, forecast_refs)
        kind = assertion.get("assertion_kind")
        if kind == "subject_identity_conflict":
            if assertion.get("forecast_raw_player_id") == target:
                raise BuildFailure(f"Forecast subject conflict {assertion_id} is not a conflict")
            if assertion.get("association_method") != "explicit_candidate_override_unique_non_name_fingerprint":
                raise BuildFailure(f"Forecast subject assertion {assertion_id} lacks an explicit non-name override")
            if assertion.get("association_status") != "needs_operator_review":
                raise BuildFailure(f"Forecast subject assertion {assertion_id} must remain needs_operator_review")
            expected_fingerprint = assertion.get("non_name_fingerprint")
            if not isinstance(expected_fingerprint, dict):
                raise BuildFailure(f"Forecast subject assertion {assertion_id} lacks fingerprint lineage")
            matching_data_ids: set[str] = set()
            for data_player_id, player_rows in data_by_id.items():
                for data_row in player_rows:
                    if int(data_row.get("season", -1)) != 2024:
                        continue
                    if _data_non_name_fingerprint(data_row) == expected_fingerprint:
                        matching_data_ids.add(data_player_id)
            if matching_data_ids != {target}:
                raise BuildFailure(
                    f"Forecast subject assertion {assertion_id} fingerprint is not unique to target: "
                    f"{sorted(matching_data_ids)}"
                )
            subject_by_target[target].append(ref)
            conflict_findings.append(
                {
                    "conflict_id": f"subject-{assertion_id}",
                    "conflict_type": "forecast_subject_raw_id_mismatch",
                    "affected_gsis_id": target,
                    "source_assertion": ref,
                    "governed_assertion": {"gsis_id": target},
                    "status": "unresolved",
                    "resolution": None,
                    "blocked_edge": "forecast_row_to_core_identity",
                }
            )
            raw_id = assertion["forecast_raw_player_id"]
            if raw_id in census_ids:
                collision_ref = {**ref, "collision_origin": "subject_conflict_raw_id"}
                collision_by_target[raw_id].append(collision_ref)
                conflict_findings.append(
                    {
                        "conflict_id": f"collision-{assertion_id}",
                        "conflict_type": "forecast_raw_id_assigned_to_different_census_identity",
                        "affected_gsis_id": raw_id,
                        "source_assertion": collision_ref,
                        "governed_assertion": {"gsis_id": raw_id},
                        "status": "unresolved",
                        "resolution": None,
                        "blocked_edge": "forecast_raw_id_to_core_identity",
                    }
                )
        elif kind == "canonical_id_assigned_to_other_subject":
            if assertion.get("forecast_raw_player_id") != target:
                raise BuildFailure(f"Forecast collision assertion {assertion_id} must key exact raw GSIS")
            collision_by_target[target].append(ref)
            conflict_findings.append(
                {
                    "conflict_id": f"collision-{assertion_id}",
                    "conflict_type": "forecast_raw_id_assigned_to_different_census_identity",
                    "affected_gsis_id": target,
                    "source_assertion": ref,
                    "governed_assertion": {"gsis_id": target},
                    "status": "unresolved",
                    "resolution": None,
                    "blocked_edge": "forecast_raw_id_to_core_identity",
                }
            )
        else:
            raise BuildFailure(f"unsupported Forecast assertion kind {kind!r}")

    return subject_by_target, collision_by_target, sorted(conflict_findings, key=lambda row: row["conflict_id"])


def build_payloads() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    source, source_raw = load_json(SOURCE_ASSERTIONS_PATH)
    data, data_raw = load_json(DATA_COVERAGE_PATH)
    tiber_identity_v1, tiber_identity_v1_raw = load_json(TIBER_IDENTITY_V1_PATH)
    if sha256(source_raw) != SOURCE_ASSERTIONS_SHA256:
        raise BuildFailure("identity source assertion snapshot does not match the pinned content hash")
    if sha256(data_raw) != DATA_COVERAGE_SHA256:
        raise BuildFailure("promoted Data coverage content hash does not match the pinned source")
    if sha256(tiber_identity_v1_raw) != TIBER_IDENTITY_V1_SHA256:
        raise BuildFailure("promoted TIBER identity V1 content hash does not match the pinned source")
    if any("gsis_id" in row for row in tiber_identity_v1.get("records", []) if isinstance(row, dict)):
        raise BuildFailure("TIBER identity V1 unexpectedly changed to include a GSIS edge; review required")

    census = source.get("records")
    assertions = source.get("forecast_row_assertions")
    forecast_refs = source.get("forecast_source_refs")
    overrides = source.get("explicit_name_overrides")
    if not isinstance(census, list) or not isinstance(assertions, list):
        raise BuildFailure("source assertion snapshot is missing census or Forecast assertions")
    if not isinstance(forecast_refs, dict) or not isinstance(overrides, list):
        raise BuildFailure("source assertion snapshot is missing Forecast pins or overrides")
    if len(census) != 80:
        raise BuildFailure(f"expected 80 census rows, found {len(census)}")

    census_ids = {row.get("gsis_id") for row in census if isinstance(row, dict)}
    if None in census_ids or len(census_ids) != 80:
        raise BuildFailure("census GSIS IDs must be present and unique")
    data_by_id = _data_index(data)
    subject_by_target, collision_by_target, conflict_findings = _forecast_indexes(
        assertions, census_ids, forecast_refs, data_by_id
    )
    override_by_id = defaultdict(list)
    for override in overrides:
        override_by_id[override["key_value"]].append(override["override_id"])

    rows: list[dict[str, Any]] = []
    for census_row in sorted(census, key=lambda row: int(row["overall_pick"])):
        gsis_id = census_row["gsis_id"]
        data_rows = data_by_id.get(gsis_id, [])
        seasons = sorted({int(row["season"]) for row in data_rows})
        if 2023 in seasons:
            data_status = "exact_gsis_source_verified_in_2023_reg"
        elif data_rows:
            data_status = "exact_gsis_source_verified_in_later_promoted_reg_only"
        else:
            data_status = "unresolved_no_governed_data_record"
        canonical_team, team_rule = normalize_team_code(
            census_row["draft_team_source_code"],
            source_namespace="nflverse_draft_results",
            season=2023,
        )
        data_draft_years = sorted({row.get("draft_year") for row in data_rows})
        data_draft_picks = sorted({row.get("draft_pick") for row in data_rows})
        data_raw_draft_teams = sorted({row.get("draft_team") for row in data_rows if isinstance(row.get("draft_team"), str)})
        data_canonical_draft_teams = sorted(
            {
                normalize_team_code(value, source_namespace="tiber_data_player_season", season=2023)[0]
                for value in data_raw_draft_teams
            }
        )
        if data_rows and (
            data_draft_years != [2023]
            or data_draft_picks != [census_row["overall_pick"]]
            or data_canonical_draft_teams != [canonical_team]
        ):
            raise BuildFailure(
                f"exact-GSIS Data row contradicts draft metadata for {gsis_id}: "
                f"years={data_draft_years}, picks={data_draft_picks}, teams={data_canonical_draft_teams}"
            )
        subject_assertions = subject_by_target.get(gsis_id, [])
        collision_assertions = collision_by_target.get(gsis_id, [])
        forecast_status = "conflict_blocked" if subject_assertions or collision_assertions else "not_present"
        data_names = sorted({row["player_name"] for row in data_rows if isinstance(row.get("player_name"), str)})
        data_positions = sorted({row["position"] for row in data_rows if isinstance(row.get("position"), str)})
        variances: list[dict[str, Any]] = []
        if data_names and data_names != [census_row["player_name"]]:
            variances.append(
                {
                    "field": "display_name",
                    "rookies_value_audit_only": census_row["player_name"],
                    "data_values_audit_only": data_names,
                    "identity_effect": "none",
                }
            )
        if data_positions and data_positions != [census_row["position"]]:
            variances.append(
                {
                    "field": "position_context",
                    "rookies_draft_value": census_row["position"],
                    "data_historical_values": data_positions,
                    "identity_effect": "none",
                }
            )

        rows.append(
            {
                "crosswalk_row_id": f"rookie-2023-gsis-{gsis_id}",
                "draft_class": 2023,
                "overall_pick": census_row["overall_pick"],
                "player_name_audit_only": census_row["player_name"],
                "draft_position_audit_only": census_row["position"],
                "core_identity": {
                    "gsis_id": gsis_id,
                    "gsis_status": "source_asserted_pinned_rookies_draft_census",
                    "rookies_slug": census_row["rookies_slug"],
                    "rookies_slug_status": census_row["rookies_slug_status"],
                    "tiber_data_source_player_id": gsis_id if data_rows else None,
                    "tiber_data_source_player_id_status": data_status,
                    "tiber_canonical_player_id": None,
                    "tiber_canonical_identity_status": "unresolved_no_admissible_gsis_to_tiber_player_id_edge",
                    "tiber_canonical_namespace": "TIBER_IDENTITY_CROSSWALK_V1.tiber_player_id",
                    "join_method": "exact_gsis_only",
                    "display_name_join_used": False,
                    "data_identity_corroboration": {
                        "status": "exact_gsis_and_draft_metadata_agree" if data_rows else "unavailable_no_governed_data_record",
                        "draft_year_values": data_draft_years,
                        "draft_pick_values": data_draft_picks,
                        "raw_draft_team_values": data_raw_draft_teams,
                        "canonical_draft_team_values": data_canonical_draft_teams,
                    },
                },
                "draft_team": {
                    "source_namespace": "nflverse_draft_results",
                    "source_season": 2023,
                    "raw_code": census_row["draft_team_source_code"],
                    "canonical_code": canonical_team,
                    "normalization_rule_id": team_rule,
                },
                "data_history_audit_context": {
                    "source_player_id": gsis_id if data_rows else None,
                    "observed_seasons": seasons,
                    "display_names_audit_only": data_names,
                    "positions_audit_only": data_positions,
                    "team_contexts": _team_contexts(data_rows),
                    "descriptor_variances": variances,
                },
                "forecast_link": {
                    "status": forecast_status,
                    "resolved_forecast_row_identity": None,
                    "subject_assertions": subject_assertions,
                    "canonical_id_collision_assertions": collision_assertions,
                    "auto_resolution_allowed": False,
                    "display_name_join_allowed": False,
                },
                "identity_aliases": [],
                "explicit_override_ids": sorted(override_by_id.get(gsis_id, [])),
                "source_refs": ["rookies-2023-draft-census", "tiber-data-player-season-coverage-v0"],
            }
        )

    position_counts = dict(sorted(Counter(row["draft_position_audit_only"] for row in rows).items()))
    data_status_counts = dict(sorted(Counter(row["core_identity"]["tiber_data_source_player_id_status"] for row in rows).items()))
    subject_conflicted_ids = {row["affected_gsis_id"] for row in conflict_findings if row["conflict_type"] == "forecast_subject_raw_id_mismatch"}
    affected_ids = {row["affected_gsis_id"] for row in conflict_findings}
    unique_forecast_assertion_ids = {row["source_assertion"]["assertion_id"] for row in conflict_findings}
    draft_alias_counts = Counter(
        (row["draft_team"]["raw_code"], row["draft_team"]["canonical_code"])
        for row in rows
        if row["draft_team"]["raw_code"] != row["draft_team"]["canonical_code"]
    )
    rams_alias_evidence_count = sum(
        "LA" in row["core_identity"]["data_identity_corroboration"]["raw_draft_team_values"]
        and row["draft_team"]["canonical_code"] == "LAR"
        for row in rows
    )

    crosswalk = {
        "artifact_id": ARTIFACT_ID,
        "schema_version": SCHEMA_VERSION,
        "crosswalk_version": VERSION,
        "status": "candidate_partial_source_identity_ready_tiber_canonical_namespace_blocked",
        "generated_at": GENERATED_AT,
        "issue": "Prometheus-Frameworks/TIBER-Data#237",
        "promotion_authorized": False,
        "forecast_mutation_authorized": False,
        "join_contract": {
            "allowed_player_join_keys": ["gsis_id", "crosswalk_row_id", "explicit_source_row_assertion_id"],
            "forbidden_player_join_keys": ["display_name", "normalized_display_name", "fuzzy_name"],
            "display_names_are": "audit_descriptors_only",
            "conflicts": "fail_closed_no_auto_resolution",
            "consumer_requirement": "verify_crosswalk_version_and_sha256_before_use",
        },
        "source_artifacts": [
            {
                "source_ref_id": "rookies-2023-draft-census",
                **source["source_ref"],
                "local_assertion_snapshot_path": str(SOURCE_ASSERTIONS_PATH.relative_to(ROOT)),
                "local_assertion_snapshot_sha256": sha256(source_raw),
            },
            {
                "source_ref_id": "tiber-data-player-season-coverage-v0",
                "repository": "Prometheus-Frameworks/TIBER-Data",
                "git_commit": DATA_COVERAGE_COMMIT,
                "path": str(DATA_COVERAGE_PATH.relative_to(ROOT)),
                "git_blob": DATA_COVERAGE_BLOB,
                "sha256": DATA_COVERAGE_SHA256,
                "source_status": "promoted_governed_artifact",
            },
            {
                "source_ref_id": "tiber-identity-crosswalk-v1",
                "repository": "Prometheus-Frameworks/TIBER-Data",
                "git_commit": TIBER_IDENTITY_V1_COMMIT,
                "path": str(TIBER_IDENTITY_V1_PATH.relative_to(ROOT)),
                "git_blob": TIBER_IDENTITY_V1_BLOB,
                "sha256": TIBER_IDENTITY_V1_SHA256,
                "source_status": "promoted_governed_sleeper_to_tiber_crosswalk_no_gsis_field",
            },
            {
                "source_ref_id": "forecast-run1-scaffold",
                **forecast_refs,
            },
        ],
        "canonical_team_code_policy": {
            "policy_version": "rookie-2023-team-code-candidate-v0.1.0",
            "canonical_rams_code": "LAR",
            "rams_alias_policy": {
                "canonical": "LAR",
                "accepted_alias": "LA",
                "direction": "LA_to_LAR_only",
                "requires_source_namespace": "tiber_data_player_season",
                "supported_source_seasons": [2023, 2024, 2025],
                "support_scope_basis": "candidate_observed_2023_class_data_history_not_franchise_history_claim",
                "lac_is_distinct": True,
                "reverse_emission_allowed": False,
                "exact_gsis_draft_metadata_evidence_count": rams_alias_evidence_count,
                "evidence_source_refs": ["rookies-2023-draft-census", "tiber-data-player-season-coverage-v0"],
                "lineage": {
                    "repository": "Prometheus-Frameworks/TIBER-Data",
                    "git_commit": "2b3ae259742f695e99bdadbd00caee903112064e",
                    "path": "scripts/build_team_week_raw_v0_2024_candidate.py",
                    "git_blob": "0472f52d21523083d3d0cdd462edfe7365145f58",
                    "sha256": "d781691a1e4619854eb0007a282d7429cc6ffcd1c98865fadbbf181ba12787bc",
                },
            },
            "draft_source_aliases_2023": [
                {
                    "raw": raw,
                    "canonical": value[0],
                    "rule_id": value[1],
                    "scope": "nflverse_draft_results:2023",
                    "exact_gsis_draft_metadata_evidence_count": draft_alias_counts[(raw, value[0])],
                    "evidence_source_refs": ["rookies-2023-draft-census", "tiber-data-player-season-coverage-v0"],
                }
                for raw, value in sorted(DRAFT_TEAM_ALIASES_2023.items())
            ],
            "unknown_or_unscoped_alias_behavior": "fail_closed",
            "raw_code_preservation_required": True,
            "team_codes_are_player_join_keys": False,
        },
        "explicit_name_overrides": overrides,
        "forecast_subject_override_policy": source["forecast_subject_override_policy"],
        "coverage_summary": {
            "row_count": len(rows),
            "position_counts": position_counts,
            "rookies_slug_status_counts": dict(sorted(Counter(row["core_identity"]["rookies_slug_status"] for row in rows).items())),
            "tiber_data_source_player_id_status_counts": data_status_counts,
            "tiber_data_source_player_id_exact_gsis_resolved_count": sum(row["core_identity"]["tiber_data_source_player_id"] is not None for row in rows),
            "tiber_data_source_player_id_unresolved_count": sum(row["core_identity"]["tiber_data_source_player_id"] is None for row in rows),
            "tiber_canonical_player_id_resolved_count": 0,
            "tiber_canonical_player_id_unresolved_count": len(rows),
            "forecast_subject_link_counts": {"resolved": 0, "conflict_blocked": len(subject_conflicted_ids), "not_present": len(rows) - len(subject_conflicted_ids)},
            "forecast_census_risk_counts": {"conflict_blocked": len(affected_ids), "no_known_run1_subject_or_collision": len(rows) - len(affected_ids)},
            "forecast_unique_source_rows_with_conflicts": len(unique_forecast_assertion_ids),
            "forecast_conflict_findings": len(conflict_findings),
        },
        "consumer_readiness": {
            "source_identity_edge_for_236_pilot": "exact_gsis_to_data_source_player_id_ready_for_bounded_pilot",
            "full_tiber_canonical_crosswalk": "rookie_2023_identity_crosswalk_blocked",
            "forecast_edges": "blocked_all_observed_edges_conflict",
            "emitted_forecast_artifacts": "emitted_artifact_identity_remediation_requires_operator_decision",
        },
        "records": rows,
    }

    crosswalk_sha = sha256(serialize(crosswalk))
    conflict_report = {
        "artifact_id": CONFLICT_ARTIFACT_ID,
        "schema_version": CONFLICT_SCHEMA_VERSION,
        "crosswalk_version": VERSION,
        "status": "candidate_explicit_unresolved_conflicts",
        "generated_at": GENERATED_AT,
        "issue": "Prometheus-Frameworks/TIBER-Data#237",
        "crosswalk_ref": {"path": str(CROSSWALK_PATH.relative_to(ROOT)), "sha256": crosswalk_sha},
        "summary": {
            "subject_identity_conflicts": len(subject_conflicted_ids),
            "raw_id_collision_findings": sum(row["conflict_type"] == "forecast_raw_id_assigned_to_different_census_identity" for row in conflict_findings),
            "unique_forecast_source_rows": len(unique_forecast_assertion_ids),
            "affected_census_rows": len(affected_ids),
            "resolved_conflicts": 0,
            "open_conflicts": len(conflict_findings),
        },
        "puka_required_conflict": {
            "forecast_raw_gsis": "00-0038543",
            "governed_gsis": "00-0039075",
            "status": "unresolved_fail_closed",
            "resolution": None,
            "note": "00-0038543 remains the governed GSIS for Jaxon Smith-Njigba; it is never a Puka alias.",
        },
        "tiber_canonical_namespace_gap": {
            "governed_namespace": "TIBER_IDENTITY_CROSSWALK_V1.tiber_player_id",
            "source_artifact": {
                "path": str(TIBER_IDENTITY_V1_PATH.relative_to(ROOT)),
                "sha256": TIBER_IDENTITY_V1_SHA256,
            },
            "gsis_field_present_in_source": False,
            "admissible_gsis_to_tiber_player_id_links": 0,
            "unresolved_census_rows": len(rows),
            "status": "blocked_no_non_name_cross_namespace_edge",
            "note": "Sleeper-only V1 descriptors cannot be joined to this census by display name; no candidate TIBER ID is minted.",
        },
        "conflicts": conflict_findings,
        "impacted_artifact_inventory": {
            "tiber_forecast": {
                "repository": "Prometheus-Frameworks/TIBER-Forecast",
                "git_commit": forecast_refs["git_commit"],
                "inventory_scope": "bounded_direct_and_reference_inventory_not_a_full_transitive_dependency_graph",
                "discovery_rule": "paths at the pinned commit matching the seed path, scaffold dataset version, or known conflicting raw IDs within seasonal source, backtest fixtures, and reports",
                "known_gap_behavior": "additional_transitive_consumers_need_verification",
                "artifacts": FORECAST_IMPACTED_ARTIFACTS,
                "mutation_authorized": False,
            },
            "tiber_rookies": [
                {
                    "path": source["source_ref"]["path"],
                    "sha256": source["source_ref"]["sha256"],
                    "status": "draft_census_source_do_not_mutate_from_data_issue",
                }
            ],
            "tiber_data": [
                {
                    "path": "exports/promoted/identity_crosswalk/tiber_identity_crosswalk_v1.json",
                    "sha256": TIBER_IDENTITY_V1_SHA256,
                    "status": "governed_tiber_id_namespace_but_not_admissible_for_gsis_join_sleeper_only_no_mutation",
                },
                {
                    "path": str(DATA_COVERAGE_PATH.relative_to(ROOT)),
                    "sha256": DATA_COVERAGE_SHA256,
                    "status": "governed_exact_gsis_source_read_only",
                },
            ],
        },
        "recommended_remediation_sequence": [
            "pilot_source_identity_consumers_may_use_only_exact_gsis_to_data_source_player_id_edges_after_version_and_hash_verification",
            "operator_defines_or_sources_a_non_name_gsis_to_tiber_player_id_edge_before_full_crosswalk_readiness",
            "keep_every_forecast_edge_blocked_and_publish_limitation_record",
            "operator_decides_correction_supersession_or_limitation_for_already_emitted_forecast_artifacts",
            "separate_authority_required_before_any_forecast_mutation_or_rerun",
        ],
        "open_operator_decisions": [
            "durable_gsis_to_tiber_player_id_namespace_edge",
            "disposition_of_already_emitted_forecast_artifacts",
            "promotion_or_governance_status_of_this_candidate_crosswalk",
        ],
    }

    conflict_sha = sha256(serialize(conflict_report))
    manifest = {
        "artifact_id": MANIFEST_ARTIFACT_ID,
        "crosswalk_version": VERSION,
        "status": "candidate_manifest_not_promotion",
        "generated_at": GENERATED_AT,
        "artifacts": [
            {"path": str(CROSSWALK_PATH.relative_to(ROOT)), "sha256": crosswalk_sha},
            {"path": str(CONFLICT_PATH.relative_to(ROOT)), "sha256": conflict_sha},
        ],
        "inputs": [
            {"path": str(SOURCE_ASSERTIONS_PATH.relative_to(ROOT)), "sha256": sha256(source_raw)},
            {"path": str(DATA_COVERAGE_PATH.relative_to(ROOT)), "sha256": DATA_COVERAGE_SHA256},
            {"path": str(TIBER_IDENTITY_V1_PATH.relative_to(ROOT)), "sha256": TIBER_IDENTITY_V1_SHA256},
        ],
        "downstream_binding": {
            "required_version": VERSION,
            "required_crosswalk_sha256": crosswalk_sha,
            "fail_on_mismatch": True,
            "allowed_identity_edge": "gsis_to_tiber_data_source_player_id",
            "tiber_canonical_player_id_edge_authorized": False,
        },
        "promotion_authorized": False,
    }
    return crosswalk, conflict_report, manifest


def write_outputs() -> None:
    crosswalk, conflicts, manifest = build_payloads()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    CROSSWALK_PATH.write_bytes(serialize(crosswalk))
    CONFLICT_PATH.write_bytes(serialize(conflicts))
    MANIFEST_PATH.write_bytes(serialize(manifest))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    write_outputs()
    print(f"wrote {CROSSWALK_PATH.relative_to(ROOT)}")
    print(f"wrote {CONFLICT_PATH.relative_to(ROOT)}")
    print(f"wrote {MANIFEST_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

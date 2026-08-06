"""Validate the candidate 2023 rookie identity crosswalk for issue #237."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any

try:
    from scripts.build_rookie_2023_identity_crosswalk_candidate import (
        ARTIFACT_ID,
        CONFLICT_ARTIFACT_ID,
        CONFLICT_PATH,
        CROSSWALK_PATH,
        EXPECTED_MISSING_DATA_IDS,
        EXPECTED_POSITION_COUNTS,
        FORECAST_IMPACTED_ARTIFACTS,
        GENERATED_AT,
        MANIFEST_ARTIFACT_ID,
        MANIFEST_PATH,
        ROOT,
        SCHEMA_VERSION,
        SOURCE_ASSERTIONS_PATH,
        DATA_COVERAGE_COMMIT,
        DATA_COVERAGE_PATH,
        DATA_COVERAGE_SHA256,
        TIBER_IDENTITY_V1_COMMIT,
        TIBER_IDENTITY_V1_PATH,
        TIBER_IDENTITY_V1_SHA256,
        VERSION,
        BuildFailure,
        build_payloads,
        normalize_team_code,
        serialize,
        sha256,
    )
except ModuleNotFoundError:  # Direct script execution.
    from build_rookie_2023_identity_crosswalk_candidate import (  # type: ignore[no-redef]
        ARTIFACT_ID,
        CONFLICT_ARTIFACT_ID,
        CONFLICT_PATH,
        CROSSWALK_PATH,
        EXPECTED_MISSING_DATA_IDS,
        EXPECTED_POSITION_COUNTS,
        FORECAST_IMPACTED_ARTIFACTS,
        GENERATED_AT,
        MANIFEST_ARTIFACT_ID,
        MANIFEST_PATH,
        ROOT,
        SCHEMA_VERSION,
        SOURCE_ASSERTIONS_PATH,
        DATA_COVERAGE_COMMIT,
        DATA_COVERAGE_PATH,
        DATA_COVERAGE_SHA256,
        TIBER_IDENTITY_V1_COMMIT,
        TIBER_IDENTITY_V1_PATH,
        TIBER_IDENTITY_V1_SHA256,
        VERSION,
        BuildFailure,
        build_payloads,
        normalize_team_code,
        serialize,
        sha256,
    )

VALIDATION_PATH = ROOT / f"exports/candidates/identity_crosswalk/rookie_2023_identity_crosswalk_v{VERSION}.validation.json"
FORBIDDEN_METRIC_KEYS = {
    "actual_ppr",
    "absolute_error",
    "coefficient",
    "feature_contributions",
    "input_value",
    "ppr_2024",
    "ppr_2025_actual",
    "predicted_ppr",
    "projection",
    "rank",
    "recommendation",
}


class ValidationFailure(RuntimeError):
    """Raised when the candidate violates its fail-closed contract."""


def _load(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_bytes())
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationFailure(f"cannot read JSON artifact {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValidationFailure(f"artifact must be an object: {path}")
    return payload


def _git_blob(repo_root: Path, commit: str, path: str) -> bytes:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "show", f"{commit}:{path}"],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise ValidationFailure(f"cannot read {repo_root}@{commit}:{path}: {detail}")
    return result.stdout


def forecast_seed_non_name_fingerprint(seed_line: str) -> dict[str, Any]:
    """Extract only the admitted non-name binding fields from one TS seed row."""

    patterns = {
        "position": r"\bposition:\s*'([^']+)'",
        "team": r"\bteam_2024:\s*'([^']+)'",
        "games_played": r"\bgames_2024:\s*(\d+)",
        "receptions": r"\breceptions_2024:\s*(\d+)",
        "targets": r"\btargets_2024:\s*(\d+)",
    }
    values: dict[str, str] = {}
    for field, pattern in patterns.items():
        match = re.search(pattern, seed_line)
        if match is None:
            raise ValidationFailure(f"Forecast seed row lacks fingerprint field {field}")
        values[field] = match.group(1)
    canonical_team, _ = normalize_team_code(
        values["team"],
        source_namespace="forecast_seasonal_seed",
        season=2024,
    )
    return {
        "season": 2024,
        "position": values["position"],
        "canonical_team": canonical_team,
        "games_played": int(values["games_played"]),
        "receptions": int(values["receptions"]),
        "targets": int(values["targets"]),
    }


def validate_forecast_assertion_seed_binding(
    assertion: dict[str, Any], seed_line: str
) -> list[str]:
    assertion_id = assertion.get("assertion_id")
    if assertion.get("assertion_kind") != "subject_identity_conflict":
        return []
    try:
        extracted = forecast_seed_non_name_fingerprint(seed_line)
    except (ValidationFailure, BuildFailure) as exc:
        return [f"Forecast seed fingerprint extraction failed for {assertion_id}: {exc}"]
    if assertion.get("non_name_fingerprint") != extracted:
        return [
            f"Forecast assertion fingerprint differs from pinned seed row for {assertion_id}: "
            f"asserted={assertion.get('non_name_fingerprint')}, extracted={extracted}"
        ]
    return []


def validate_cross_repo_sources(rookies_repo_root: Path, forecast_repo_root: Path) -> list[str]:
    """Reproduce every external pin and exact Forecast row locator."""

    errors: list[str] = []
    assertions = _load(SOURCE_ASSERTIONS_PATH)
    rookies_ref = assertions["source_ref"]
    try:
        rookies_raw = _git_blob(
            rookies_repo_root,
            rookies_ref["git_commit"],
            rookies_ref["path"],
        )
    except ValidationFailure as exc:
        errors.append(str(exc))
    else:
        if sha256(rookies_raw) != rookies_ref["sha256"]:
            errors.append("pinned Rookies census cross-repo hash mismatch")
        else:
            upstream = json.loads(rookies_raw)
            expected_projection = [
                {
                    "overall_pick": row["overall_pick"],
                    "player_name": row["player_name"],
                    "position": row["position"],
                    "rookies_slug": row["canonical_player_id"],
                    "rookies_slug_status": row["canonical_id_status"],
                    "gsis_id": row["gsis_id"],
                    "draft_team_source_code": row["draft_team"],
                }
                for row in upstream.get("players", [])
            ]
            if assertions.get("records") != expected_projection:
                errors.append("local 80-row assertion projection differs from the pinned Rookies census")

    for override in assertions.get("explicit_name_overrides", []):
        for lineage in override.get("lineage", []):
            try:
                raw = _git_blob(rookies_repo_root, lineage["git_commit"], lineage["path"])
            except ValidationFailure as exc:
                errors.append(str(exc))
            else:
                if sha256(raw) != lineage["sha256"]:
                    errors.append(f"name-override lineage hash mismatch: {lineage['path']}")

    for commit, path, expected_hash, label in (
        (DATA_COVERAGE_COMMIT, str(DATA_COVERAGE_PATH.relative_to(ROOT)), DATA_COVERAGE_SHA256, "Data coverage"),
        (TIBER_IDENTITY_V1_COMMIT, str(TIBER_IDENTITY_V1_PATH.relative_to(ROOT)), TIBER_IDENTITY_V1_SHA256, "TIBER identity V1"),
    ):
        try:
            raw = _git_blob(ROOT, commit, path)
        except ValidationFailure as exc:
            errors.append(str(exc))
        else:
            if sha256(raw) != expected_hash:
                errors.append(f"{label} immutable git-blob hash mismatch")

    crosswalk = _load(CROSSWALK_PATH)
    team_lineage = crosswalk["canonical_team_code_policy"]["rams_alias_policy"]["lineage"]
    try:
        raw = _git_blob(ROOT, team_lineage["git_commit"], team_lineage["path"])
    except ValidationFailure as exc:
        errors.append(str(exc))
    else:
        if sha256(raw) != team_lineage["sha256"]:
            errors.append("Rams alias implementation-lineage hash mismatch")

    forecast_refs = assertions["forecast_source_refs"]
    forecast_commit = forecast_refs["git_commit"]
    external_files: dict[str, bytes] = {}
    for role in ("seed", "emitted_predictions"):
        ref = forecast_refs[role]
        try:
            raw = _git_blob(forecast_repo_root, forecast_commit, ref["path"])
        except ValidationFailure as exc:
            errors.append(str(exc))
            continue
        external_files[ref["path"]] = raw
        if sha256(raw) != ref["sha256"]:
            errors.append(f"Forecast {role} cross-repo hash mismatch")

    seed_path = forecast_refs["seed"]["path"]
    prediction_path = forecast_refs["emitted_predictions"]["path"]
    if seed_path in external_files and prediction_path in external_files:
        seed_rows = [
            line
            for line in external_files[seed_path].decode("utf-8").splitlines(keepends=True)
            if line.lstrip().startswith("{ player_id:")
        ]
        prediction_rows = external_files[prediction_path].decode("utf-8").splitlines(keepends=True)
        if len(seed_rows) != 39:
            errors.append(f"Forecast seed expected 39 source rows, found {len(seed_rows)}")
        for assertion in assertions.get("forecast_row_assertions", []):
            assertion_id = assertion.get("assertion_id")
            try:
                seed_line = seed_rows[assertion["seed_row_index_zero_based"]]
                prediction_line = prediction_rows[assertion["prediction_jsonl_line_one_based"] - 1]
            except (IndexError, KeyError, TypeError) as exc:
                errors.append(f"Forecast assertion locator invalid for {assertion_id}: {exc}")
                continue
            if sha256(seed_line.encode("utf-8")) != assertion.get("seed_source_line_sha256"):
                errors.append(f"Forecast seed row hash mismatch for {assertion_id}")
            if sha256(prediction_line.encode("utf-8")) != assertion.get("prediction_source_line_sha256"):
                errors.append(f"Forecast prediction row hash mismatch for {assertion_id}")
            raw_id = assertion.get("forecast_raw_player_id")
            if not isinstance(raw_id, str) or raw_id not in seed_line or raw_id not in prediction_line:
                errors.append(f"Forecast raw ID locator mismatch for {assertion_id}")
            errors.extend(validate_forecast_assertion_seed_binding(assertion, seed_line))

    for inventory in FORECAST_IMPACTED_ARTIFACTS:
        try:
            raw = _git_blob(forecast_repo_root, forecast_commit, inventory["path"])
        except ValidationFailure as exc:
            errors.append(str(exc))
        else:
            if sha256(raw) != inventory["sha256"]:
                errors.append(f"Forecast inventory hash mismatch: {inventory['path']}")
    return errors


def _walk_forbidden(value: Any, path: str = "$") -> list[str]:
    errors: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key in FORBIDDEN_METRIC_KEYS:
                errors.append(f"{path}.{key}: prohibited Forecast/model metric")
            errors.extend(_walk_forbidden(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            errors.extend(_walk_forbidden(child, f"{path}[{index}]"))
    return errors


def resolve_core_identity(crosswalk: dict[str, Any], gsis_id: str) -> dict[str, Any]:
    """Resolve the bounded source-player edge by exact GSIS only."""

    matches = [
        row
        for row in crosswalk.get("records", [])
        if isinstance(row, dict) and row.get("core_identity", {}).get("gsis_id") == gsis_id
    ]
    if len(matches) != 1:
        raise ValidationFailure(f"exact GSIS resolution requires one row; found {len(matches)} for {gsis_id!r}")
    row = matches[0]
    if row["core_identity"].get("tiber_data_source_player_id") is None:
        raise ValidationFailure(f"GSIS {gsis_id} has no governed TIBER-Data source player record")
    return row


def resolve_forecast_identity(crosswalk: dict[str, Any], assertion_id: str) -> str:
    """Fail closed for every current Forecast source-row assertion."""

    for row in crosswalk.get("records", []):
        link = row.get("forecast_link", {}) if isinstance(row, dict) else {}
        assertions = [*link.get("subject_assertions", []), *link.get("canonical_id_collision_assertions", [])]
        if any(item.get("assertion_id") == assertion_id for item in assertions):
            raise ValidationFailure(f"Forecast assertion {assertion_id} is conflict-blocked")
    raise ValidationFailure(f"unknown Forecast assertion {assertion_id!r}; resolution is fail-closed")


def validate_payloads(
    crosswalk: dict[str, Any], conflicts: dict[str, Any], manifest: dict[str, Any]
) -> list[str]:
    errors: list[str] = []
    if crosswalk.get("artifact_id") != ARTIFACT_ID:
        errors.append("crosswalk artifact_id mismatch")
    if crosswalk.get("schema_version") != SCHEMA_VERSION:
        errors.append("crosswalk schema_version mismatch")
    if crosswalk.get("crosswalk_version") != VERSION:
        errors.append("crosswalk version mismatch")
    if conflicts.get("artifact_id") != CONFLICT_ARTIFACT_ID:
        errors.append("conflict artifact_id mismatch")
    if manifest.get("artifact_id") != MANIFEST_ARTIFACT_ID:
        errors.append("manifest artifact_id mismatch")
    if crosswalk.get("promotion_authorized") is not False:
        errors.append("promotion_authorized must be false")
    if crosswalk.get("forecast_mutation_authorized") is not False:
        errors.append("forecast_mutation_authorized must be false")
    source_ids = {
        item.get("source_ref_id")
        for item in crosswalk.get("source_artifacts", [])
        if isinstance(item, dict)
    }
    if source_ids != {
        "rookies-2023-draft-census",
        "tiber-data-player-season-coverage-v0",
        "tiber-identity-crosswalk-v1",
        "forecast-run1-scaffold",
    }:
        errors.append(f"source artifact inventory mismatch: {sorted(source_ids)}")

    join_contract = crosswalk.get("join_contract", {})
    forbidden_joins = set(join_contract.get("forbidden_player_join_keys", []))
    if not {"display_name", "normalized_display_name", "fuzzy_name"}.issubset(forbidden_joins):
        errors.append("join contract does not forbid all display-name/fuzzy joins")
    if "display_name" in set(join_contract.get("allowed_player_join_keys", [])):
        errors.append("display_name is present in allowed join keys")
    override_policy = crosswalk.get("forecast_subject_override_policy", {})
    if override_policy.get("status") != "candidate_override_bindings_need_operator_review":
        errors.append("Forecast subject override policy overclaims approval")
    if override_policy.get("display_name_used") is not False:
        errors.append("Forecast subject override policy permits display-name association")
    if override_policy.get("association_basis") != "unique_exact_non_name_2024_fingerprint_in_pinned_data_source":
        errors.append("Forecast subject override policy lacks the pinned non-name association basis")
    if override_policy.get("resolution_effect") != "none_conflict_binding_only":
        errors.append("Forecast subject override policy resolves identity")

    rows = crosswalk.get("records")
    if not isinstance(rows, list):
        return [*errors, "records must be an array"]
    if len(rows) != 80:
        errors.append(f"expected 80 records, found {len(rows)}")
    picks = [row.get("overall_pick") for row in rows if isinstance(row, dict)]
    row_ids = [row.get("crosswalk_row_id") for row in rows if isinstance(row, dict)]
    gsis_ids = [row.get("core_identity", {}).get("gsis_id") for row in rows if isinstance(row, dict)]
    slugs = [row.get("core_identity", {}).get("rookies_slug") for row in rows if isinstance(row, dict)]
    for name, values in (("overall_pick", picks), ("crosswalk_row_id", row_ids), ("gsis_id", gsis_ids), ("rookies_slug", slugs)):
        if len(values) != len(set(values)):
            errors.append(f"duplicate {name}")
        if any(value is None for value in values):
            errors.append(f"missing {name}")
    if picks != sorted(picks):
        errors.append("records are not sorted by overall_pick")

    position_counts = dict(sorted(Counter(row.get("draft_position_audit_only") for row in rows).items()))
    if position_counts != EXPECTED_POSITION_COUNTS:
        errors.append(f"position counts mismatch: {position_counts}")
    slug_counts = Counter(row["core_identity"].get("rookies_slug_status") for row in rows)
    if slug_counts != Counter({"proposed_slug": 67, "existing_repo_id": 13}):
        errors.append(f"Rookies slug status counts mismatch: {dict(slug_counts)}")

    unresolved_ids: set[str] = set()
    resolved_count = 0
    season_status_counts: Counter[str] = Counter()
    affected_ids: set[str] = set()
    subject_assertion_ids: set[str] = set()
    collision_pairs: set[tuple[str, str]] = set()
    all_alias_values: set[str] = set()
    for index, row in enumerate(rows):
        core = row.get("core_identity", {})
        draft = row.get("draft_team", {})
        gsis_id = core.get("gsis_id")
        data_id = core.get("tiber_data_source_player_id")
        status = core.get("tiber_data_source_player_id_status")
        corroboration = core.get("data_identity_corroboration", {})
        season_status_counts[status] += 1
        if core.get("join_method") != "exact_gsis_only" or core.get("display_name_join_used") is not False:
            errors.append(f"records[{index}] violates exact-GSIS-only join policy")
        if core.get("tiber_canonical_player_id") is not None:
            errors.append(f"records[{index}] invents or resolves a TIBER canonical player ID")
        if core.get("tiber_canonical_identity_status") != "unresolved_no_admissible_gsis_to_tiber_player_id_edge":
            errors.append(f"records[{index}] hides the unresolved TIBER canonical namespace edge")
        if core.get("tiber_canonical_namespace") != "TIBER_IDENTITY_CROSSWALK_V1.tiber_player_id":
            errors.append(f"records[{index}] uses an undeclared TIBER canonical namespace")
        if data_id is None:
            unresolved_ids.add(gsis_id)
            if status != "unresolved_no_governed_data_record":
                errors.append(f"records[{index}] null Data ID lacks unresolved status")
            if corroboration.get("status") != "unavailable_no_governed_data_record":
                errors.append(f"records[{index}] unresolved Data ID has false corroboration")
        else:
            resolved_count += 1
            if data_id != gsis_id:
                errors.append(f"records[{index}] Data source player ID differs from exact GSIS")
            if corroboration.get("status") != "exact_gsis_and_draft_metadata_agree":
                errors.append(f"records[{index}] resolved Data ID lacks draft-metadata corroboration")
            if corroboration.get("draft_year_values") != [2023]:
                errors.append(f"records[{index}] Data draft year does not corroborate the census")
            if corroboration.get("draft_pick_values") != [row.get("overall_pick")]:
                errors.append(f"records[{index}] Data draft pick does not corroborate the census")
            if corroboration.get("canonical_draft_team_values") != [draft.get("canonical_code")]:
                errors.append(f"records[{index}] Data draft team does not corroborate the census")
        for alias in row.get("identity_aliases", []):
            if isinstance(alias, str):
                all_alias_values.add(alias)

        try:
            canonical, rule = normalize_team_code(
                draft.get("raw_code"),
                source_namespace=draft.get("source_namespace"),
                season=draft.get("source_season"),
            )
        except BuildFailure as exc:
            errors.append(f"records[{index}] team policy: {exc}")
        else:
            if draft.get("canonical_code") != canonical or draft.get("normalization_rule_id") != rule:
                errors.append(f"records[{index}] draft team normalization mismatch")

        link = row.get("forecast_link", {})
        subjects = link.get("subject_assertions", [])
        collisions = link.get("canonical_id_collision_assertions", [])
        if subjects or collisions:
            affected_ids.add(gsis_id)
            if link.get("status") != "conflict_blocked":
                errors.append(f"records[{index}] known Forecast conflict is not blocked")
        elif link.get("status") != "not_present":
            errors.append(f"records[{index}] non-conflict Forecast status is not not_present")
        if link.get("resolved_forecast_row_identity") is not None:
            errors.append(f"records[{index}] resolves a Forecast conflict")
        if link.get("auto_resolution_allowed") is not False or link.get("display_name_join_allowed") is not False:
            errors.append(f"records[{index}] permits Forecast auto/name resolution")
        for assertion in subjects:
            subject_assertion_ids.add(assertion.get("assertion_id"))
            if assertion.get("forecast_raw_player_id") == gsis_id:
                errors.append(f"records[{index}] subject assertion does not express an ID conflict")
            if assertion.get("association_method") != "explicit_candidate_override_unique_non_name_fingerprint":
                errors.append(f"records[{index}] subject assertion lacks an explicit non-name override")
            if assertion.get("association_status") != "needs_operator_review":
                errors.append(f"records[{index}] subject override falsely claims resolution or operator approval")
            fingerprint = assertion.get("non_name_fingerprint")
            if not isinstance(fingerprint, dict) or set(fingerprint) != {
                "season", "position", "canonical_team", "games_played", "receptions", "targets"
            }:
                errors.append(f"records[{index}] subject override lacks complete non-name fingerprint lineage")
        for assertion in collisions:
            collision_pairs.add((gsis_id, assertion.get("assertion_id")))

    if resolved_count != 76:
        errors.append(f"expected 76 exact Data source-player resolutions, found {resolved_count}")
    if unresolved_ids != EXPECTED_MISSING_DATA_IDS:
        errors.append(f"unexpected unresolved Data IDs: {sorted(unresolved_ids)}")
    if season_status_counts != Counter({
        "exact_gsis_source_verified_in_2023_reg": 68,
        "exact_gsis_source_verified_in_later_promoted_reg_only": 8,
        "unresolved_no_governed_data_record": 4,
    }):
        errors.append(f"Data identity status ledger mismatch: {dict(season_status_counts)}")
    if len(subject_assertion_ids) != 8:
        errors.append(f"expected 8 unique Forecast subject conflicts, found {len(subject_assertion_ids)}")
    if len(collision_pairs) != 5:
        errors.append(f"expected 5 Forecast census-ID collisions, found {len(collision_pairs)}")
    if len(affected_ids) != 11:
        errors.append(f"expected 11 affected census rows, found {len(affected_ids)}")

    if any(row["core_identity"].get("tiber_canonical_player_id") is not None for row in rows):
        errors.append("TIBER canonical player IDs must remain 0/80 resolved without an admissible GSIS edge")

    puka = next((row for row in rows if row.get("core_identity", {}).get("gsis_id") == "00-0039075"), None)
    if not puka:
        errors.append("Puka governed GSIS row is missing")
    else:
        assertions = puka["forecast_link"].get("subject_assertions", [])
        if len(assertions) != 1 or assertions[0].get("forecast_raw_player_id") != "00-0038543":
            errors.append("Puka conflict does not preserve Forecast 00-0038543 and governed 00-0039075")
        if puka["forecast_link"].get("status") != "conflict_blocked":
            errors.append("Puka Forecast edge is not blocked")
    if "00-0038543" in all_alias_values:
        errors.append("Forecast Puka raw ID 00-0038543 was incorrectly admitted as an alias")

    summary = conflicts.get("summary", {})
    expected_summary = {
        "subject_identity_conflicts": 8,
        "raw_id_collision_findings": 5,
        "unique_forecast_source_rows": 11,
        "affected_census_rows": 11,
        "resolved_conflicts": 0,
        "open_conflicts": 13,
    }
    if summary != expected_summary:
        errors.append(f"conflict summary mismatch: {summary}")
    namespace_gap = conflicts.get("tiber_canonical_namespace_gap", {})
    if namespace_gap.get("governed_namespace") != "TIBER_IDENTITY_CROSSWALK_V1.tiber_player_id":
        errors.append("conflict report omits the governed TIBER canonical namespace")
    if namespace_gap.get("gsis_field_present_in_source") is not False:
        errors.append("conflict report misstates the V1 GSIS gap")
    if namespace_gap.get("admissible_gsis_to_tiber_player_id_links") != 0:
        errors.append("conflict report fabricates a GSIS-to-TIBER canonical edge")
    if namespace_gap.get("unresolved_census_rows") != 80:
        errors.append("conflict report TIBER canonical gap is not 80 rows")
    conflict_rows = conflicts.get("conflicts", [])
    if not isinstance(conflict_rows, list) or len(conflict_rows) != 13:
        errors.append("conflict report must contain 13 explicit findings")
    else:
        conflict_ids = [row.get("conflict_id") for row in conflict_rows]
        if len(conflict_ids) != len(set(conflict_ids)):
            errors.append("duplicate conflict_id")
        for index, conflict in enumerate(conflict_rows):
            if conflict.get("status") != "unresolved" or conflict.get("resolution") is not None:
                errors.append(f"conflicts[{index}] is not explicit unresolved/null")
            if conflict.get("affected_gsis_id") not in set(gsis_ids):
                errors.append(f"conflicts[{index}] is orphaned from the census")
            source_assertion = conflict.get("source_assertion", {})
            required = {
                "assertion_id", "source_repository", "source_commit", "seed_path",
                "seed_row_index_zero_based", "seed_source_line_sha256", "prediction_path",
                "prediction_jsonl_line_one_based", "prediction_source_line_sha256",
                "forecast_raw_player_id", "association_method", "resolution_effect",
            }
            if not required.issubset(source_assertion):
                errors.append(f"conflicts[{index}] lacks complete source-row lineage")

    team_policy = crosswalk.get("canonical_team_code_policy", {})
    rams = team_policy.get("rams_alias_policy", {})
    if team_policy.get("canonical_rams_code") != "LAR" or rams.get("direction") != "LA_to_LAR_only":
        errors.append("Rams LA-to-LAR canonical policy mismatch")
    if rams.get("lac_is_distinct") is not True or rams.get("reverse_emission_allowed") is not False:
        errors.append("Rams policy fails LA/LAC or reverse-emission boundary")
    if rams.get("supported_source_seasons") != [2023, 2024, 2025]:
        errors.append("Rams candidate support seasons mismatch")
    if rams.get("support_scope_basis") != "candidate_observed_2023_class_data_history_not_franchise_history_claim":
        errors.append("Rams support bound is presented as an unsupported historical fact")
    if rams.get("exact_gsis_draft_metadata_evidence_count") != 3:
        errors.append("Rams LA-to-LAR exact-GSIS evidence count mismatch")
    expected_alias_counts = {"GNB": 7, "KAN": 1, "LVR": 3, "NOR": 3, "NWE": 2, "SFO": 3, "TAM": 2}
    actual_alias_counts = {
        item.get("raw"): item.get("exact_gsis_draft_metadata_evidence_count")
        for item in team_policy.get("draft_source_aliases_2023", [])
        if isinstance(item, dict)
    }
    if actual_alias_counts != expected_alias_counts:
        errors.append(f"draft alias evidence counts mismatch: {actual_alias_counts}")

    inventory = conflicts.get("impacted_artifact_inventory", {}).get("tiber_forecast", {})
    if inventory.get("inventory_scope") != "bounded_direct_and_reference_inventory_not_a_full_transitive_dependency_graph":
        errors.append("Forecast inventory overclaims full transitive completeness")
    inventory_rows = inventory.get("artifacts", [])
    if not isinstance(inventory_rows, list) or len(inventory_rows) != 16:
        errors.append("Forecast bounded inventory must contain the 16 pinned direct/reference paths")
    else:
        inventory_paths = [item.get("path") for item in inventory_rows]
        if len(inventory_paths) != len(set(inventory_paths)):
            errors.append("Forecast bounded inventory has duplicate paths")
        if any(not item.get("git_blob") or not item.get("sha256") for item in inventory_rows):
            errors.append("Forecast bounded inventory lacks blob/hash lineage")

    errors.extend(_walk_forbidden(rows, "$.records"))

    crosswalk_raw = serialize(crosswalk)
    conflicts_raw = serialize(conflicts)
    crosswalk_hash = sha256(crosswalk_raw)
    conflicts_hash = sha256(conflicts_raw)
    if conflicts.get("crosswalk_ref", {}).get("sha256") != crosswalk_hash:
        errors.append("conflict report crosswalk hash mismatch")
    manifest_entries = {
        item.get("path"): item.get("sha256")
        for item in manifest.get("artifacts", [])
        if isinstance(item, dict)
    }
    if manifest_entries.get(str(CROSSWALK_PATH.relative_to(ROOT))) != crosswalk_hash:
        errors.append("manifest crosswalk hash mismatch")
    if manifest_entries.get(str(CONFLICT_PATH.relative_to(ROOT))) != conflicts_hash:
        errors.append("manifest conflict hash mismatch")
    binding = manifest.get("downstream_binding", {})
    if binding.get("required_version") != VERSION or binding.get("required_crosswalk_sha256") != crosswalk_hash:
        errors.append("downstream version/hash binding mismatch")
    if binding.get("allowed_identity_edge") != "gsis_to_tiber_data_source_player_id":
        errors.append("manifest does not constrain the pilot to the source-player edge")
    if binding.get("tiber_canonical_player_id_edge_authorized") is not False:
        errors.append("manifest authorizes an unresolved TIBER canonical identity edge")
    if manifest.get("promotion_authorized") is not False:
        errors.append("manifest promotion_authorized must be false")

    coverage = crosswalk.get("coverage_summary", {})
    if coverage.get("position_counts") != EXPECTED_POSITION_COUNTS:
        errors.append("coverage summary position counts mismatch")
    if coverage.get("tiber_data_source_player_id_exact_gsis_resolved_count") != resolved_count:
        errors.append("coverage summary Data source-player resolution count mismatch")
    if coverage.get("tiber_canonical_player_id_resolved_count") != 0:
        errors.append("coverage summary falsely resolves TIBER canonical player IDs")
    if coverage.get("tiber_canonical_player_id_unresolved_count") != 80:
        errors.append("coverage summary TIBER canonical gap count mismatch")
    if coverage.get("forecast_subject_link_counts") != {"resolved": 0, "conflict_blocked": 8, "not_present": 72}:
        errors.append("coverage summary Forecast subject counts mismatch")
    if coverage.get("forecast_census_risk_counts") != {"conflict_blocked": 11, "no_known_run1_subject_or_collision": 69}:
        errors.append("coverage summary Forecast risk counts mismatch")

    return errors


def validate_committed(
    *,
    rookies_repo_root: Path | None = None,
    forecast_repo_root: Path | None = None,
    strict_cross_repo: bool = False,
) -> tuple[dict[str, Any], list[str]]:
    crosswalk = _load(CROSSWALK_PATH)
    conflicts = _load(CONFLICT_PATH)
    manifest = _load(MANIFEST_PATH)
    errors = validate_payloads(crosswalk, conflicts, manifest)
    try:
        expected_crosswalk, expected_conflicts, expected_manifest = build_payloads()
    except BuildFailure as exc:
        errors.append(f"deterministic rebuild failed: {exc}")
    else:
        if serialize(crosswalk) != serialize(expected_crosswalk):
            errors.append("committed crosswalk differs from deterministic rebuild")
        if serialize(conflicts) != serialize(expected_conflicts):
            errors.append("committed conflict report differs from deterministic rebuild")
        if serialize(manifest) != serialize(expected_manifest):
            errors.append("committed manifest differs from deterministic rebuild")

    external_status = "not_run"
    if rookies_repo_root is not None and forecast_repo_root is not None:
        external_errors = validate_cross_repo_sources(rookies_repo_root, forecast_repo_root)
        errors.extend(external_errors)
        external_status = "passed" if not external_errors else "failed"
    elif strict_cross_repo:
        errors.append("strict cross-repo validation requires both --rookies-repo-root and --forecast-repo-root")
        external_status = "failed_missing_repo_roots"

    report = {
        "artifact_id": "rookie_2023_identity_crosswalk_candidate_validation",
        "validator_version": "0.1.0",
        "crosswalk_version": VERSION,
        "generated_at": GENERATED_AT,
        "status": "valid" if not errors else "invalid",
        "valid": not errors,
        "error_count": len(errors),
        "errors": errors,
        "external_source_verification": {
            "status": external_status,
            "rookies_repo_root_supplied": rookies_repo_root is not None,
            "forecast_repo_root_supplied": forecast_repo_root is not None,
        },
        "validated_artifacts": [
            {"path": str(CROSSWALK_PATH.relative_to(ROOT)), "sha256": sha256(CROSSWALK_PATH.read_bytes())},
            {"path": str(CONFLICT_PATH.relative_to(ROOT)), "sha256": sha256(CONFLICT_PATH.read_bytes())},
            {"path": str(MANIFEST_PATH.relative_to(ROOT)), "sha256": sha256(MANIFEST_PATH.read_bytes())},
        ],
        "checks": [
            "source_content_pins",
            "deterministic_rebuild",
            "80_row_census_and_position_counts",
            "unique_gsis_slug_pick_and_row_ids",
            "exact_gsis_only_data_resolution",
            "display_name_join_ban",
            "explicit_unresolved_forecast_conflicts",
            "forecast_non_name_fingerprint_to_pinned_seed_row_binding",
            "puka_dual_id_conflict",
            "directed_date_scoped_team_alias_policy",
            "version_and_sha256_consumer_binding",
            "candidate_and_no_mutation_boundaries",
            "optional_cross_repo_git_blob_and_forecast_row_pins",
        ],
    }
    return report, errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", action="store_true", help="write the deterministic validation report")
    parser.add_argument("--rookies-repo-root", type=Path)
    parser.add_argument("--forecast-repo-root", type=Path)
    parser.add_argument("--strict-cross-repo", action="store_true")
    args = parser.parse_args()
    report, errors = validate_committed(
        rookies_repo_root=args.rookies_repo_root,
        forecast_repo_root=args.forecast_repo_root,
        strict_cross_repo=args.strict_cross_repo,
    )
    if args.report:
        VALIDATION_PATH.parent.mkdir(parents=True, exist_ok=True)
        VALIDATION_PATH.write_bytes(serialize(report))
    if errors:
        print("VALIDATION FAILED")
        for error in errors:
            print(f"- {error}")
        return 1
    print(
        "VALIDATION PASSED: 80 rows; 76 Data source-player exact-GSIS links; "
        "0 TIBER canonical links; 13 explicit Forecast findings"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

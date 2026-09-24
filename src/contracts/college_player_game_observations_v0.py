"""Offline contract gate; never acquires, imputes, resolves or promotes observations.

JSON Schema is the shape authority. This module adds cross-row semantic checks.
Run from repository root: python -m src.contracts.college_player_game_observations_v0 FILE
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, TypedDict

from jsonschema import Draft202012Validator, FormatChecker

SCHEMA_PATH = (
    Path(__file__).resolve().parents[2]
    / "schemas"
    / ("college_player_game_observations_v0.schema.json")
)


class Finding(TypedDict):
    code: str
    path: str
    message: str


def _instant(value: str) -> datetime:
    return datetime.fromisoformat(value.upper().replace("Z", "+00:00"))


FORMAT_CHECKER = FormatChecker()


@FORMAT_CHECKER.checks("date-time", raises=ValueError)
def _timestamp(value: Any) -> bool:
    # Do not silently skip timestamp checks when optional jsonschema extras are absent.
    if not isinstance(value, str):
        return True  # schema's type gate handles non-strings
    if not re.fullmatch(
        r"\d{4}-\d{2}-\d{2}[Tt]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:[Zz]|[+-](?:[01]\d|2[0-3]):[0-5]\d)",
        value,
    ):
        return False
    parsed = _instant(value)
    return parsed.tzinfo is not None


def validate(envelope: Any) -> list[Finding]:
    """Return deterministic findings without changing input. [] means contract-valid only."""
    schema = json.loads(SCHEMA_PATH.read_text())
    findings: list[Finding] = []

    def fail(code: str, path: str, message: str) -> None:
        findings.append({"code": code, "path": path, "message": message})

    gate = Draft202012Validator(schema, format_checker=FORMAT_CHECKER)
    for error in gate.iter_errors(envelope):
        fail("SCHEMA", "/" + "/".join(map(str, error.absolute_path)), error.message)
    if findings:
        return sorted(findings, key=lambda f: (f["path"], f["code"], f["message"]))

    evidence = envelope["evidence"]

    def references(
        ids: list[str],
        path: str,
        kind: str | None = None,
        *,
        as_known: datetime | None = None,
        row: dict | None = None,
    ) -> None:
        for ref in ids:
            if ref not in evidence:
                fail("EVIDENCE_REF", path, f"Unknown evidence reference: {ref}")
            elif kind and evidence[ref]["kind"] != kind:
                fail("EVIDENCE_KIND", path, f"Expected {kind}: {ref}")
            else:
                item = evidence[ref]
                if as_known and _instant(item["known_at"]) > as_known:
                    fail("EVIDENCE_FUTURE", path, f"Evidence first known after cutoff: {ref}")
                if row:
                    binding = item["scope"]
                    expected = {
                        "season": row["game"]["season"],
                        "source_game_id": row["game"]["source_game_id"],
                        "source_player_id": row["identity"]["source_player_id"],
                        "source_revision_id": row["source_revision_id"],
                        "source_record_type": row["source_record_type"],
                    }
                    if item["provider"] != row["provider"] or any(
                        binding[k] is not None and binding[k] != value
                        for k, value in expected.items()
                    ):
                        fail("EVIDENCE_SCOPE", path, f"Evidence binding disagrees with row: {ref}")

    if envelope["evidence_mode"] == "synthetic_fixture":
        for key, item in evidence.items():
            if not item["locator"].startswith("synthetic:"):
                fail("SYNTHETIC_PROVENANCE", f"/evidence/{key}", "Use synthetic: locators.")
    else:
        for key, item in evidence.items():
            if item["locator"].startswith("synthetic:"):
                fail(
                    "SYNTHETIC_PROVENANCE",
                    f"/evidence/{key}",
                    "Fixture cannot claim source evidence.",
                )

    coverage = envelope["coverage"]
    for key, item in evidence.items():
        if _instant(item["known_at"]) > _instant(envelope["generated_at"]):
            fail("EVIDENCE_FUTURE", f"/evidence/{key}", "Evidence postdates artifact generation.")
        if item["provider"] != coverage["provider"]:
            fail("EVIDENCE_SCOPE", f"/evidence/{key}", "Evidence provider disagrees with envelope.")
    references(coverage["evidence_refs"], "/coverage", "scope")
    scope = coverage["game_scope"]
    expected = scope["expected_game_ids"]

    def game_key(item: dict) -> tuple[int, str]:
        return (item["season"], item["source_game_id"])

    observed_games = {game_key(item) for item in scope["observed_game_ids"]}
    if len(observed_games) != len(scope["observed_game_ids"]):
        fail("GAME_SCOPE", "/coverage", "Duplicate season/game coverage key.")
    references(scope["expectation_evidence_refs"], "/coverage/game_scope", "scope")
    if (expected is None) != (not scope["expectation_evidence_refs"]):
        fail(
            "GAME_EXPECTATION",
            "/coverage",
            "Expected games require independent evidence; unknown requires none.",
        )
    if expected is not None:
        expected_keys = {game_key(item) for item in expected}
        if len(expected_keys) != len(expected):
            fail("GAME_EXPECTATION", "/coverage", "Duplicate season/game expectation key.")
        if not observed_games <= expected_keys:
            fail("GAME_SCOPE", "/coverage", "Observed game outside declared expected scope.")
        if coverage["population_status"] == "complete" and observed_games != expected_keys:
            fail(
                "COVERAGE_COMPLETE",
                "/coverage",
                "Missing expected games contradict complete population.",
            )

    rows = envelope["observations"]
    ids: dict[str, dict] = {}
    grains: dict[tuple, dict] = {}
    successors: dict[str, str] = {}
    roots: dict[tuple, str] = {}
    generated = _instant(envelope["generated_at"])

    def logical_key(row: dict) -> tuple:
        return (
            row["provider"],
            row["identity"]["source_player_id"],
            row["game"]["season"],
            row["game"]["source_game_id"],
        )

    for i, row in enumerate(rows):
        path = f"/observations/{i}"
        oid = row["observation_id"]
        if row["provider"] != coverage["provider"]:
            fail("PROVIDER_SCOPE", path, "One provider namespace per envelope.")
        if oid in ids:
            fail("DUPLICATE_ID", path, oid)
        ids[oid] = row
        grain = (*logical_key(row), row["source_revision_id"])
        if grain in grains:
            previous = {k: v for k, v in grains[grain].items() if k != "observation_id"}
            current = {k: v for k, v in row.items() if k != "observation_id"}
            fail(
                "DUPLICATE_REVISION" if previous == current else "CONFLICTING_REVISION",
                path,
                "One observation per player/game/source revision; no silent deduplication.",
            )
        grains[grain] = row
        relationship = row["source_relationship"]
        relation = relationship["status"]
        if relation == "initial" and row["supersedes"] is None:
            if logical_key(row) in roots:
                fail(
                    "UNLINKED_REVISION", path, "Additional revision requires supersession lineage."
                )
            roots[logical_key(row)] = oid
        if relation == "established_supersession":
            if not row["supersedes"] or row["supersedes"] != relationship["related_observation_id"]:
                fail("RELATIONSHIP", path, "Established correction must link its same ancestor.")
            if row["supersedes"] is None:
                fail(
                    "UNLINKED_REVISION",
                    path,
                    "Established correction requires a retained ancestor.",
                )
            if row["revision_reason"] is None:
                fail("REVISION_REASON", path, "Established correction requires a reason.")
            if (
                not row["revision_reason"]
                or relationship["basis"] == "none"
                or not relationship["evidence_refs"]
            ):
                fail("RELATIONSHIP_BASIS", path, "Source correction requires a supported basis.")
        elif row["supersedes"] is not None or row["revision_reason"] is not None:
            fail("RELATIONSHIP", path, "Unestablished source relationship cannot supersede.")
        if relation == "initial" and (
            relationship["related_observation_id"] is not None
            or relationship["basis"] != "none"
            or relationship["evidence_refs"]
        ):
            fail("RELATIONSHIP", path, "Initial row has no source relation.")
        if relation in ("unresolved", "older_discovered_later") and (
            not relationship["related_observation_id"] or relationship["basis"] != "none"
        ):
            fail(
                "RELATIONSHIP",
                path,
                "Unordered material requires a related assertion and no claimed ordering basis.",
            )
        if row["revision_origin"] == "retained_snapshot_digest":
            if not re.fullmatch(r"sha256:[0-9a-f]{64}", row["source_revision_id"]):
                fail("REVISION_DIGEST", path, "Digest revision must be sha256:<64 lowercase hex>.")
        identity = row["identity"]
        retrieved = _instant(row["retrieved_at"])
        references(
            identity["evidence_refs"], path + "/identity", "identity", as_known=retrieved, row=row
        )
        references(
            [row["source_snapshot_ref"]], path, "source_snapshot", as_known=retrieved, row=row
        )
        references([row["mapping_ref"]], path, "mapping", as_known=retrieved, row=row)
        game = row["game"]
        if (game["season"], game["source_game_id"]) not in observed_games:
            fail("GAME_SCOPE", path, "Observation game absent from observed source-game scope.")
        if (game["date"] is None) != (game["date_origin"] == "not_supplied_by_source"):
            fail("EVENT_CLOCK", path, "Game date availability contradicts origin.")
        if game["team"]["source_program_id"] == game["opponent"]["source_program_id"]:
            fail("EVENT_TEAMS", path, "Team and opponent must differ.")
        references(
            game["status_evidence_refs"],
            path + "/game",
            "source_snapshot",
            as_known=retrieved,
            row=row,
        )
        if retrieved > generated:
            fail("CLOCK_ORDER", path, "Retrieval occurs after artifact generation.")
        clock = row["source_updated_at"]
        references(
            clock["evidence_refs"],
            path + "/source_updated_at",
            "source_snapshot",
            as_known=retrieved,
            row=row,
        )
        if (clock["value"] is None) != (clock["origin"] == "not_supplied_by_source"):
            fail("SOURCE_CLOCK", path, "Source clock availability contradicts origin.")
        if clock["value"] is not None and _instant(clock["value"]) > retrieved:
            fail(
                "CLOCK_ORDER", path, "Source update occurs after retrieval; resolve clock conflict."
            )
        if game["status"] == "final" and game["date"] is not None:
            # A date-only event can span timezone boundaries; permit a full day
            # after UTC first knowledge, but never a plainly future final event.
            from datetime import date

            if (
                date.fromisoformat(game["date"])
                > (retrieved.astimezone(timezone.utc) + timedelta(days=1)).date()
            ):
                fail(
                    "FINAL_EVENT_CHRONOLOGY",
                    path,
                    "Final event date is clearly after first knowledge.",
                )
        snapshot = evidence.get(row["source_snapshot_ref"])
        if snapshot and snapshot["scope"]["source_revision_id"] != row["source_revision_id"]:
            fail(
                "EVIDENCE_REVISION",
                path,
                "Declared snapshot does not bind to this source revision.",
            )
        if snapshot and snapshot["scope"]["source_record_type"] != row["source_record_type"]:
            fail("SOURCE_RECORD_TYPE", path, "Observed row type must be backed by its snapshot.")
        references(
            relationship["evidence_refs"],
            path + "/source_relationship",
            as_known=retrieved,
            row=row,
        )
        if envelope["evidence_mode"] == "synthetic_fixture":
            tokens = [
                oid,
                row["provider"],
                identity["source_player_id"],
                game["source_game_id"],
                game["team"]["source_program_id"],
                game["opponent"]["source_program_id"],
            ]
            if identity["canonical_college_player_id"]:
                tokens.append(identity["canonical_college_player_id"])
            if any(not t.startswith("synthetic-") for t in tokens) or not identity[
                "name"
            ].startswith("SYNTHETIC "):
                fail(
                    "SYNTHETIC_IDENTITY",
                    path,
                    "Fixture names and IDs must be unmistakably synthetic.",
                )
        for category, metrics in row["observed"].items():
            complete = row["category_completeness"][category]
            for name, metric in metrics.items():
                mp = f"{path}/observed/{category}/{name}"
                references(
                    metric["evidence_refs"], mp, "source_snapshot", as_known=retrieved, row=row
                )
                if metric["availability"] in ("observed_zero", "observed_value") and metric[
                    "evidence_refs"
                ] != [row["source_snapshot_ref"]]:
                    fail(
                        "RAW_EVIDENCE_BINDING",
                        mp,
                        "Observed fact must cite its declared source snapshot.",
                    )
                if metric["availability"] == "not_applicable":
                    basis = metric.get("applicability_basis")
                    if (
                        basis is None
                        or basis["rule_id"] != "field_not_defined_for_source_record_type"
                    ):
                        fail(
                            "APPLICABILITY",
                            mp,
                            "Not applicable requires a bounded field/event rule.",
                        )
                    else:
                        references(
                            basis["evidence_refs"],
                            mp + "/applicability_basis",
                            as_known=retrieved,
                            row=row,
                        )
                        if (
                            row["source_snapshot_ref"] not in basis["evidence_refs"]
                            or row["mapping_ref"] not in basis["evidence_refs"]
                        ):
                            fail(
                                "APPLICABILITY",
                                mp,
                                "Applicability requires source snapshot and mapping evidence.",
                            )
                        mapping = evidence.get(row["mapping_ref"])
                        rule = {
                            "source_record_type": basis["source_record_type"],
                            "field": f"{category}.{name}",
                            "rule_id": basis["rule_id"],
                        }
                        if basis["source_record_type"] != row["source_record_type"]:
                            fail(
                                "APPLICABILITY",
                                mp,
                                "Applicability record type differs from the source row type.",
                            )
                        if mapping and rule not in mapping["applicability_rules"]:
                            fail(
                                "APPLICABILITY",
                                mp,
                                "No mapping rule for this field and record type.",
                            )
                elif metric.get("applicability_basis") is not None:
                    fail("APPLICABILITY", mp, "Applicability basis only belongs on not_applicable.")
                value = metric["value"]
                if value is not None and name != "yards" and value < 0:
                    fail("STAT_DOMAIN", mp, "Counts cannot be negative; net yards may be negative.")
                available = metric["availability"] in ("observed_zero", "observed_value")
                if complete == "complete" and not available:
                    fail(
                        "CATEGORY_COMPLETE",
                        mp,
                        "Complete category requires every contract field observed.",
                    )
                if complete in ("unavailable", "not_applicable") and available:
                    fail(
                        "CATEGORY_UNAVAILABLE",
                        mp,
                        "Category declaration contradicts observed value.",
                    )
                if complete == "not_applicable" and metric["availability"] != "not_applicable":
                    fail(
                        "CATEGORY_UNAVAILABLE",
                        mp,
                        "Not-applicable category requires matching fields.",
                    )
        passing = row["observed"]["passing"]
        attempts, completions = (passing[n]["value"] for n in ("attempts", "completions"))
        if attempts is not None and completions is not None and completions > attempts:
            fail("PASS_COUNTS", path, "Completions exceed attempts.")

    for i, row in enumerate(rows):
        parent = row["supersedes"]
        relation = row["source_relationship"]
        related = relation["related_observation_id"]
        if related and related not in ids:
            fail(
                "LINEAGE_MISSING",
                f"/observations/{i}/source_relationship",
                "Retain related assertion.",
            )
        elif related and logical_key(ids[related]) != logical_key(row):
            fail(
                "LINEAGE_GRAIN",
                f"/observations/{i}/source_relationship",
                "Relation crosses source player/game grain.",
            )
        if relation["status"] == "established_supersession" and related in ids:
            old = ids[related]
            old_clock = old["source_updated_at"]["value"]
            new_clock = row["source_updated_at"]["value"]
            if old_clock and new_clock and _instant(new_clock) < _instant(old_clock):
                fail(
                    "SOURCE_ORDER_CONFLICT",
                    f"/observations/{i}",
                    "Source correction clock predates its predecessor; quarantine relation.",
                )
            for ref in relation["evidence_refs"]:
                if ref in evidence and evidence[ref]["kind"] != "source_snapshot":
                    fail(
                        "RELATIONSHIP_BASIS",
                        f"/observations/{i}",
                        "Ordering basis needs source assertion evidence.",
                    )
            if row["source_snapshot_ref"] not in relation["evidence_refs"]:
                fail(
                    "RELATIONSHIP_BASIS",
                    f"/observations/{i}",
                    "Correction evidence must cite the new source snapshot.",
                )
            claim = evidence.get(row["source_snapshot_ref"], {}).get("source_order_claim")
            expected_assertion = (
                "explicit_correction"
                if relation["basis"] == "provider_explicit_correction"
                else "documented_provider_order"
            )
            if claim != {
                "older_revision_id": old["source_revision_id"],
                "newer_revision_id": row["source_revision_id"],
                "assertion": expected_assertion,
            }:
                fail(
                    "RELATIONSHIP_BASIS",
                    f"/observations/{i}",
                    "Evidence does not assert this exact revision order.",
                )
        if parent is None:
            continue
        path = f"/observations/{i}/supersedes"
        if parent not in ids:
            fail("LINEAGE_MISSING", path, "Retain the superseded observation in this envelope.")
            continue
        old = ids[parent]
        if logical_key(old) != logical_key(row):
            fail(
                "LINEAGE_GRAIN", path, "Correction must concern the same provider player and game."
            )
        if _instant(old["retrieved_at"]) >= _instant(row["retrieved_at"]):
            fail("LINEAGE_CLOCK", path, "Correction must be known strictly after its predecessor.")
        if parent in successors:
            fail(
                "LINEAGE_FORK",
                path,
                "Competing corrections require resolution; no arbitrary winner.",
            )
        successors[parent] = row["observation_id"]
    _validate_attributions_and_aliases(envelope, ids, logical_key, evidence, fail, references)
    return sorted(findings, key=lambda f: (f["path"], f["code"], f["message"]))


def _validate_attributions_and_aliases(envelope, ids, logical_key, evidence, fail, references):
    events: dict[str, dict] = {}
    successor: dict[str, str] = {}
    recorded = {oid: _instant(row["retrieved_at"]) for oid, row in ids.items()}
    # Retained attribution order is not its knowledge chronology. Index all
    # ancestors before checking links, even when the envelope lists a child first.
    for i, event in enumerate(envelope["attributions"]):
        eid = event["attribution_id"]
        if eid in events or eid in ids:
            fail(
                "ATTRIBUTION_DUPLICATE",
                f"/attributions/{i}",
                "Attribution ID must be unique across the envelope.",
            )
        else:
            events[eid] = event
            recorded[eid] = _instant(event["recorded_at"])
    for i, event in enumerate(envelope["attributions"]):
        path = f"/attributions/{i}"
        eid = event["attribution_id"]
        oid = event["source_observation_id"]
        if oid not in ids:
            fail("ATTRIBUTION_SOURCE", path, "Unknown immutable source observation.")
            continue
        parent = event["supersedes_attribution_id"] or oid
        if parent in successor:
            fail("ATTRIBUTION_FORK", path, "Only one successor per attribution state.")
        successor[parent] = eid
        predecessor = events.get(parent)
        if predecessor and predecessor["source_observation_id"] != oid:
            fail(
                "ATTRIBUTION_SOURCE",
                path,
                "Attribution predecessor belongs to another observation.",
            )
        if parent not in ids and predecessor is None:
            fail("ATTRIBUTION_MISSING", path, "Missing attribution ancestor.")
        event_time = _instant(event["recorded_at"])
        previous_time = recorded.get(parent)
        if previous_time and event_time <= previous_time:
            fail("ATTRIBUTION_CLOCK", path, "New knowledge must follow predecessor.")
        if event_time > _instant(envelope["generated_at"]):
            fail("ATTRIBUTION_CLOCK", path, "Attribution postdates artifact generation.")
        state = event["state"]
        if state["source_player_id"] != ids[oid]["identity"]["source_player_id"]:
            fail("ATTRIBUTION_SOURCE", path, "TIBER attribution cannot change source player ID.")
        references(state["evidence_refs"], path, "identity", as_known=event_time, row=ids[oid])
    ordered = sorted(
        enumerate(envelope["attributions"]), key=lambda pair: _instant(pair[1]["recorded_at"])
    )
    history = {
        oid: [(recorded[oid], row["identity"], f"/observations/{oid}/identity")]
        for oid, row in ids.items()
    }
    for i, event in ordered:
        oid = event["source_observation_id"]
        if oid in history:
            history[oid].append(
                (_instant(event["recorded_at"]), event["state"], f"/attributions/{i}/state")
            )

    def state_at(oid, cutoff):
        return next(state for when, state, _ in reversed(history[oid]) if when <= cutoff)

    # An event may appear before its predecessor in the envelope; check the
    # actual time-ordered chain independently of input order.
    for oid, entries in history.items():
        previous = oid
        previous_time = entries[0][0]
        for when, _, path in entries[1:]:
            event = envelope["attributions"][int(path.split("/")[2])]
            if (event["supersedes_attribution_id"] or oid) != previous:
                fail(
                    "ATTRIBUTION_LINEAGE",
                    path,
                    "Each retained state must follow its immediate predecessor.",
                )
            if when <= previous_time:
                fail("ATTRIBUTION_CLOCK", path, "Attribution knowledge times must increase.")
            previous = event["attribution_id"]
            previous_time = when

    for oid, row in ids.items():
        for state_known_at, state, path in history[oid]:
            resolved = state["status"] == "resolved"
            if resolved != (state["canonical_college_player_id"] is not None):
                fail("IDENTITY_STATUS", path, "Only resolved identity carries a canonical ID.")
            if not resolved and state["aggregation_status"] != "blocked_unresolved_identity":
                fail(
                    "ALIAS_STATUS", path, "Unresolved identity cannot enter canonical aggregation."
                )
            if resolved and state["aggregation_status"] == "blocked_unresolved_identity":
                fail(
                    "ALIAS_STATUS",
                    path,
                    "Resolved identity requires an explicit aggregation state.",
                )
            target = state["alias_of_observation_id"]
            if (state["aggregation_status"] == "excluded_reconciled_alias") != (target is not None):
                fail(
                    "ALIAS_STATUS",
                    path,
                    "Excluded alias requires exactly one retained representative.",
                )
            if target is not None:
                if (
                    target == oid
                    or target not in ids
                    or (
                        target in ids
                        and (
                            ids[target]["provider"] != row["provider"]
                            or logical_key(ids[target])[2:] != logical_key(row)[2:]
                        )
                    )
                ):
                    fail(
                        "ALIAS_REFERENCE",
                        path,
                        "Alias representative must be another provider row in the same game.",
                    )
                elif _instant(ids[target]["retrieved_at"]) > state_known_at:
                    fail(
                        "ALIAS_REFERENCE",
                        path,
                        "Representative unknown at this attribution cutoff.",
                    )
                else:
                    representative = state_at(target, state_known_at)
                    if (
                        representative["canonical_college_player_id"]
                        != state["canonical_college_player_id"]
                    ):
                        fail(
                            "ALIAS_REFERENCE",
                            path,
                            "Representative canonical ID differs at this cutoff.",
                        )
                    if representative["aggregation_status"] != "eligible":
                        fail(
                            "ALIAS_REPRESENTATIVE",
                            path,
                            "A reviewed alias must point directly to an eligible representative.",
                        )
                    if any(
                        r["supersedes"] == target and _instant(r["retrieved_at"]) <= state_known_at
                        for r in ids.values()
                    ):
                        fail(
                            "ALIAS_REFERENCE",
                            path,
                            "Representative source revision was already superseded.",
                        )
                    claim = {
                        "alias_source_player_id": row["identity"]["source_player_id"],
                        "alias_observation_id": oid,
                        "representative_observation_id": target,
                        "representative_source_player_id": ids[target]["identity"][
                            "source_player_id"
                        ],
                        "season": row["game"]["season"],
                        "source_game_id": row["game"]["source_game_id"],
                        "canonical_college_player_id": state["canonical_college_player_id"],
                    }
                    if not any(
                        evidence.get(ref, {}).get("kind") == "identity"
                        and evidence[ref].get("alias_claim") == claim
                        for ref in state["evidence_refs"]
                    ):
                        fail(
                            "ALIAS_EVIDENCE",
                            path,
                            "Reviewed alias requires exact source-player/game evidence.",
                        )
    # Check every knowledge boundary, not only the final state: a later review
    # cannot retroactively make earlier duplicate canonical claims safe.
    cutoffs = sorted(
        set(
            [_instant(r["retrieved_at"]) for r in ids.values()]
            + [_instant(e["recorded_at"]) for e in envelope["attributions"]]
        )
    )
    for cutoff in cutoffs:
        visible = {oid: row for oid, row in ids.items() if _instant(row["retrieved_at"]) <= cutoff}
        states = {oid: state_at(oid, cutoff) for oid in visible}
        superseded = {r["supersedes"] for r in visible.values() if r["supersedes"]}
        active = {oid: row for oid, row in visible.items() if oid not in superseded}
        # Reviewed decisions are scoped to their exact source revision pair.
        # Source correction ends their effective interval, but not their history.
        expired_representatives = {}
        for oid in superseded & states.keys():
            state = states[oid]
            if state["aggregation_status"] != "excluded_reconciled_alias":
                continue
            correction_time = min(
                _instant(row["retrieved_at"])
                for row in visible.values()
                if row["supersedes"] == oid
            )
            target = state["alias_of_observation_id"]
            expired_representatives[target] = max(
                correction_time, expired_representatives.get(target, correction_time)
            )
        effective = {}
        for oid in active:
            state = states[oid]
            target = state["alias_of_observation_id"]
            status = state["aggregation_status"]
            if status == "excluded_reconciled_alias" and target not in active:
                status = "blocked_alias_conflict"
            state_time = next(when for when, _, _ in reversed(history[oid]) if when <= cutoff)
            if (
                status == "eligible"
                and oid in expired_representatives
                and state_time <= expired_representatives[oid]
            ):
                status = "blocked_alias_conflict"
            effective[oid] = status
        groups: dict[tuple, dict[str, list[str]]] = {}
        for oid, row in active.items():
            state = states[oid]
            if state["status"] == "resolved":
                key = (
                    row["provider"],
                    row["game"]["season"],
                    row["game"]["source_game_id"],
                    state["canonical_college_player_id"],
                )
                groups.setdefault(key, {}).setdefault(
                    row["identity"]["source_player_id"], []
                ).append(oid)
        for aliases in groups.values():
            if len(aliases) <= 1:
                continue
            member_ids = [oid for group in aliases.values() for oid in group]
            statuses = [effective[oid] for oid in member_ids]
            representative_ids = [oid for oid in member_ids if effective[oid] == "eligible"]
            if not (
                all(x == "blocked_alias_conflict" for x in statuses)
                or (
                    len(representative_ids) == 1
                    and all(x in ("eligible", "excluded_reconciled_alias") for x in statuses)
                )
            ):
                fail(
                    "ALIAS_CONFLICT",
                    "/observations",
                    "Aliases need quarantine or one reviewed representative at every cutoff.",
                )
            elif len(representative_ids) == 1:
                representative_id = representative_ids[0]
                for oid in member_ids:
                    if (
                        effective[oid] == "excluded_reconciled_alias"
                        and states[oid]["alias_of_observation_id"] != representative_id
                    ):
                        fail(
                            "ALIAS_REPRESENTATIVE",
                            "/observations",
                            "Reviewed alias must bind the eligible observation at this cutoff.",
                        )
    for i, receipt in enumerate(envelope["retrieval_receipts"]):
        oid = receipt["source_observation_id"]
        path = f"/retrieval_receipts/{i}"
        if oid not in ids:
            fail("RECEIPT_SOURCE", path, "Receipt must name a retained observation.")
        elif receipt["source_snapshot_ref"] != ids[oid]["source_snapshot_ref"] or _instant(
            receipt["retrieved_at"]
        ) <= _instant(ids[oid]["retrieved_at"]):
            fail(
                "RECEIPT_SOURCE",
                path,
                "Repeat receipt must be later and point to identical retained source material.",
            )
        if _instant(receipt["retrieved_at"]) > _instant(envelope["generated_at"]):
            fail("RECEIPT_CLOCK", path, "Receipt postdates artifact generation.")
        if [r["receipt_id"] for r in envelope["retrieval_receipts"]].count(
            receipt["receipt_id"]
        ) != 1:
            fail("RECEIPT_DUPLICATE", path, "Receipt ID must be unique.")


def corrected_leaf_ids(envelope: dict) -> list[str]:
    """Minimal fail-closed selector; no checkpoint, scoring or aggregation engine."""
    findings = validate(envelope)
    if findings:
        raise ValueError("Invalid observation envelope")
    rows = envelope["observations"]
    if any(
        r["source_relationship"]["status"] in ("unresolved", "older_discovered_later") for r in rows
    ):
        raise ValueError("Source assertion ordering unresolved; corrected leaf unavailable")
    superseded = {r["supersedes"] for r in rows if r["supersedes"] is not None}
    return sorted(r["observation_id"] for r in rows if r["observation_id"] not in superseded)


def main() -> int:
    if len(sys.argv) != 2:
        print(
            "usage: python -m src.contracts.college_player_game_observations_v0 FILE",
            file=sys.stderr,
        )
        return 2
    try:
        payload = json.loads(Path(sys.argv[1]).read_text(), object_pairs_hook=_unique_keys)
        findings = validate(payload)
    except (OSError, ValueError) as exc:
        print(json.dumps({"valid": False, "error": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps({"valid": not findings, "findings": findings}, sort_keys=True))
    return int(bool(findings))


def _unique_keys(pairs: list[tuple[str, Any]]) -> dict:
    result: dict = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


if __name__ == "__main__":
    raise SystemExit(main())

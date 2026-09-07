#!/usr/bin/env python3
"""Offline, read-only admission proposal for Data #263 / Fantasy #360.

Reads pinned committed evidence and prints an audit to stdout. --check compares
that result with the committed audit. Never fetches, promotes, or writes files.
This is a bounded audit, not a production identity resolver or consumer gate.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = "6fd0754e74a63f940ae3fa74140715f1e03b4840"
REPORT = "docs/audits/draft-review-evidence-admission-2026-09-07.json"
CANDIDATES = "exports/candidates/identity_crosswalk/identity_crosswalk_candidates_v0.json"
CROSSWALK = "exports/promoted/identity_crosswalk/tiber_identity_crosswalk_v2.json"
COVERAGE = "exports/promoted/nfl/player_season_coverage_v0.json"
CONFLICTS = "exports/candidates/identity_crosswalk/identity_crosswalk_review_v0.csv"
USAGE = "data/processed/evidence/player_weekly_usage_2025.source_backed.json"
OUTCOMES = "data/processed/evidence/player_weekly_ppr_outcomes_2025.source_backed.json"
PINS = {
    CANDIDATES: "45a69f2176104249d3ea416ccdd71dadd8196c6f5dfe3f1bf4e303580ecf47cd",
    CROSSWALK: "e6c6f8720352f1b94bf0a60fc5c6a2af7995b2b86b87ef9170b18ef3fcc96f9c",
    COVERAGE: "d45f612b207085df00b4b080e4f55ce1abbd060dcbf30b0bee777ff833ddd8ac",
    CONFLICTS: "3f7002c33e6ef31a07e1a63db10f3ecbeefcb0328f78e083893973f55ea137f8",
    USAGE: "30a8e17370270e2fa5d055c7a771f19af2fe7bd89282cd2373f7704a492412cb",
    OUTCOMES: "f241112115c9a625abead3410db89db6b4a8b603ce1dd663a45ff0697563e3a2",
    "scripts/build_player_weekly_usage_source_backed_2025.py": "6d3a3313b2355897dca6762eb554f0d7527a7f896f7d2fd3f407f1286726e020",
    "scripts/build_player_weekly_ppr_outcomes_source_backed_2025.py": "0b54704b3c3c428500b586bbff58a5386d5e50b336e84a2b126ea8718480033f",
    "scripts/promote_identity_crosswalk_rows.py": "840e4b73dc6f586f9584ae056e63d67216c89bf373caef99242e7a13a0e3d0fa",
    "schemas/tiber_identity_crosswalk_v2.schema.json": "e2cbb780013e4baaad3d52c61aabd5b7a1576f2b54f72de848c9c2cd9a3fc0f7",
    "exports/promoted/nfl/player_weekly_usage_v1.json": "425db119ed6b6d78bead9a638a4295703bf316547c4b76c0022b0de765804260",
    "exports/promoted/nfl/player_weekly_ppr_outcomes_v1.json": "20a0cb0494a5bae30e2d667cf0572a50a6dcde60fb2de33a317529716ce095f5",
}
# Exact proposed edges authorized for review; these are not runtime mappings.
EDGES = {"7526": "00-0036613", "12512": "00-0040784",
         "12481": "00-0040715", "7594": "00-0036555"}
REFERENCE = {"9997": "00-0039064"}
OUTCOME_FIELDS = ["targets", "receptions", "rushing_attempts", "receiving_yards",
                  "receiving_tds", "rushing_yards", "rushing_tds", "passing_yards",
                  "passing_tds", "interceptions"]
UNSUPPORTED = ["routes_run", "route_participation", "team_rushing_attempts",
               "rush_share", "red_zone_targets", "red_zone_carries", "snap_share"]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def read_pinned(root: Path, path: str) -> bytes:
    raw = (root / path).read_bytes()
    require(hashlib.sha256(raw).hexdigest() == PINS[path], f"source hash drift: {path}")
    return raw


def index_rows(rows: list[dict]) -> dict[tuple, dict]:
    result = {}
    for row in rows:
        key = (row["season"], row["week"], row["player_id"])
        require(key not in result, f"duplicate weekly key: {key}")
        require(type(key[0]) is int and key[0] == 2025 and
                type(key[1]) is int and 1 <= key[1] <= 22, "unexpected source window")
        result[key] = row
    return result


def inspect_identities(candidate: dict, promoted: dict, coverage: dict, conflicts: list[dict]) -> list[dict]:
    require(candidate["status"] == "candidate_only", "candidate authority changed")
    require("consume without operator promotion review" in candidate["consumer_safety"]["not_allowed"],
            "candidate consumer boundary missing")
    require(promoted["id_vocabulary"] == "gsis", "wrong crosswalk vocabulary")
    rows = candidate["rows"]
    proposed = []
    # V2's existing validator accepts second-precision UTC. Retain the full
    # candidate-generation clock separately; this is not a provider update time.
    clock = datetime.fromisoformat(candidate["generated_at"]).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    for sid, pid in EDGES.items():
        matches = [r for r in rows if r["sleeper_id"] == sid or r["tiber_player_id"] == pid]
        require(len(matches) == 1, f"ambiguous candidate edge: {sid}")
        row = matches[0]
        require((row["sleeper_id"], row["tiber_player_id"]) == (sid, pid), f"candidate edge conflict: {sid}")
        require(row["match_tier"] == "name_exact", f"unexpected evidence tier: {sid}")
        require(row["evidence"]["sleeper_gsis_id"] is None and row["evidence"]["sleeper_espn_id"] is None,
                f"provider evidence changed: {sid}")
        require(not any(r["provider_player_id"] == sid or r["tiber_player_id"] == pid
                        for r in promoted["records"]), f"promoted collision: {sid}")
        require(not any(r["player_id"] == pid or r.get("gsis_match") == sid or r.get("espn_match") == sid
                        for r in conflicts), f"candidate review conflict: {sid}")
        cr = [r for r in coverage["records"] if r["player_id"] == pid and r["season"] == 2025 and r["season_type"] == "REG"]
        require(len(cr) == 1 and cr[0]["player_name"] == row["player_name"] and cr[0]["position"] == row["position"] and
                cr[0]["provider_ids"]["espn_id"] == row["evidence"]["coverage_espn_id"],
                f"canonical coverage disagreement: {sid}")
        proposed.append({"provider": "sleeper", "provider_player_id": sid,
                         "provider_canonical_id": f"sleeper:{sid}", "tiber_player_id": pid,
                         "player_name": row["player_name"], "position": row["position"],
                         "team": row["evidence"]["sleeper_team"], "confidence": "medium",
                         "match_method": "name_exact", "source": CANDIDATES,
                         "source_updated_at": clock})
    return proposed


def inspect_weekly(usage: dict, outcomes: dict) -> dict:
    for wrapper in [usage, outcomes]:
        require(wrapper["provenance"] == "nflreadpy.load_player_stats", "wrong weekly source")
    ui, oi = index_rows(usage["records"]), index_rows(outcomes["records"])
    require(ui.keys() <= oi.keys(), "usage lacks outcome support")
    for key, u in ui.items():
        o = oi[key]
        require(all(u[f] == o[f] for f in ["targets", "receptions", "rushing_attempts", "team", "opponent"]),
                f"cross-source disagreement: {key}")
        require(all(u[f] is None for f in UNSUPPORTED), "unsupported field gained values")
        for field in ["target_share", "air_yards_share"]:
            value = u[field]
            require(value is None or (type(value) in (int, float) and math.isfinite(value)), "invalid share")
        require(u["target_share"] is None or 0 <= u["target_share"] <= 1, "invalid target share")
    mismatches = [{"season": k[0], "week": k[1], "player_id": k[2],
                   "usage_position": u["position"], "outcome_position": oi[k]["position"]}
                  for k, u in sorted(ui.items()) if k[1] <= 18 and u["position"] != oi[k]["position"]]
    subjects = []
    for sid, pid in {**REFERENCE, **EDGES}.items():
        ur = [r for k, r in ui.items() if k[2] == pid and k[1] <= 18]
        ore = [r for k, r in oi.items() if k[2] == pid and k[1] <= 18]
        subjects.append({"sleeper_id": sid, "inspected_gsis": pid,
                         "identity_status": "already_promoted" if sid in REFERENCE else "proposed_unadmitted",
                         "usage_weeks": sorted(r["week"] for r in ur),
                         "outcome_weeks": sorted(r["week"] for r in ore),
                         "historical_teams": sorted({r["team"] for r in ore}),
                         "position_conflict": any(u["position"] != oi[k]["position"] for k, u in ui.items()
                                                  if k[2] == pid and k[1] <= 18)})
    return {"usage_rows": len(ui), "outcome_rows": len(oi),
            "usage_regular_season_rows": sum(k[1] <= 18 for k in ui),
            "outcome_regular_season_rows": sum(k[1] <= 18 for k in oi),
            "regular_season_position_conflicts": mismatches, "subjects": subjects}


def build_report(root: Path = ROOT) -> dict:
    raw = {p: read_pinned(root, p) for p in PINS}
    candidate, promoted, coverage = [json.loads(raw[p]) for p in [CANDIDATES, CROSSWALK, COVERAGE]]
    require(candidate["sources"]["coverage_artifact"]["sha256"] == PINS[COVERAGE], "candidate coverage lineage drift")
    for sid, pid in REFERENCE.items():
        require(sum(r["provider_player_id"] == sid and r["tiber_player_id"] == pid for r in promoted["records"]) == 1,
                "reference identity changed")
    proposal = inspect_identities(candidate, promoted, coverage, list(csv.DictReader(io.StringIO(raw[CONFLICTS].decode()))))
    weekly = inspect_weekly(json.loads(raw[USAGE]), json.loads(raw[OUTCOMES]))
    fixtures = {}
    for path in [p for p in PINS if p.startswith("exports/promoted/nfl/player_weekly_")]:
        rows = json.loads(raw[path])
        require(all(r["source"].startswith("offline_fixture:") for r in rows), "fixture lane changed")
        fixtures[path] = len(rows)
    return {
        "schema_version": "draft_review_evidence_admission_proposal_v0_1",
        "status": "proposed_inactive", "consumer_allowed": False,
        "operator_admission_decision": None, "review_record": "Data #263 / linked exact-head PR review",
        "data_commit": BASE, "fantasy_base_commit": "8e2da54a572038d889d02c85fb5e84fad712aedb",
        "sources": [{"path": p, "sha256": h} for p, h in PINS.items()],
        "identity": {"proposed_records": proposal, "existing_records": len(promoted["records"]),
                     "resulting_count_if_later_promoted": len(promoted["records"]) + len(proposal),
                     "candidate_generation_time": candidate["generated_at"],
                     "source_updated_at_semantics": "candidate generation time truncated to V2 second precision; provider update time unknown",
                     "provider_update_time": None,
                     "raw_sleeper_replay": "unavailable; original dump hash retained, original match census not rerun",
                     "raw_sleeper_sha256": candidate["sources"]["sleeper_players_dump"]["sha256"],
                     "name_matching_at_consumption": "prohibited"},
        "historical_validation": weekly, "canonical_fixture_rows_excluded": fixtures,
        "proposed_consumer_scope": {
            "consumer": "TIBER-Fantasy Draft Review / issue 360", "season": 2025, "weeks": [1, 18],
            "period_basis": "documented 2025 regular-season week boundary; game_type/game_id absent",
            "mode": "retrospective_descriptive_only", "exact_approved_identity_required": True,
            "outcome_fields": OUTCOME_FIELDS, "usage_fields": ["target_share", "air_yards_share"],
            "air_yards": "excluded: zero origin ambiguous after legacy defaulting",
            "unavailable_usage_fields": UNSUPPORTED,
            "join_policy": "season/week/GSIS exact; cross-lane context or position conflict blocks joined derivations",
            "missing_usage_policy": "retain independent outcomes; usage unavailable, never fabricate a row",
            "missing_week_policy": "unknown, not bye/DNP/injury/zero",
            "aggregation_policy": "same explicit calendar window; report recorded weeks and nonnull denominators; average weekly share is not season share",
            "scoring": "raw statistics only; no league fantasy points or scoring subtotal in this grant",
            "source_acquired_at": None, "source_updated_at": None, "original_release_hash": None,
            "package_version": None, "forecast_allowed": False, "refresh_allowed": False,
            "public_rights_receipt": "proposal and dated primary-source references in companion Markdown; not effective admission",
            "attribution_required": "nflverse contributors; source and CC-BY-4.0 links; identify TIBER filtering/aggregation; retain supplied notices",
        },
    }


def render_report(report: dict) -> str:
    return json.dumps(report, indent=2, allow_nan=False) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    rendered = render_report(build_report())
    if args.check:
        require((ROOT / REPORT).read_text() == rendered, "committed audit differs from pinned replay")
        print("Pinned admission proposal replay matches; consumer_allowed=false.")
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()

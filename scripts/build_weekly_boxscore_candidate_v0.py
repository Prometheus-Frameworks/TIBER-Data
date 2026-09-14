"""Offline, candidate-only weekly box-score facts. No scores, buckets or promotion."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

FIELDS = (
    "completions", "attempts", "passing_yards", "passing_tds",
    "passing_interceptions", "sacks_suffered", "sack_fumbles_lost",
    "carries", "rushing_yards", "rushing_tds", "rushing_fumbles_lost",
    "receptions", "targets", "receiving_yards", "receiving_tds",
    "receiving_fumbles_lost", "fumbles_lost_total",
    "passing_2pt_conversions", "rushing_2pt_conversions",
    "receiving_2pt_conversions", "receiving_air_yards",
    "receiving_yards_after_catch", "passing_first_downs",
    "rushing_first_downs", "receiving_first_downs",
)
SIGNED_FIELDS = {"passing_yards", "rushing_yards", "receiving_yards",
                 "receiving_air_yards", "receiving_yards_after_catch"}
MISSING = {"", "NA", "NaN", "null"}


def integer(value: str | None, field: str) -> int | None:
    if value is None or value in MISSING:
        return None
    if not re.fullmatch(r"-?\d+(?:\.0+)?", value):
        raise ValueError(f"Non-integer value in {field}")
    result = int(value.split(".")[0])
    if abs(result) > 1_000_000 or (result < 0 and field not in SIGNED_FIELDS):
        raise ValueError(f"Invalid range in {field}")
    return result


def parse(raw: bytes, scope: dict, player: bool) -> tuple[list[dict], list[str], int, list[dict]]:
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
    headers = reader.fieldnames or []
    required = {"season", "week", "season_type", "game_id", "team", "opponent_team"}
    if player:
        required.add("player_id")
    if len(set(headers)) != len(headers) or not required.issubset(headers):
        raise ValueError("Missing or duplicate identity columns")
    rows, seen, excluded, unattributed = [], set(), 0, []
    for number, raw_row in enumerate(reader, 2):
        if None in raw_row or any(v is None for v in raw_row.values()):
            raise ValueError(f"Malformed CSV row {number}")
        if (raw_row["season"], raw_row["season_type"], raw_row["week"]) != (
            str(scope["season"]), scope["season_type"], str(scope["week"])
        ):
            excluded += 1
            continue
        game_required = required - {"player_id"}
        if any(not raw_row[k] or raw_row[k] != raw_row[k].strip() for k in game_required):
            raise ValueError(f"Unusable identity at row {number}")
        if player and not re.fullmatch(r"00-\d{7}", raw_row["player_id"]):
            unattributed.append({"identity": {k: raw_row[k] for k in sorted(game_required)},
                "raw_player_id": raw_row["player_id"], "source_csv_row": number,
                "reason": "unresolved_source_player_id", "source": "nflverse_stats_player",
                "observed": {f: integer(raw_row.get(f), f) for f in FIELDS}})
            continue
        key = (raw_row["game_id"], raw_row["team"])
        if player:
            key += (raw_row["player_id"],)
        if key in seen:
            raise ValueError(f"Duplicate source key {key}")
        seen.add(key)
        identity = {k: raw_row[k] for k in sorted(required)}
        identity["season"], identity["week"] = scope["season"], scope["week"]
        if player:
            identity.update(player_name=raw_row.get("player_display_name") or None,
                            position=raw_row.get("position") or None)
        rows.append({"identity": identity, "source_csv_row": number,
                     "observed": {f: integer(raw_row.get(f), f) for f in FIELDS}})
    if not rows:
        raise ValueError("Requested week has no source rows")
    return rows, headers, excluded, unattributed


def build_candidate(player_raw: bytes, team_raw: bytes, receipt: dict) -> dict:
    if receipt.get("status") != "unadmitted_candidate_source_snapshot":
        raise ValueError("Unexpected source receipt status")
    scope = receipt["requested_scope"]
    if (type(scope.get("season")) is not int or type(scope.get("week")) is not int
            or scope.get("season_type") != "REG"
            or not 1900 <= scope["season"] <= 2200 or not 1 <= scope["week"] <= 18):
        raise ValueError("Invalid explicit REG scope")
    for kind, raw in (("player", player_raw), ("team", team_raw)):
        pin = receipt["sources"][kind]
        if len(raw) != pin["byte_count"] or hashlib.sha256(raw).hexdigest() != pin["sha256"]:
            raise ValueError(f"{kind} source bytes do not match receipt")
    players, ph, pe, unattributed = parse(player_raw, scope, True)
    teams, th, te, _ = parse(team_raw, scope, False)
    team_index = {(r["identity"]["game_id"], r["identity"]["team"]): r for r in teams}
    grouped = defaultdict(list)
    for row in players + unattributed:
        i = row["identity"]
        key = (i["game_id"], i["team"])
        if key not in team_index or i["opponent_team"] != team_index[key]["identity"]["opponent_team"]:
            raise ValueError(f"Player/team identity disagreement for {key}")
        grouped[key].append(row)
    checks = {}
    for key, team in team_index.items():
        identity = team["identity"]
        opposite = team_index.get((key[0], identity["opponent_team"]))
        if key[1] == identity["opponent_team"] or not opposite or opposite["identity"]["opponent_team"] != key[1]:
            raise ValueError(f"Missing or conflicting opponent pair for {key}")
        checks[key] = {}
        for field in FIELDS:
            values = [r["observed"][field] for r in grouped[key]]
            subtotal = sum(values) if values and all(v is not None for v in values) else None
            total = team["observed"][field]
            status = "unknown" if subtotal is None or total is None else (
                "matched" if subtotal == total else "conflict")
            checks[key][field] = {"status": status, "player_sum": subtotal, "team_value": total}
        team["reconciliation"] = checks[key]
        team["source"] = "nflverse_stats_team"
    for row in players:
        identity, obs = row["identity"], row["observed"]
        key = (identity["game_id"], identity["team"])
        row["source"] = "nflverse_stats_player"
        row["team_reference"] = {"game_id": key[0], "team": key[1]}
        row["derived"] = {"carries_plus_targets": (
            obs["carries"] + obs["targets"] if obs["carries"] is not None and obs["targets"] is not None else None)}
        for field, output in (("targets", "target_share_credited_team_targets"),
                              ("carries", "carry_share_all_team_carries")):
            check = checks[key][field]
            denominator = check["team_value"]
            available = check["status"] == "matched" and denominator > 0 and obs[field] is not None
            row["derived"][output] = {"numerator": obs[field], "denominator": denominator,
                "value": obs[field] / denominator if available else None,
                "status": "available" if available else "unavailable",
                "reason": None if available else (
                    check["status"] if check["status"] != "matched" else "zero_or_missing_denominator")}
    players.sort(key=lambda r: tuple(r["identity"][k] for k in ("game_id", "team", "player_id")))
    teams.sort(key=lambda r: (r["identity"]["game_id"], r["identity"]["team"]))
    games = sorted({r["identity"]["game_id"] for r in teams})
    game_counts = Counter(r["identity"]["game_id"] for r in teams)
    if any(n != 2 for n in game_counts.values()):
        raise ValueError("A source game must have exactly two reciprocal team rows")
    conflicts = [{"game_id": key[0], "team": key[1], "field": field, **result}
        for key in sorted(checks) for field, result in checks[key].items() if result["status"] == "conflict"]
    return {"schema_version": "weekly_boxscore_candidate_v0", "status": "candidate_needs_review",
        "consumer_admitted": False, "scope": scope,
        "snapshot_compiled_at": receipt["snapshot_compiled_at"],
        "source_receipt": receipt,
        "coverage": {"source_player_rows_in_scope": len(players) + len(unattributed),
            "player_rows": len(players), "unattributed_player_rows": len(unattributed), "team_rows": len(teams),
            "game_ids": games, "game_count": len(games),
            "positions": dict(sorted(Counter(r["identity"]["position"] or "unknown" for r in players).items())),
            "excluded_out_of_scope_rows": {"player": pe, "team": te},
            "full_week_completeness": "unverified", "game_finality": "unverified",
            "player_universe": "all identity-resolved source rows in scope; unattributed rows separate; not an active-roster or participation census"},
        "validation": {"source_hashes": "matched", "duplicate_keys": 0,
            "opponent_pairs": "matched", "metric_conflicts": conflicts,
            "missing_columns": {"player": sorted(set(FIELDS) - set(ph)), "team": sorted(set(FIELDS) - set(th))},
            "null_values": {kind: {f: sum(r["observed"][f] is None for r in rows) for f in FIELDS}
                for kind, rows in (("player", players), ("team", teams))},
            "independent_review": "pending"},
        "unavailable": ["routes", "route_participation", "snap_share", "first_read_share",
            "inside_five_work", "red_zone_work", "designed_runs", "scrambles", "injury_context"],
        "limitations": ["Descriptive candidate only; no fantasy scoring, bucket classification or forecasts.",
            "No Sleeper-to-GSIS admission, ownership, eligibility, health or transaction inference.",
            "Raw game-team and source position retained; no current-team rewrite or name join.",
            "Shares use explicit team targets/carries only after same-snapshot population reconciliation.",
            "All-team carry share includes quarterbacks; it is not RB-only backfield share.",
            "Missing observations stay null; missing players are not zero-usage players.",
            "No schedule or game-status source read; listed games are not certified final or a complete week.",
            "Team reconciliation includes unattributed source observations with valid game/team keys; they are never player identities.",
            "Reconciliation is internal to nflverse, not independent box-score corroboration.",
            "Historical replay and independent review remain required before live evidence promotion."],
        "teams": teams, "players": players, "unattributed_source_observations": unattributed}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip())
    source_dir, output = args.source_dir.resolve(), args.output.resolve()
    output.relative_to(root / "exports" / "candidates" / "weekly_boxscore")
    if output.exists():
        raise ValueError("Output already exists; preserve candidate versions")
    if not re.fullmatch(r"[0-9a-f]{40}", args.source_commit):
        raise ValueError("An exact source-support commit is required")
    source_commit = args.source_commit
    contents = {}
    for name in ("player.csv", "team.csv", "receipt.json", "LICENSE.md"):
        path = source_dir / name
        relative = path.relative_to(root).as_posix()
        raw = path.read_bytes()
        committed = subprocess.check_output(["git", "show", f"{source_commit}:{relative}"])
        if raw != committed:
            raise ValueError(f"Uncommitted source support: {name}")
        contents[name] = raw
    receipt = json.loads(contents["receipt.json"])
    if hashlib.sha256(contents["LICENSE.md"]).hexdigest() != receipt["attribution"]["license_sha256"]:
        raise ValueError("License snapshot mismatch")
    candidate = build_candidate(contents["player.csv"], contents["team.csv"], receipt)
    candidate["source_support_commit"] = source_commit
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x") as handle:
        json.dump(candidate, handle, indent=2, allow_nan=False)
        handle.write("\n")
    print(json.dumps({"output": str(output), "coverage": candidate["coverage"],
                      "metric_conflicts": len(candidate["validation"]["metric_conflicts"])}))


if __name__ == "__main__":
    main()

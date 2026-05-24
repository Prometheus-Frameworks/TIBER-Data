from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

ROSTER_SOURCE_PATH = ROOT / "data/processed/evidence/roster_player_team_map_2025.source_backed.json"
DRAFT_SOURCE_PATH = ROOT / "exports/promoted/nfl_draft_results/nfl_draft_results_2026.json"
OUTPUT_SOURCE_PATH = (
    ROOT / "data/raw/player_ownership/player_ownership_source_roster_smoke_test_2026_05_24.json"
)
PREVIOUS_LATEST_PATH = ROOT / "exports/promoted/player_ownership/player_ownership_latest.json"
OWNERSHIP_SCHEMA_PATH = ROOT / "schemas/player_ownership_v0.schema.json"

SMOKE_TEST_NAMES: list[str] = [
    "Jalen Hurts",
    "Geno Smith",
    "Michael Penix",
    "Garrett Nussmeier",
    "Omarion Hampton",
    "Chris Rodriguez",
    "Jonah Coleman",
    "Joe Mixon",
    "Tank Bigsby",
    "Eli Heidenreich",
    "Mike Washington",
    "Seth McGowan",
    "Christian Watson",
    "Ladd McConkey",
    "Tet McMillan",
    "Jordyn Tyson",
    "Khalil Shakir",
    "Tory Horton",
    "Keon Coleman",
    "Jaylin Noel",
    "Kyle Williams",
    "Romeo Doubs",
    "Antonio Williams",
    "Colston Loveland",
    "Dallas Goedert",
    "Juwan Johnson",
]

# Input name → canonical source name (Jr. suffixes and known nicknames)
NAME_ALIASES: dict[str, str] = {
    "Michael Penix": "Michael Penix Jr.",
    "Chris Rodriguez": "Chris Rodriguez Jr.",
    "Tet McMillan": "Tetairoa McMillan",
    "Mike Washington": "Mike Washington Jr.",
}

# Approximate week-end roster observation dates for 2025-2026 season
WEEK_TO_OBSERVED_AT: dict[int, str] = {
    18: "2026-01-05T00:00:00Z",
    19: "2026-01-12T00:00:00Z",
    20: "2026-01-19T00:00:00Z",
    21: "2026-01-26T00:00:00Z",
    22: "2026-02-09T00:00:00Z",
}

NFL_TEAM_NAMES: dict[str, str] = {
    "ARI": "Arizona Cardinals",
    "ATL": "Atlanta Falcons",
    "BAL": "Baltimore Ravens",
    "BUF": "Buffalo Bills",
    "CAR": "Carolina Panthers",
    "CHI": "Chicago Bears",
    "CIN": "Cincinnati Bengals",
    "CLE": "Cleveland Browns",
    "DAL": "Dallas Cowboys",
    "DEN": "Denver Broncos",
    "DET": "Detroit Lions",
    "GB": "Green Bay Packers",
    "HOU": "Houston Texans",
    "IND": "Indianapolis Colts",
    "JAX": "Jacksonville Jaguars",
    "KC": "Kansas City Chiefs",
    "LAC": "Los Angeles Chargers",
    "LA": "Los Angeles Rams",
    "LV": "Las Vegas Raiders",
    "MIA": "Miami Dolphins",
    "MIN": "Minnesota Vikings",
    "NE": "New England Patriots",
    "NO": "New Orleans Saints",
    "NYG": "New York Giants",
    "NYJ": "New York Jets",
    "PHI": "Philadelphia Eagles",
    "PIT": "Pittsburgh Steelers",
    "SEA": "Seattle Seahawks",
    "SF": "San Francisco 49ers",
    "TB": "Tampa Bay Buccaneers",
    "TEN": "Tennessee Titans",
    "WAS": "Washington Commanders",
}

DRAFT_TEAM_NAME_TO_ABBR: dict[str, str] = {v: k for k, v in NFL_TEAM_NAMES.items()}

DRAFT_SOURCE_URL = (
    "https://www.nbcsports.com/nfl/profootballtalk/news/"
    "2026-nfl-draft-picks-full-tracker-of-every-selection-rounds-1-7"
)
DRAFT_SOURCE_NAME = "nfl_draft_results_2026_nbcsports_profootballtalk"
ROSTER_SOURCE_NAME = "nflreadpy_load_rosters_weekly_2025"
DRAFT_OBSERVED_AT = "2026-04-25T00:00:00Z"

RFC3339_UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def normalize_input_name(name: str) -> str:
    """Apply known alias mapping; return canonical source name."""
    return NAME_ALIASES.get(name, name)


def load_roster_by_latest_week(path: Path) -> dict[str, dict[str, Any]]:
    """Return dict keyed by lowercase player name → most-recent-week roster record."""
    data = json.loads(path.read_text(encoding="utf-8"))
    records = data.get("records", [])
    by_name: dict[str, dict[str, Any]] = {}
    for record in records:
        name_key = (record.get("player_name") or "").strip().lower()
        if not name_key:
            continue
        existing = by_name.get(name_key)
        if existing is None or record.get("week", 0) > existing.get("week", 0):
            by_name[name_key] = record
    return by_name


def load_draft_by_name(path: Path) -> dict[str, dict[str, Any]]:
    """Return dict keyed by lowercase player name → 2026 draft record."""
    records = json.loads(path.read_text(encoding="utf-8"))
    return {
        (r.get("player_name") or "").strip().lower(): r
        for r in records
        if r.get("player_name")
    }


def match_roster_player(
    normalized_name: str,
    roster_by_name: dict[str, dict[str, Any]],
) -> dict[str, Any] | None:
    return roster_by_name.get(normalized_name.strip().lower())


def match_draft_player(
    normalized_name: str,
    draft_by_name: dict[str, dict[str, Any]],
) -> dict[str, Any] | None:
    return draft_by_name.get(normalized_name.strip().lower())


def build_roster_row(input_name: str, record: dict[str, Any]) -> dict[str, Any]:
    """Build a source ownership row from an nflreadpy 2025 roster record."""
    team_abbr = (record.get("team") or "").upper()
    team_name = NFL_TEAM_NAMES.get(team_abbr, team_abbr)
    week = record.get("week", 18)
    observed_at = WEEK_TO_OBSERVED_AT.get(week, "2026-01-05T00:00:00Z")
    alias_note = (
        f"Input name '{input_name}' normalized to '{record['player_name']}'. "
        if input_name != record["player_name"]
        else ""
    )
    return {
        "player_id": record["player_id"],
        "player_name": record["player_name"],
        "position": record["position"],
        "football_level": "NFL",
        "team_id": f"nfl-{team_abbr.lower()}",
        "team_abbr": team_abbr,
        "team_name": team_name,
        "ownership_status": "active_roster",
        "valid_from": None,
        "valid_to": None,
        "ownership_confidence": "source_verified",
        "source_name": ROSTER_SOURCE_NAME,
        "observed_at": observed_at,
        "source_confidence": "source_verified",
        "notes": f"{alias_note}nflreadpy 2025 roster week {week}.",
    }


def build_draft_row(input_name: str, record: dict[str, Any]) -> dict[str, Any] | None:
    """Build a source ownership row from a 2026 NFL draft result record.

    Returns None if player_id is unresolved in the draft record.
    """
    if not record.get("player_id"):
        return None
    team_name = record.get("team") or ""
    team_abbr = DRAFT_TEAM_NAME_TO_ABBR.get(team_name, "")
    if not team_abbr:
        return None
    alias_note = (
        f"Input name '{input_name}' normalized to '{record['player_name']}'. "
        if input_name != record["player_name"]
        else ""
    )
    return {
        "player_id": record["player_id"],
        "player_name": record["player_name"],
        "position": record["position"],
        "football_level": "NFL",
        "team_id": f"nfl-{team_abbr.lower()}",
        "team_abbr": team_abbr,
        "team_name": team_name,
        "ownership_status": "unsigned_draft_pick",
        "valid_from": DRAFT_OBSERVED_AT,
        "valid_to": None,
        "ownership_confidence": "source_verified",
        "source_name": DRAFT_SOURCE_NAME,
        "source_url": DRAFT_SOURCE_URL,
        "observed_at": DRAFT_OBSERVED_AT,
        "source_confidence": "source_verified",
        "notes": (
            f"{alias_note}2026 NFL Draft round {record.get('round')}, "
            f"overall pick {record.get('overall_pick')}."
        ),
    }


def build_source_output(
    smoke_test_names: list[str],
    roster_by_name: dict[str, dict[str, Any]],
    draft_by_name: dict[str, dict[str, Any]],
    generated_at: str | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Build the source JSON payload and per-player match results.

    Returns: (source_payload, match_results)
    """
    generated_at = generated_at or _utc_now()
    player_rows: list[dict[str, Any]] = []
    match_results: list[dict[str, Any]] = []

    for input_name in smoke_test_names:
        normalized_name = normalize_input_name(input_name)

        roster_record = match_roster_player(normalized_name, roster_by_name)
        if roster_record:
            row = build_roster_row(input_name, roster_record)
            player_rows.append(row)
            match_results.append(
                {
                    "input_name": input_name,
                    "normalized_name": normalized_name,
                    "matched": True,
                    "source": "nflreadpy_roster_2025",
                    "player_id": roster_record["player_id"],
                    "position": roster_record["position"],
                    "football_level": "NFL",
                    "team_abbr": row["team_abbr"],
                    "team_name": row["team_name"],
                    "ownership_status": "active_roster",
                    "confidence": "source_verified",
                    "observed_at": row["observed_at"],
                    "name_normalized": input_name != normalized_name,
                    "warnings": [],
                }
            )
            continue

        draft_record = match_draft_player(normalized_name, draft_by_name)
        if draft_record:
            row = build_draft_row(input_name, draft_record)
            if row:
                player_rows.append(row)
                team_abbr = DRAFT_TEAM_NAME_TO_ABBR.get(draft_record.get("team", ""), "")
                match_results.append(
                    {
                        "input_name": input_name,
                        "normalized_name": normalized_name,
                        "matched": True,
                        "source": "nfl_draft_results_2026",
                        "player_id": draft_record["player_id"],
                        "position": draft_record["position"],
                        "football_level": "NFL",
                        "team_abbr": team_abbr,
                        "team_name": draft_record.get("team", ""),
                        "ownership_status": "unsigned_draft_pick",
                        "confidence": "source_verified",
                        "observed_at": DRAFT_OBSERVED_AT,
                        "name_normalized": input_name != normalized_name,
                        "warnings": [],
                    }
                )
            else:
                match_results.append(
                    {
                        "input_name": input_name,
                        "normalized_name": normalized_name,
                        "matched": False,
                        "source": "nfl_draft_results_2026",
                        "player_id": None,
                        "position": draft_record.get("position"),
                        "football_level": None,
                        "team_abbr": None,
                        "team_name": None,
                        "ownership_status": None,
                        "confidence": None,
                        "observed_at": None,
                        "name_normalized": input_name != normalized_name,
                        "warnings": ["draft_player_id_unresolved"],
                    }
                )
            continue

        match_results.append(
            {
                "input_name": input_name,
                "normalized_name": normalized_name,
                "matched": False,
                "source": None,
                "player_id": None,
                "position": None,
                "football_level": None,
                "team_abbr": None,
                "team_name": None,
                "ownership_status": None,
                "confidence": None,
                "observed_at": None,
                "name_normalized": input_name != normalized_name,
                "warnings": ["no_source_match"],
            }
        )

    source_payload: dict[str, Any] = {
        "source_name": "tiber_data_roster_smoke_test_2026_05_24",
        "generated_at": generated_at,
        "sources": [
            "data/processed/evidence/roster_player_team_map_2025.source_backed.json",
            "exports/promoted/nfl_draft_results/nfl_draft_results_2026.json",
        ],
        "notes": (
            "Smoke-test source for 26-player dynasty roster ownership coverage, 2026-05-24. "
            "Roster players sourced from nflreadpy 2025 weekly rosters; "
            "2026 rookies sourced from nfl_draft_results_2026."
        ),
        "players": player_rows,
    }

    return source_payload, match_results


def validate_source_payload(source_payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Validate the normalized source payload against player_ownership_v0.schema.json.

    Returns a list of validation error dicts (empty if valid).
    """
    import sys

    sys.path.insert(0, str(ROOT))
    from scripts.ingest_player_ownership import normalize_source_player, _validate_payload, _utc_now

    source_path = OUTPUT_SOURCE_PATH
    source_meta = {
        k: v
        for k, v in source_payload.items()
        if k not in {"players", "sources"} and not isinstance(v, (dict, list))
    }
    normalized_players = [
        normalize_source_player(row, source_meta=source_meta, source_path=source_path)
        for row in source_payload.get("players", [])
    ]
    normalized_payload = {
        "contract_version": "player_ownership_v0",
        "generated_at": source_payload.get("generated_at") or _utc_now(),
        "players": normalized_players,
    }
    errors, _ = _validate_payload(normalized_payload, scope="source_builder_validation")
    return errors


def build_promoted_payload(
    source_payload: dict[str, Any],
    previous_latest_path: Path,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Merge source-backed rows with previous latest, returning promoted payload.

    Previous records not in source are retained (absence is uncertainty, not release).
    Source-backed records overwrite previous records for the same player_id.
    """
    import sys

    sys.path.insert(0, str(ROOT))
    from scripts.ingest_player_ownership import normalize_source_player, _utc_now

    generated_at = generated_at or _utc_now()
    previous = json.loads(previous_latest_path.read_text(encoding="utf-8"))
    previous_players = previous.get("players", []) if isinstance(previous, dict) else []

    source_path = OUTPUT_SOURCE_PATH
    source_meta = {
        k: v
        for k, v in source_payload.items()
        if k not in {"players", "sources"} and not isinstance(v, (dict, list))
    }

    merged: dict[str, dict[str, Any]] = {
        str(p["player_id"]): p for p in previous_players if p.get("player_id")
    }
    for row in source_payload.get("players", []):
        normalized = normalize_source_player(row, source_meta=source_meta, source_path=source_path)
        player_id = normalized.get("player_id")
        if player_id:
            merged[str(player_id)] = normalized

    return {
        "contract_version": "player_ownership_v0",
        "generated_at": generated_at,
        "players": sorted(merged.values(), key=lambda p: (str(p.get("player_id") or ""), str(p.get("player_name") or ""))),
    }


def _atomic_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp")
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build player ownership source input for the 2026-05-24 smoke-test roster."
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help=(
            "Write the source JSON and promote validated rows to player_ownership_latest.json. "
            "Without --write, prints a dry-run summary only."
        ),
    )
    parser.add_argument(
        "--source-output",
        type=Path,
        default=OUTPUT_SOURCE_PATH,
        help="Path for the generated source JSON file.",
    )
    parser.add_argument(
        "--previous",
        type=Path,
        default=PREVIOUS_LATEST_PATH,
        help="Path for the current player_ownership_latest.json to merge against.",
    )
    parser.add_argument(
        "--latest-output",
        type=Path,
        default=PREVIOUS_LATEST_PATH,
        help="Path to write the promoted latest ownership artifact.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)

    roster_by_name = load_roster_by_latest_week(ROSTER_SOURCE_PATH)
    draft_by_name = load_draft_by_name(DRAFT_SOURCE_PATH)
    source_payload, match_results = build_source_output(
        SMOKE_TEST_NAMES, roster_by_name, draft_by_name
    )

    matched = [r for r in match_results if r["matched"]]
    unmatched = [r for r in match_results if not r["matched"]]
    name_normalized = [r for r in match_results if r["name_normalized"]]

    print(f"Smoke-test players: {len(match_results)}")
    print(f"  Matched:   {len(matched)}")
    print(f"  Unmatched: {len(unmatched)}")
    print(f"  Name normalizations: {len(name_normalized)}")
    for r in name_normalized:
        print(f"    '{r['input_name']}' -> '{r['normalized_name']}'")

    if unmatched:
        print("\nUnmatched players:")
        for r in unmatched:
            print(f"  {r['input_name']}: {r['warnings']}")

    validation_errors = validate_source_payload(source_payload)
    if validation_errors:
        print(f"\nValidation errors ({len(validation_errors)}):")
        for err in validation_errors:
            print(f"  [{err['path']}] {err['message']}")
        print("Source file not written (validation failed).")
        return 1

    print(f"\nValidation: OK ({len(source_payload['players'])} rows pass schema)")

    if args.write:
        _atomic_write(args.source_output, source_payload)
        print(f"Source written: {args.source_output}")

        promoted = build_promoted_payload(source_payload, args.previous)
        _atomic_write(args.latest_output, promoted)
        print(f"Promoted latest written: {args.latest_output} ({len(promoted['players'])} players)")
    else:
        print(f"\nDry-run complete. Use --write to write source and promoted artifacts.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

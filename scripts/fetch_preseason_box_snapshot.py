#!/usr/bin/env python3
"""Fetch NFL preseason box-score snapshots from ESPN's public API (issue #242).

Preseason is otherwise invisible to TIBER: nflverse publishes no preseason
play-by-play, Sleeper's `stats/nfl/pre` endpoint serves an empty object, and
the coverage audits enforce REG-only. August games are the only pre-week-1
source of live role/usage signal, so this script persists them as CANDIDATE
artifacts with explicit consumer-safety fencing.

ESPN is NOT an approved truth source (see TRUTH_SOURCES.md); these snapshots
must never be consumed as regular-season evidence or promoted without an
operator decision about source policy. Same standalone pattern as
TIBER-Fantasy's scripts/fetch_adp_snapshot.mjs: no repo imports, no DB,
nonzero exit on fetch/shape failure, safe to schedule.

Usage:
  python3 scripts/fetch_preseason_box_snapshot.py [--start YYYYMMDD] [--end YYYYMMDD]
      [--out exports/candidates/preseason_box]

Defaults to yesterday (UTC) through today, which suits a morning-after sweep.
"""
import argparse, json, os, sys, urllib.request
from datetime import datetime, timedelta, timezone

API = "https://site.api.espn.com/apis/site/v2/sports/football/nfl"


def get(url: str):
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.load(r)


def extract_box(summary: dict):
    """Flatten ESPN's boxscore players structure into per-player stat lines."""
    lines = []
    for team in (summary.get("boxscore", {}) or {}).get("players", []):
        abbr = (team.get("team") or {}).get("abbreviation")
        for cat in team.get("statistics", []):
            labels = cat.get("labels", [])
            for a in cat.get("athletes", []):
                ath = a.get("athlete") or {}
                lines.append({
                    "team": abbr,
                    "category": cat.get("name"),
                    "espn_athlete_id": ath.get("id"),
                    "player_name": ath.get("displayName"),
                    "stats": dict(zip(labels, a.get("stats", []))),
                })
    return lines


def main() -> int:
    ap = argparse.ArgumentParser()
    today = datetime.now(timezone.utc).date()
    ap.add_argument("--start", default=(today - timedelta(days=1)).strftime("%Y%m%d"))
    ap.add_argument("--end", default=today.strftime("%Y%m%d"))
    ap.add_argument("--out", default="exports/candidates/preseason_box")
    args = ap.parse_args()

    window = f"{args.start}-{args.end}"
    sb_url = f"{API}/scoreboard?dates={window}"
    try:
        sb = get(sb_url)
    except Exception as e:
        print(f"scoreboard fetch failed: {e}", file=sys.stderr)
        return 1

    events = sb.get("events", [])
    games, skipped, fetch_failures = [], [], []
    for e in events:
        season_type = (e.get("season") or {}).get("type")
        status = ((e.get("status") or {}).get("type") or {}).get("detail", "")
        if season_type != 1:  # 1 = preseason in ESPN's enum
            skipped.append({"name": e.get("name"), "reason": f"season_type={season_type}"})
            continue
        if "Final" not in str(status):
            skipped.append({"name": e.get("name"), "reason": f"not final ({status})"})
            continue
        eid = e["id"]
        comp = (e.get("competitions") or [{}])[0]
        score = {c.get("team", {}).get("abbreviation"): c.get("score")
                 for c in comp.get("competitors", [])}
        try:
            summary = get(f"{API}/summary?event={eid}")
        except Exception as ex:
            fetch_failures.append({"name": e.get("name"), "reason": f"summary fetch failed: {ex}"})
            continue
        games.append({
            "espn_event_id": eid,
            "name": e.get("name"),
            "date": e.get("date"),
            "status": status,
            "score": score,
            "player_lines": extract_box(summary),
        })

    if not games and not events:
        print(f"no NFL games in window {window}; nothing written")
        return 0

    fetched_at = datetime.now(timezone.utc).isoformat()
    artifact = {
        "kind": "preseason_box_snapshot",
        "schema_version": "preseason_box_snapshot_v0",
        "status": "candidate_only",
        "consumer_safety": {
            "not_allowed": [
                "consume as regular-season evidence",
                "join into REG season_type artifacts",
                "promote without operator source-policy review (ESPN is not an approved truth source)",
            ],
            "notes": "Preseason usage/box evidence only. Player identity is ESPN athlete id + "
                     "display name — join via the identity crosswalk before any cross-artifact use.",
        },
        "source": {"name": "espn_site_api", "scoreboard_url": sb_url, "fetched_at": fetched_at},
        "window": {"start": args.start, "end": args.end},
        "partial": bool(fetch_failures),
        "counts": {"events_seen": len(events), "games_captured": len(games),
                   "skipped": len(skipped), "fetch_failures": len(fetch_failures)},
        "skipped": skipped,
        "fetch_failures": fetch_failures,
        "games": games,
    }

    os.makedirs(args.out, exist_ok=True)
    path = os.path.join(args.out, f"preseason_box_snapshot_{args.start}_{args.end}.json")
    with open(path, "w") as f:
        json.dump(artifact, f, indent=1)
    total_lines = sum(len(g["player_lines"]) for g in games)
    print(f"captured {len(games)} final game(s), {total_lines} player lines, "
          f"skipped {len(skipped)}, fetch failures {len(fetch_failures)}")
    print(f"wrote {path}")
    if fetch_failures:
        # Partial publication is an explicit failure state: the artifact is written
        # (marked partial) but a scheduled run must not report success.
        print(f"PARTIAL snapshot — {len(fetch_failures)} game summary fetch(es) failed", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

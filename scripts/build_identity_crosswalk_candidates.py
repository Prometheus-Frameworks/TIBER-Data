#!/usr/bin/env python3
"""Build identity-crosswalk CANDIDATES from provider-declared IDs (issue #241).

Joins the promoted player_season_coverage universe (keyed by GSIS player_id)
to Sleeper's public players dump using three evidence tiers:

  T0 gsis_direct : Sleeper row declares gsis_id == coverage player_id
  T1 espn_bridge : coverage espn_id == Sleeper espn_id (no T0 available)
  T2 name_exact  : unique normalized-name + position match (no T0/T1)

Anything ambiguous or conflicting lands in a review CSV instead of the
candidates file. Output goes to exports/candidates/ only — this script never
touches exports/promoted/, and the artifact declares itself non-authoritative.
Promotion remains a manual operator decision per repo governance.

Usage:
  python3 scripts/build_identity_crosswalk_candidates.py \
      --sleeper-json /path/to/players_nfl.json \
      [--coverage exports/promoted/nfl/player_season_coverage_v0.json] \
      [--out exports/candidates/identity_crosswalk]

The Sleeper dump is https://api.sleeper.app/v1/players/nfl saved to disk
(pass --fetch to download it to a temp file instead).
"""
import argparse, csv, hashlib, json, os, re, sys, unicodedata, urllib.request
from datetime import datetime, timezone

SUFFIXES = re.compile(r"\b(jr|sr|ii|iii|iv|v)\b")

def norm_name(n: str) -> str:
    n = unicodedata.normalize("NFKD", n or "").encode("ascii", "ignore").decode()
    n = n.lower().replace("'", "").replace(".", "").replace("-", " ")
    return re.sub(r"\s+", " ", SUFFIXES.sub("", n)).strip()

def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sleeper-json")
    ap.add_argument("--fetch", action="store_true", help="download the Sleeper dump instead of reading a file")
    ap.add_argument("--coverage", default="exports/promoted/nfl/player_season_coverage_v0.json")
    ap.add_argument("--out", default="exports/candidates/identity_crosswalk")
    args = ap.parse_args()

    if args.fetch:
        args.sleeper_json = "/tmp/sleeper_players_nfl.json"
        urllib.request.urlretrieve("https://api.sleeper.app/v1/players/nfl", args.sleeper_json)
    if not args.sleeper_json or not os.path.exists(args.sleeper_json):
        print("need --sleeper-json <path> or --fetch", file=sys.stderr)
        return 1

    sleeper = json.load(open(args.sleeper_json))
    cov = json.load(open(args.coverage))
    rows = cov.get("rows") or cov.get("records") or []

    # one universe row per GSIS player_id, keeping the newest season's identity fields
    universe = {}
    for r in sorted(rows, key=lambda x: x.get("season") or 0):
        universe[r["player_id"]] = {
            "player_id": r["player_id"],
            "player_name": r.get("player_name"),
            "position": r.get("position"),
            "espn_id": (r.get("provider_ids") or {}).get("espn_id"),
            "last_season": r.get("season"),
        }

    by_gsis, by_espn, by_name = {}, {}, {}
    for sid, p in sleeper.items():
        if p.get("gsis_id"):
            by_gsis[str(p["gsis_id"]).strip()] = sid
        if p.get("espn_id"):
            by_espn[str(p["espn_id"])] = sid
        nm = norm_name(p.get("full_name") or ((p.get("first_name") or "") + " " + (p.get("last_name") or "")))
        if nm:
            by_name.setdefault((nm, p.get("position")), []).append(sid)

    candidates, review = [], []
    tiers = {"gsis_direct": 0, "espn_bridge": 0, "name_exact": 0}
    for pid, u in universe.items():
        sid_gsis = by_gsis.get(pid)
        sid_espn = by_espn.get(str(u["espn_id"])) if u["espn_id"] else None
        nm_key = (norm_name(u["player_name"]), u["position"])
        name_hits = by_name.get(nm_key, [])

        if sid_gsis and sid_espn and sid_gsis != sid_espn:
            review.append({**u, "issue": "gsis_vs_espn_conflict", "gsis_match": sid_gsis, "espn_match": sid_espn})
            continue
        if sid_gsis:
            tier, sid = "gsis_direct", sid_gsis
        elif sid_espn:
            tier, sid = "espn_bridge", sid_espn
        elif len(name_hits) == 1:
            tier, sid = "name_exact", name_hits[0]
        else:
            review.append({**u, "issue": "no_id_match_ambiguous_name" if name_hits else "no_match",
                           "name_hits": len(name_hits)})
            continue
        tiers[tier] += 1
        sp = sleeper[sid]
        candidates.append({
            "tiber_player_id": pid,
            "player_name": u["player_name"],
            "position": u["position"],
            "sleeper_id": sid,
            "match_tier": tier,
            "evidence": {
                "sleeper_gsis_id": sp.get("gsis_id"),
                "coverage_espn_id": u["espn_id"],
                "sleeper_espn_id": sp.get("espn_id"),
                "sleeper_name": sp.get("full_name"),
                "sleeper_team": sp.get("team"),
            },
            "last_coverage_season": u["last_season"],
        })

    now = datetime.now(timezone.utc).isoformat()
    artifact = {
        "kind": "identity_crosswalk_candidates",
        "schema_version": "identity_crosswalk_candidates_v0",
        "generated_at": now,
        "status": "candidate_only",
        "consumer_safety": {
            "not_allowed": [
                "treat as promoted identity truth",
                "consume without operator promotion review",
            ],
            "notes": "Provider-declared ID joins (tiers gsis_direct/espn_bridge) plus unique-name matches. "
                     "Review file rows are excluded here and require human adjudication.",
        },
        "sources": {
            "coverage_artifact": {"path": args.coverage, "sha256": sha256_file(args.coverage)},
            "sleeper_players_dump": {"path": os.path.basename(args.sleeper_json),
                                     "sha256": sha256_file(args.sleeper_json),
                                     "endpoint": "https://api.sleeper.app/v1/players/nfl"},
        },
        "counts": {"universe": len(universe), "candidates": len(candidates),
                   "by_tier": tiers, "review": len(review)},
        "rows": sorted(candidates, key=lambda x: x["tiber_player_id"]),
    }

    os.makedirs(args.out, exist_ok=True)
    out_json = os.path.join(args.out, "identity_crosswalk_candidates_v0.json")
    json.dump(artifact, open(out_json, "w"), indent=1)
    out_csv = os.path.join(args.out, "identity_crosswalk_review_v0.csv")
    with open(out_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["player_id", "player_name", "position", "last_season",
                                          "espn_id", "issue", "gsis_match", "espn_match", "name_hits"])
        w.writeheader()
        for r in review:
            w.writerow({k: r.get(k, "") for k in w.fieldnames})
    print(f"universe {len(universe)} -> candidates {len(candidates)} {tiers} | review {len(review)}")
    print(f"wrote {out_json}\nwrote {out_csv}")
    return 0

if __name__ == "__main__":
    sys.exit(main())

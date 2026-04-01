#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path

from src.team_state import (
    build_team_state_artifact,
    load_pbp_for_season,
    validate_artifact_shape,
    write_artifact,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate tiber_team_state_v0_1 artifact.")
    parser.add_argument("--season", type=int, required=True, help="NFL season year.")
    parser.add_argument("--through-week", type=int, default=None, help="Optional week cutoff.")
    parser.add_argument(
        "--pbp-path",
        type=str,
        default=None,
        help="Optional local pbp input file (.parquet, .csv, .json) for deterministic runs/tests.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("team-state/artifacts/tiber_team_state_v0_1.json"),
        help="Output artifact path.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    pbp = load_pbp_for_season(args.season, args.through_week, args.pbp_path)
    artifact = build_team_state_artifact(
        pbp=pbp,
        season=args.season,
        through_week=args.through_week,
    )
    validate_artifact_shape(artifact)
    path = write_artifact(artifact, args.output)
    print(f"Wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

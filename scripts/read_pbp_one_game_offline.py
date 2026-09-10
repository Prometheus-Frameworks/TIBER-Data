#!/usr/bin/env python3
"""Offline one-game PBP receipt verification and bounded read (Research #22 first PR).

Usage (all inputs explicit; nothing is guessed, downloaded, or written to a database):

    python scripts/read_pbp_one_game_offline.py \
        --path /local/path/play_by_play_2026.parquet \
        --expected-bytes 222639 \
        --expected-sha256 <exact sha256 of those bytes> \
        --season 2026 --date 2026-09-09 --away NE --home SEA \
        --possession-team SEA --possession-ordinal 2 \
        [--source-ref nflverse-data:pbp/play_by_play_2026] \
        [--retrieved-at 2026-09-10T18:14:57Z] [--published-at 2026-09-10T13:20:51Z] \
        [--out /local/path/result.json]

Exit codes: 0 = a result was produced (matched, read, or honestly unresolved);
2 = the input was rejected (missing file, byte/digest mismatch, unsupported format,
or a bounded parse failure after magic-byte verification) and nothing was written;
3 = invalid arguments; 4 = --out already exists (any existing path, including the
input file or an alias of it) so nothing was read or written; 5 = the reader's own
post-parse processing failed (reader_processing_failure, a reader defect that says
nothing about the source file) and nothing was written.

The result is local and non-canonical. It is not an ingestion, admission, promotion,
or Research activation. See docs/data/pbp-one-game-offline-read-v0.md.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.pbp_one_game.offline_read import (  # noqa: E402
    GameRequest,
    PossessionRequest,
    SourceDeclaration,
    dumps,
    read_one_game,
)


class _UsageErrorParser(argparse.ArgumentParser):
    """argparse exits 2 on usage errors by default; 2 is reserved here for source rejection."""

    def error(self, message: str) -> None:  # type: ignore[override]
        self.print_usage(sys.stderr)
        print(f"{self.prog}: error: {message}", file=sys.stderr)
        raise SystemExit(3)


def build_parser() -> argparse.ArgumentParser:
    parser = _UsageErrorParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--path", required=True, help="Explicit local path to the source parquet file."
    )
    parser.add_argument("--expected-bytes", required=True, type=int)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--season", required=True, type=int)
    parser.add_argument("--date", required=True, help="Requested game date, YYYY-MM-DD.")
    parser.add_argument("--away", required=True, help="Requested away team code.")
    parser.add_argument("--home", required=True, help="Requested home team code.")
    parser.add_argument("--possession-team", default=None)
    parser.add_argument("--possession-ordinal", default=None, type=int)
    parser.add_argument(
        "--source-ref", default=None, help="Provider/dataset reference, if known."
    )
    parser.add_argument("--retrieved-at", default=None, help="Retrieval time, if known.")
    parser.add_argument(
        "--published-at", default=None, help="Source publication time, if evidenced."
    )
    parser.add_argument(
        "--out", default=None, help="Write JSON here instead of stdout (only on exit 0)."
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if (args.possession_team is None) != (args.possession_ordinal is None):
        print(
            "--possession-team and --possession-ordinal must be supplied together",
            file=sys.stderr,
        )
        return 3
    request = GameRequest(
        season=args.season, game_date=args.date, away_team=args.away, home_team=args.home
    )
    try:
        request.validate()
    except ValueError as exc:
        print(f"invalid request: {exc}", file=sys.stderr)
        return 3
    possession = (
        PossessionRequest(team=args.possession_team, ordinal=args.possession_ordinal)
        if args.possession_team is not None
        else None
    )
    if args.out is not None and os.path.lexists(args.out):
        # Refuse any existing path (regular file, the input itself, a symlink or hardlink
        # alias of it, or a dangling symlink) before reading anything. Nothing is modified.
        print(
            f"refusing --out {args.out!r}: path already exists; the reader only creates a "
            "new output file and never overwrites the source or any existing file",
            file=sys.stderr,
        )
        return 4
    result = read_one_game(
        path=args.path,
        expected_bytes=args.expected_bytes,
        expected_sha256=args.expected_sha256,
        request=request,
        possession=possession,
        declaration=SourceDeclaration(
            provider_dataset_ref=args.source_ref,
            retrieved_at=args.retrieved_at,
            published_at=args.published_at,
        ),
    )
    text = dumps(result)
    if result["status"] == "rejected":
        sys.stdout.write(text)
        return 2
    if result["status"] == "processing_failed":
        # A reader defect after successful parsing: distinct from a source rejection.
        sys.stdout.write(text)
        return 5
    if args.out:
        try:
            # O_CREAT|O_EXCL: atomic exclusive creation. Fails (without truncating anything)
            # if the path appeared since the pre-check, including as a symlink.
            with open(args.out, "x", encoding="utf-8") as handle:
                handle.write(text)
        except FileExistsError:
            print(
                f"refusing --out {args.out!r}: path appeared before exclusive creation; "
                "no file was modified",
                file=sys.stderr,
            )
            return 4
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

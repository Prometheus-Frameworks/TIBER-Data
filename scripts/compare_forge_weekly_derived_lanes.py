from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

SUPPORTED_SEASON = 2024
SUPPORTED_WEEKS = (1, 2, 3)

LEGACY_DERIVED_PATTERN = "data/gold/forge/forge_weekly_player_input_2024_w{week:02d}.skill_offline_fixture.derived.json"
UPSTREAM_DERIVED_PATTERN = (
    "data/gold/forge/forge_weekly_player_input_2024_w{week:02d}."
    "skill_upstream_public_w01_w03_8player_scaffold.derived.json"
)

DISPLAY_FIELDS: tuple[str, ...] = (
    "targets",
    "receptions",
    "rushAttempts",
    "routesRun",
    "routeParticipation",
    "snapShare",
    "activeProjection",
    "roleVolatility",
    "featureCoverage",
    "qualityFlags",
    "sourceSetId",
)


def _load_artifact_records(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise RuntimeError(f"Expected artifact array in {path}, got {type(payload).__name__}.")
    return payload


def _load_week_records(pattern: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for week in SUPPORTED_WEEKS:
        path = Path(pattern.format(week=week))
        if not path.exists():
            raise FileNotFoundError(
                f"Missing derived artifact for supported week W{week}: {path}. "
                "Generate artifacts first."
            )
        rows.extend(_load_artifact_records(path))
    return rows


def _filter_records(
    rows: list[dict[str, Any]],
    *,
    player_id: str | None,
    player_name: str | None,
) -> list[dict[str, Any]]:
    filtered = [
        row
        for row in rows
        if int(row.get("season", 0)) == SUPPORTED_SEASON and int(row.get("week", 0)) in SUPPORTED_WEEKS
    ]
    if player_id:
        filtered = [row for row in filtered if str(row.get("playerId", "")) == player_id]
    if player_name:
        normalized = player_name.strip().lower()
        filtered = [row for row in filtered if str(row.get("playerName", "")).strip().lower() == normalized]
    return sorted(filtered, key=lambda row: (int(row["week"]), str(row["playerId"])))


def _fmt(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.4f}".rstrip("0").rstrip(".")
    if isinstance(value, list):
        return " | ".join(str(item) for item in value)
    return str(value)


def _print_row_block(field: str, legacy: dict[str, Any] | None, upstream: dict[str, Any] | None) -> None:
    legacy_value = "-" if legacy is None else _fmt(legacy.get(field, "-"))
    upstream_value = "-" if upstream is None else _fmt(upstream.get(field, "-"))
    print(f"  {field:20} legacy={legacy_value:<44} | upstream={upstream_value}")


def compare_derived_rows(
    legacy_rows: list[dict[str, Any]],
    upstream_rows: list[dict[str, Any]],
    *,
    player_id: str | None,
    player_name: str | None,
) -> None:
    filtered_legacy = _filter_records(legacy_rows, player_id=player_id, player_name=player_name)
    filtered_upstream = _filter_records(upstream_rows, player_id=player_id, player_name=player_name)

    legacy_by_key = {(int(row["week"]), str(row["playerId"])): row for row in filtered_legacy}
    upstream_by_key = {(int(row["week"]), str(row["playerId"])): row for row in filtered_upstream}

    keys = sorted(set(legacy_by_key) | set(upstream_by_key))

    print("\n=== Derived lane comparison (legacy skill_offline_fixture vs upstream scaffold skill) ===")
    if player_id or player_name:
        print(f"Focus filter: player_id={player_id or '-'} player_name={player_name or '-'}")

    if not keys:
        print("No derived rows matched filters in supported 2024 W1-W3 slice.")
        return

    for week, pid in keys:
        legacy = legacy_by_key.get((week, pid))
        upstream = upstream_by_key.get((week, pid))
        ref = legacy or upstream or {}
        print(
            f"\nW{week} | {ref.get('playerName', 'unknown')} ({pid}) | "
            f"{ref.get('position', 'unknown')} {ref.get('team', 'unknown')}"
        )
        for field in ("week", "playerName", "position", "team", *DISPLAY_FIELDS):
            _print_row_block(field, legacy, upstream)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare legacy vs upstream-scaffold FORGE derived weekly rows for 2024 W1-W3."
    )
    parser.add_argument("--player-name", default=None, help='Exact player name (e.g. "Amon-Ra St. Brown").')
    parser.add_argument("--player-id", default=None, help="Player id (e.g. 00-0037834).")
    parser.add_argument("--legacy-pattern", default=LEGACY_DERIVED_PATTERN)
    parser.add_argument("--upstream-pattern", default=UPSTREAM_DERIVED_PATTERN)
    args = parser.parse_args()

    legacy_rows = _load_week_records(args.legacy_pattern)
    upstream_rows = _load_week_records(args.upstream_pattern)

    print(f"Supported slice: season={SUPPORTED_SEASON}, weeks={list(SUPPORTED_WEEKS)}")
    compare_derived_rows(
        legacy_rows,
        upstream_rows,
        player_id=args.player_id,
        player_name=args.player_name,
    )


if __name__ == "__main__":
    main()

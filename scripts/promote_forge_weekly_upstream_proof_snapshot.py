from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

RAW_SOURCE_PATHS = (
    Path("data/raw/forge/weekly_player_stats.upstream_public_2024_w01_w03_8player_scaffold.json"),
    Path("data/raw/forge/team_week_context.upstream_public_2024_w01_w03_2team_scaffold.json"),
)

DERIVED_SOURCE_PATHS = (
    Path("data/gold/forge/forge_weekly_player_input_2024_w01.skill_upstream_public_w01_w03_8player_scaffold.derived.json"),
    Path("data/gold/forge/forge_weekly_player_input_2024_w02.skill_upstream_public_w01_w03_8player_scaffold.derived.json"),
    Path("data/gold/forge/forge_weekly_player_input_2024_w03.skill_upstream_public_w01_w03_8player_scaffold.derived.json"),
)

RAW_SNAPSHOT_PATHS = (
    Path("data/raw/forge/weekly_player_stats.upstream_public_2024_w01_w03_8player_scaffold.proof_reference_snapshot.json"),
    Path("data/raw/forge/team_week_context.upstream_public_2024_w01_w03_2team_scaffold.proof_reference_snapshot.json"),
)

DERIVED_SNAPSHOT_PATHS = (
    Path("data/gold/forge/forge_weekly_player_input_2024_w01.skill_upstream_public_w01_w03_8player_scaffold.proof_reference_snapshot.derived.json"),
    Path("data/gold/forge/forge_weekly_player_input_2024_w02.skill_upstream_public_w01_w03_8player_scaffold.proof_reference_snapshot.derived.json"),
    Path("data/gold/forge/forge_weekly_player_input_2024_w03.skill_upstream_public_w01_w03_8player_scaffold.proof_reference_snapshot.derived.json"),
)

MANIFEST_PATH = Path("data/forge_weekly_upstream_w01_w03_atl_det_proof_reference_snapshot_manifest.json")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _copy_pair(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def promote_snapshot(*, captured_at: str) -> dict[str, object]:
    missing = [str(path) for path in (*RAW_SOURCE_PATHS, *DERIVED_SOURCE_PATHS) if not path.exists()]
    if missing:
        raise FileNotFoundError(
            "Cannot promote proof snapshot. Generate upstream scaffold raw + derived files first. "
            f"Missing paths: {missing}"
        )

    for source, destination in zip(RAW_SOURCE_PATHS, RAW_SNAPSHOT_PATHS, strict=True):
        _copy_pair(source, destination)
    for source, destination in zip(DERIVED_SOURCE_PATHS, DERIVED_SNAPSHOT_PATHS, strict=True):
        _copy_pair(source, destination)

    manifest = {
        "snapshot_id": "forge_weekly_upstream_public_2024_w01_w03_atl_det_proof_reference",
        "captured_at": captured_at,
        "scope": {
            "season": 2024,
            "weeks": [1, 2, 3],
            "teams": ["ATL", "DET"],
            "cohort": "fixed_8_player_proof_slice",
        },
        "notes": [
            "Committed proof/reference specimen captured from the upstream-backed scaffold lane.",
            "Not a legacy-lane replacement and not full-season coverage.",
            "Refreshing this snapshot is deliberate/manual via this script.",
        ],
        "raw": [
            {
                "source": str(source),
                "snapshot": str(snapshot),
                "sha256": _sha256(snapshot),
            }
            for source, snapshot in zip(RAW_SOURCE_PATHS, RAW_SNAPSHOT_PATHS, strict=True)
        ],
        "derived": [
            {
                "source": str(source),
                "snapshot": str(snapshot),
                "sha256": _sha256(snapshot),
            }
            for source, snapshot in zip(DERIVED_SOURCE_PATHS, DERIVED_SNAPSHOT_PATHS, strict=True)
        ],
    }
    MANIFEST_PATH.write_text(f"{json.dumps(manifest, indent=2)}\n", encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Promote upstream scaffold W1-W3 ATL/DET outputs into committed proof/reference snapshot files."
    )
    parser.add_argument(
        "--captured-at",
        required=True,
        help="Capture timestamp used in snapshot manifest (example: 2026-04-10T00:00:00Z).",
    )
    args = parser.parse_args()

    manifest = promote_snapshot(captured_at=args.captured_at)
    print("Promoted upstream proof/reference snapshot lane:")
    for section in ("raw", "derived"):
        for row in manifest[section]:
            print(f" - {row['source']} -> {row['snapshot']}")
    print(f"Manifest: {MANIFEST_PATH}")


if __name__ == "__main__":
    main()

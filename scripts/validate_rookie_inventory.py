#!/usr/bin/env python3
"""Validate rookie data inventory integrity.

Checks that every manifest row points to a real file, every file in rookie
data directories has a matching manifest row, verified rows have hashes,
and gold-layer artifacts are verified.

Usage:
    python scripts/validate_rookie_inventory.py

Exit codes:
    0 — all checks passed
    1 — one or more checks failed
"""

import csv
import hashlib
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST_PATH = os.path.join(REPO_ROOT, "data", "rookies_manifest.csv")

ROOKIE_DIRS = [
    os.path.join(REPO_ROOT, "data", "raw", "rookies"),
    os.path.join(REPO_ROOT, "data", "silver", "rookies"),
    os.path.join(REPO_ROOT, "data", "gold", "rookies"),
]

GOLD_DIR = os.path.join(REPO_ROOT, "data", "gold", "rookies")

# Files that are allowed in rookie dirs without manifest entries.
IGNORED_FILES = {"README.md", ".gitkeep", "IMPORT_BLOCKED.md"}

REQUIRED_FIELDS = [
    "artifact_path",
    "source_repo",
    "source_path",
    "season",
    "purpose",
    "classification",
    "role",
    "verified",
    "imported_at_utc",
]


def _sha256(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _collect_rookie_files() -> set[str]:
    """Return set of relative paths (from repo root) for all data files in rookie dirs."""
    files: set[str] = set()
    for root_dir in ROOKIE_DIRS:
        if not os.path.isdir(root_dir):
            continue
        for dirpath, _, filenames in os.walk(root_dir):
            for fname in filenames:
                if fname in IGNORED_FILES:
                    continue
                full = os.path.join(dirpath, fname)
                rel = os.path.relpath(full, REPO_ROOT)
                files.add(rel)
    return files


def _load_manifest() -> list[dict[str, str]]:
    if not os.path.isfile(MANIFEST_PATH):
        return []
    with open(MANIFEST_PATH, newline="") as f:
        reader = csv.DictReader(f)
        return [row for row in reader if any(v.strip() for v in row.values())]


def validate() -> list[str]:
    errors: list[str] = []

    # Load manifest
    rows = _load_manifest()
    manifest_paths: set[str] = set()

    for i, row in enumerate(rows, start=2):  # line 1 is header
        line = f"manifest line {i}"

        # Check required fields are present and non-empty
        for field in REQUIRED_FIELDS:
            val = row.get(field, "").strip()
            if not val:
                errors.append(f"{line}: missing required field '{field}'")

        artifact_path = row.get("artifact_path", "").strip()
        if not artifact_path:
            continue

        manifest_paths.add(artifact_path)

        # Check file exists
        full_path = os.path.join(REPO_ROOT, artifact_path)
        if not os.path.isfile(full_path):
            errors.append(f"{line}: artifact_path '{artifact_path}' does not exist on disk")
            continue

        verified = row.get("verified", "").strip().lower()
        sha256 = row.get("sha256", "").strip()

        # Verified rows must have a hash
        if verified == "true" and not sha256:
            errors.append(f"{line}: verified=true but sha256 is empty for '{artifact_path}'")

        # If hash is present, verify it matches
        if verified == "true" and sha256:
            actual = _sha256(full_path)
            if actual != sha256:
                errors.append(
                    f"{line}: sha256 mismatch for '{artifact_path}': "
                    f"manifest={sha256}, actual={actual}"
                )

        # Gold-layer artifacts must be verified
        if artifact_path.startswith("data/gold/rookies/") and verified != "true":
            errors.append(
                f"{line}: gold-layer artifact '{artifact_path}' must have verified=true"
            )

    # Check for orphan files (files on disk without manifest entry)
    on_disk = _collect_rookie_files()
    orphans = on_disk - manifest_paths
    for orphan in sorted(orphans):
        errors.append(f"orphan file: '{orphan}' exists on disk but has no manifest entry")

    # Check for manifest rows pointing at non-rookie paths
    for path in manifest_paths:
        is_rookie = any(
            path.startswith(os.path.relpath(d, REPO_ROOT) + "/")
            for d in ROOKIE_DIRS
        )
        if not is_rookie:
            errors.append(
                f"manifest entry '{path}' is not under a recognized rookie data directory"
            )

    return errors


def main() -> None:
    print("Validating rookie data inventory...")
    print(f"  Manifest: {os.path.relpath(MANIFEST_PATH, REPO_ROOT)}")
    print(f"  Rookie dirs: {', '.join(os.path.relpath(d, REPO_ROOT) for d in ROOKIE_DIRS)}")
    print()

    errors = validate()

    if not errors:
        # Also report if inventory is empty (informational, not an error)
        rows = _load_manifest()
        files = _collect_rookie_files()
        if not rows and not files:
            print("OK — manifest and rookie directories are both empty (no artifacts imported yet)")
        else:
            print(f"OK — {len(rows)} manifest row(s), {len(files)} file(s) on disk, all checks passed")
        sys.exit(0)
    else:
        print(f"FAILED — {len(errors)} error(s) found:\n")
        for err in errors:
            print(f"  - {err}")
        print()
        sys.exit(1)


if __name__ == "__main__":
    main()

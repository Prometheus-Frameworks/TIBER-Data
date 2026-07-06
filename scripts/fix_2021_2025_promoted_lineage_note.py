"""One-off remediation for a Codex review finding on PR #207 (TIBER-Data #206).

The `prior_promoted_artifact.note` field written by
scripts/promote_player_season_coverage_v0_2021_2025.py originally told a reader that the
prior (#192-era, 2022-2025-only) promoted bytes were "reconstructible by running
scripts/promote_player_season_coverage_v0.py against the unchanged, still-pinned 2022-2025
candidate." That is true only in isolation: that script writes to the SAME
exports/promoted/nfl/player_season_coverage_v0.json / MANIFEST path this repo now uses for
the 2021-2025 promotion, so following that note against a live, post-#206 checkout would
silently overwrite the current governed artifact with the stale 2022-2025-only content.

The note text in the source script has already been corrected to warn against this and to
point at safe alternatives (git history, or a scratch output redirect). This script applies
that corrected note to the ALREADY-promoted, already-committed live artifact.

This is a pure textual correction, not a re-promotion: it calls the exact same
build_promoted_payload used by TIBER-Data#206's real promotion, with the exact same inputs
(the pinned merged candidate, the pinned prior sha), so the only possible difference between
the previous committed bytes and this script's output is the corrected note string. This
script asserts that explicitly before writing anything, and fails closed if any other field
differs.

Usage: python scripts/fix_2021_2025_promoted_lineage_note.py
"""

from __future__ import annotations

import hashlib
import json
import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


class RemediationError(SystemExit):
    pass


def _load_module(name: str, relpath: str):
    module_path = REPO_ROOT / relpath
    spec = spec_from_file_location(name, module_path)
    assert spec is not None and spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    promote_module = _load_module(
        "promote_player_season_coverage_v0_2021_2025", "scripts/promote_player_season_coverage_v0_2021_2025.py"
    )
    validator_module = _load_module("validate_player_season_coverage_v0", "scripts/validate_player_season_coverage_v0.py")

    if not promote_module.PROMOTED_PATH.exists():
        raise RemediationError(f"{promote_module.PROMOTED_PATH} does not exist; nothing to fix.")

    current_bytes = promote_module.PROMOTED_PATH.read_bytes()
    current_payload = json.loads(current_bytes.decode("utf-8"))
    if current_payload.get("promotion_review") != "TIBER-Data#202":
        raise RemediationError(
            "The committed promoted artifact is not at the TIBER-Data#202/#206 lineage point "
            "this remediation assumes; refusing to touch it."
        )

    candidate_raw = promote_module.CANDIDATE_PATH.read_bytes()
    candidate_sha256 = hashlib.sha256(candidate_raw).hexdigest()
    candidate = json.loads(candidate_raw.decode("utf-8"))

    corrected_payload_raw = promote_module.build_promoted_payload(
        candidate,
        candidate_sha256,
        promote_module.PINNED_CANDIDATE_SHA256,
        validator_module,
        promote_module.PRIOR_PROMOTED_SHA256,
    )
    # Round-trip through JSON so dict key types (e.g. counts.by_season) match the
    # as-loaded-from-disk shape of current_payload; otherwise int-vs-string season keys
    # would look like a spurious diff below even though the serialized bytes are identical.
    corrected_payload = json.loads(json.dumps(corrected_payload_raw, indent=1) + "\n")

    # Fail-closed proof this is a pure textual correction: every field except the note
    # string (and the manifest sha it feeds into) must be byte-for-byte unchanged.
    only_expected_diff_key = ("prior_promoted_artifact", "note")
    for key in set(current_payload) | set(corrected_payload):
        if key == only_expected_diff_key[0]:
            current_sub = dict(current_payload.get(key, {}))
            corrected_sub = dict(corrected_payload.get(key, {}))
            current_sub.pop("note", None)
            corrected_sub.pop("note", None)
            if current_sub != corrected_sub:
                raise RemediationError(
                    f"Unexpected non-note difference inside '{key}': {current_sub} != {corrected_sub}. "
                    "Refusing to write; this remediation must only change the note text."
                )
            continue
        if current_payload.get(key) != corrected_payload.get(key):
            raise RemediationError(
                f"Unexpected difference outside the note field, in '{key}'. Refusing to write; "
                "this remediation must only change the prior_promoted_artifact.note text."
            )

    # Write from the raw in-memory payload (matching exactly how the real promotion script
    # serializes it), not the JSON-round-tripped copy used only for the diff check above.
    corrected_bytes = (json.dumps(corrected_payload_raw, indent=1) + "\n").encode("utf-8")
    if corrected_bytes == current_bytes:
        print("No change needed: committed artifact already has the corrected note.")
        return 0

    promote_module.PROMOTED_PATH.write_bytes(corrected_bytes)

    manifest = {k: v for k, v in corrected_payload_raw.items() if k != "records"}
    manifest["promoted_artifact_path"] = promote_module.PROMOTED_PATH.relative_to(REPO_ROOT).as_posix()
    manifest["promoted_artifact_sha256"] = hashlib.sha256(corrected_bytes).hexdigest()
    promote_module.MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print(f"Corrected prior_promoted_artifact.note in {promote_module.PROMOTED_PATH}")
    print(f"New promoted artifact sha256: {manifest['promoted_artifact_sha256']}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

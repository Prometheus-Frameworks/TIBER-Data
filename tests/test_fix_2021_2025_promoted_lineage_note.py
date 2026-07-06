"""Tests for the Codex-review remediation (PR #207): fixes the prior_promoted_artifact.note
field's dangerous suggestion to run scripts/promote_player_season_coverage_v0.py against a
live post-#206 checkout (which would overwrite the current governed artifact)."""

import json
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PROMOTED_PATH = REPO_ROOT / "exports/promoted/nfl/player_season_coverage_v0.json"


def _load_module():
    module_path = REPO_ROOT / "scripts" / "fix_2021_2025_promoted_lineage_note.py"
    spec = spec_from_file_location("fix_2021_2025_promoted_lineage_note", module_path)
    assert spec is not None and spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_module_promote():
    module_path = REPO_ROOT / "scripts" / "promote_player_season_coverage_v0_2021_2025.py"
    spec = spec_from_file_location("promote_player_season_coverage_v0_2021_2025", module_path)
    assert spec is not None and spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_note_generation_no_longer_recommends_running_original_script_in_place():
    """Checks the actual generated note value (via build_promoted_payload), not raw source
    text -- inspect.getsource() would return the source's adjacent-string-literal form
    (split across quoted lines), not the runtime-concatenated string this test needs."""
    promote_module = _load_module_promote()
    validator_module = _load_validator_module()
    candidate = _minimal_candidate()
    sha = "a" * 64
    payload = promote_module.build_promoted_payload(candidate, sha, sha, validator_module, promote_module.PRIOR_PROMOTED_SHA256)
    note = payload["prior_promoted_artifact"]["note"]
    assert "WARNING: do NOT run scripts/promote_player_season_coverage_v0.py against this live checkout" in note
    assert "silently overwrite" in note


def _load_validator_module():
    module_path = REPO_ROOT / "scripts" / "validate_player_season_coverage_v0.py"
    spec = spec_from_file_location("validate_player_season_coverage_v0", module_path)
    assert spec is not None and spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _minimal_candidate() -> dict:
    return {
        "artifact_id": "player_season_coverage_2021_2025.source_backed",
        "status": "candidate_evidence_artifact_not_promoted",
        "generated_at": "2026-07-06T00:00:00Z",
        "seasons": [2021],
        "season_type_scope": ["REG"],
        "row_grain": "player_id + season + season_type",
        "records": [
            {
                "player_id": "00-1",
                "player_name": "Test Player",
                "position": "QB",
                "identity_confidence": "source_verified",
                "season": 2021,
                "season_type": "REG",
                "generated_at": "2026-07-06T00:00:00Z",
                "source_refs": [
                    {
                        "source_name": "nflreadpy.load_player_stats(summary_level='reg')",
                        "observed_at": "2026-07-06T00:00:00Z",
                        "confidence": "source_verified",
                    }
                ],
                "teams": ["KC"],
                "primary_team": "KC",
                "weeks_observed": 17,
                "coverage_status": "full_season",
                "coverage_notes": "17 of up to 18 REG week numbers observed.",
                "missing_fields": [],
            }
        ],
    }


def test_committed_promoted_artifact_note_carries_the_warning():
    if not PROMOTED_PATH.exists():
        import pytest

        pytest.skip("promoted artifact not present in this environment")
    payload = json.loads(PROMOTED_PATH.read_text(encoding="utf-8"))
    if payload.get("promotion_review") != "TIBER-Data#202":
        import pytest

        pytest.skip("promoted artifact has not advanced to the #202/#206 lineage point this test checks")
    note = payload["prior_promoted_artifact"]["note"]
    assert "WARNING: do NOT run scripts/promote_player_season_coverage_v0.py against this live checkout" in note
    assert "silently overwrite" in note


def test_fix_script_is_idempotent(capsys):
    """Idempotency: once applied, running the remediation again must change nothing."""
    if not PROMOTED_PATH.exists():
        import pytest

        pytest.skip("promoted artifact not present in this environment")
    payload = json.loads(PROMOTED_PATH.read_text(encoding="utf-8"))
    if payload.get("promotion_review") != "TIBER-Data#202":
        import pytest

        pytest.skip("promoted artifact has not advanced to the #202/#206 lineage point this test checks")

    module = _load_module()
    before = PROMOTED_PATH.read_bytes()
    module.main()
    after = PROMOTED_PATH.read_bytes()
    assert before == after
    captured = capsys.readouterr()
    assert "No change needed" in captured.out

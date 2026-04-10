from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import promote_forge_weekly_upstream_proof_snapshot as promote


def test_promote_snapshot_requires_all_source_artifacts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    raw_source = (tmp_path / "missing.raw.json",)
    derived_source = (tmp_path / "missing.derived.json",)

    monkeypatch.setattr(promote, "RAW_SOURCE_PATHS", raw_source)
    monkeypatch.setattr(promote, "DERIVED_SOURCE_PATHS", derived_source)

    with pytest.raises(FileNotFoundError):
        promote.promote_snapshot(captured_at="2026-04-10T00:00:00Z")


def test_promote_snapshot_copies_to_distinct_snapshot_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    raw_source = tmp_path / "weekly_player_stats.upstream_public_2024_w01_w03_8player_scaffold.json"
    team_source = tmp_path / "team_week_context.upstream_public_2024_w01_w03_2team_scaffold.json"
    w1_source = tmp_path / "forge_weekly_player_input_2024_w01.skill_upstream_public_w01_w03_8player_scaffold.derived.json"
    w2_source = tmp_path / "forge_weekly_player_input_2024_w02.skill_upstream_public_w01_w03_8player_scaffold.derived.json"
    w3_source = tmp_path / "forge_weekly_player_input_2024_w03.skill_upstream_public_w01_w03_8player_scaffold.derived.json"

    for path in (raw_source, team_source, w1_source, w2_source, w3_source):
        path.write_text('{"ok": true}\n', encoding="utf-8")

    raw_snapshot = tmp_path / "weekly_player_stats.upstream_public_2024_w01_w03_8player_scaffold.proof_reference_snapshot.json"
    team_snapshot = tmp_path / "team_week_context.upstream_public_2024_w01_w03_2team_scaffold.proof_reference_snapshot.json"
    w1_snapshot = tmp_path / "forge_weekly_player_input_2024_w01.skill_upstream_public_w01_w03_8player_scaffold.proof_reference_snapshot.derived.json"
    w2_snapshot = tmp_path / "forge_weekly_player_input_2024_w02.skill_upstream_public_w01_w03_8player_scaffold.proof_reference_snapshot.derived.json"
    w3_snapshot = tmp_path / "forge_weekly_player_input_2024_w03.skill_upstream_public_w01_w03_8player_scaffold.proof_reference_snapshot.derived.json"
    manifest_path = tmp_path / "manifest.json"

    monkeypatch.setattr(promote, "RAW_SOURCE_PATHS", (raw_source, team_source))
    monkeypatch.setattr(promote, "DERIVED_SOURCE_PATHS", (w1_source, w2_source, w3_source))
    monkeypatch.setattr(promote, "RAW_SNAPSHOT_PATHS", (raw_snapshot, team_snapshot))
    monkeypatch.setattr(promote, "DERIVED_SNAPSHOT_PATHS", (w1_snapshot, w2_snapshot, w3_snapshot))
    monkeypatch.setattr(promote, "MANIFEST_PATH", manifest_path)

    manifest = promote.promote_snapshot(captured_at="2026-04-10T00:00:00Z")

    assert raw_snapshot.exists()
    assert team_snapshot.exists()
    assert w1_snapshot.exists()
    assert w2_snapshot.exists()
    assert w3_snapshot.exists()
    assert manifest_path.exists()

    loaded = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert loaded["captured_at"] == "2026-04-10T00:00:00Z"
    assert all("proof_reference_snapshot" in row["snapshot"] for row in loaded["raw"])
    assert all("proof_reference_snapshot" in row["snapshot"] for row in loaded["derived"])
    assert all("scaffold.derived.json" in row["source"] for row in loaded["derived"])

    assert manifest["snapshot_id"] == "forge_weekly_upstream_public_2024_w01_w03_atl_det_proof_reference"

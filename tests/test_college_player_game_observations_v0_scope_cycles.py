"""Regressions for PR #275 review threads (Data #265); all data synthetic/in memory."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from src.contracts.college_player_game_observations_v0 import validate

FIXTURE = Path(__file__).parent / "fixtures/college_observations/player_games.synthetic.json"
T7 = "2026-09-07T12:00:00Z"
T8 = "2026-09-08T12:00:00Z"


@pytest.fixture
def batch():
    return json.loads(FIXTURE.read_text())


def codes(batch):
    return {f["code"] for f in validate(batch)}


def unresolved_row(batch, oid, rev, related):
    row = copy.deepcopy(batch["observations"][1])
    ref = "snapshot-" + rev
    snap = copy.deepcopy(batch["evidence"]["snapshot-r1"])
    snap.update(locator="synthetic:" + rev, known_at=T8, source_order_claim=None)
    snap["scope"]["source_revision_id"] = rev
    batch["evidence"][ref] = snap
    row.update(observation_id=oid, source_revision_id=rev, source_snapshot_ref=ref, retrieved_at=T8)
    row["source_relationship"] = {
        "status": "unresolved",
        "related_observation_id": related,
        "basis": "none",
        "evidence_refs": [],
    }
    row["source_updated_at"].update(
        value=None, origin="not_supplied_by_source", evidence_refs=[ref]
    )
    row["game"]["status_evidence_refs"] = [ref]
    for group in row["observed"].values():
        for metric in group.values():
            metric["evidence_refs"] = [ref] if metric["evidence_refs"] else []
    batch["observations"].append(row)
    return row


def test_expectation_evidence_binds_to_declared_game_scope(batch):
    game_scope = batch["coverage"]["game_scope"]
    item = copy.deepcopy(batch["evidence"]["scope"])
    item["locator"] = "synthetic:expectation-other-game"
    item["scope"].update(season=2099, source_game_id="synthetic-unrelated-game")
    batch["evidence"]["expectation"] = item
    game_scope["expectation_evidence_refs"] = ["expectation"]
    assert {"EVIDENCE_SCOPE", "GAME_EXPECTATION"} <= codes(batch)
    # Unrelated evidence cannot back a complete claim either.
    batch["coverage"]["population_status"] = "complete"
    game_scope["expected_game_ids"] = copy.deepcopy(game_scope["observed_game_ids"])
    assert {"EVIDENCE_SCOPE", "GAME_EXPECTATION"} <= codes(batch)
    # Game-scoped evidence is accepted only for exactly the games it names.
    item["scope"].update(season=2026, source_game_id="synthetic-game-1")
    game_scope["expected_game_ids"] = [{"season": 2026, "source_game_id": "synthetic-game-1"}]
    game_scope["observed_game_ids"] = copy.deepcopy(game_scope["expected_game_ids"])
    batch["observations"] = [
        r for r in batch["observations"] if r["game"]["source_game_id"] == "synthetic-game-1"
    ]
    batch["attributions"] = []
    batch["retrieval_receipts"] = [
        r
        for r in batch["retrieval_receipts"]
        if r["source_observation_id"] in {o["observation_id"] for o in batch["observations"]}
    ]
    assert not {"EVIDENCE_SCOPE", "GAME_EXPECTATION"} & codes(batch)
    # Independently established zero games cannot rest on single-game evidence.
    game_scope["expected_game_ids"] = []
    assert "EVIDENCE_SCOPE" in codes(batch)


def test_season_scoped_expectation_evidence_covers_its_season(batch):
    game_scope = batch["coverage"]["game_scope"]
    for season in (2025, 2026):
        item = copy.deepcopy(batch["evidence"]["scope"])
        item["locator"] = f"synthetic:expectation-season-{season}"
        item["scope"]["season"] = season
        batch["evidence"][f"expectation-{season}"] = item
    game_scope["expectation_evidence_refs"] = ["expectation-2025", "expectation-2026"]
    assert validate(batch) == []
    # The 2026 season ref alone leaves the expected 2025 game unbacked.
    game_scope["expectation_evidence_refs"] = ["expectation-2026"]
    findings = [f for f in validate(batch) if f["code"] == "GAME_EXPECTATION"]
    assert [f["message"] for f in findings] == [
        "No expectation evidence in scope for 2025/synthetic-game-prior."
    ]


def test_source_relationship_cycles_fail_validation(batch):
    assert validate(batch) == []
    row = unresolved_row(batch, "synthetic-related-a", "synthetic-ra", "synthetic-related-a")
    assert "LINEAGE_CYCLE" in codes(batch)
    unresolved_row(batch, "synthetic-related-b", "synthetic-rb", "synthetic-related-a")
    row["source_relationship"]["related_observation_id"] = "synthetic-related-b"
    assert "LINEAGE_CYCLE" in codes(batch)
    # Control: a chain that terminates at the retained initial row is acyclic.
    row["source_relationship"]["related_observation_id"] = batch["observations"][1][
        "observation_id"
    ]
    assert "LINEAGE_CYCLE" not in codes(batch)


@pytest.mark.parametrize(
    "change",
    [
        {"name": "Jordan Matthews"},
        {"canonical_college_player_id": "college-player-4471"},
        {"attribution_id": "attr-4471"},
        {"supersedes_attribution_id": "attr-4470"},
    ],
)
def test_synthetic_attribution_keeps_synthetic_identity(batch, change):
    row = batch["observations"][4]
    item = copy.deepcopy(batch["evidence"]["identity"])
    item.update(locator="synthetic:identity-7", known_at=T7)
    batch["evidence"]["identity-7"] = item
    state = copy.deepcopy(row["identity"])
    state.update(
        status="resolved",
        canonical_college_player_id="synthetic-college-a",
        aggregation_status="eligible",
        evidence_refs=["identity-7"],
    )
    batch["attributions"].append(
        {
            "attribution_id": "synthetic-attr-0",
            "source_observation_id": row["observation_id"],
            "supersedes_attribution_id": None,
            "recorded_at": T7,
            "state": state,
        }
    )
    assert validate(batch) == []
    event = batch["attributions"][-1]
    (event if next(iter(change)) in event else state).update(change)
    assert "SYNTHETIC_IDENTITY" in codes(batch)

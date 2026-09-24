"""Independent finding reproductions for R1–R7; all data synthetic/in memory."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from src.contracts.college_player_game_observations_v0 import corrected_leaf_ids, validate

FIXTURE = Path(__file__).parent / "fixtures/college_observations/player_games.synthetic.json"


@pytest.fixture
def batch():
    return json.loads(FIXTURE.read_text())


def codes(batch):
    return {f["code"] for f in validate(batch)}


def snapshot(batch, label, rev, known="2026-09-08T12:00:00Z"):
    e = copy.deepcopy(batch["evidence"]["snapshot-r1"])
    e.update(locator="synthetic:" + label, known_at=known, source_order_claim=None)
    e["scope"]["source_revision_id"] = rev
    batch["evidence"][label] = e


def append_competitor(batch, status="unresolved", source_time=None):
    old = batch["observations"][1]
    r = copy.deepcopy(old)
    r.update(
        observation_id="synthetic-competing",
        source_revision_id="synthetic-different",
        source_snapshot_ref="snapshot-different",
        retrieved_at="2026-09-08T12:00:00Z",
        revision_reason=None,
        supersedes=None,
    )
    r["source_relationship"] = {
        "status": status,
        "related_observation_id": old["observation_id"],
        "basis": "none",
        "evidence_refs": [],
    }
    r["source_updated_at"].update(
        value=source_time,
        origin="source_supplied" if source_time else "not_supplied_by_source",
        evidence_refs=["snapshot-different"],
    )
    r["game"]["status_evidence_refs"] = ["snapshot-different"]
    for group in r["observed"].values():
        for m in group.values():
            m["evidence_refs"] = ["snapshot-different"]
    batch["observations"].append(r)
    snapshot(batch, "snapshot-different", "synthetic-different")
    return r


def test_r1_supported_correction_and_repeat_receipt(batch):
    assert validate(batch) == []
    assert batch["observations"][-1]["observation_id"] in corrected_leaf_ids(batch)
    batch["retrieval_receipts"].append(
        {
            "receipt_id": "synthetic-repeat",
            "source_observation_id": "synthetic-observation-qb",
            "retrieved_at": "2026-09-07T12:00:00Z",
            "source_snapshot_ref": "snapshot-r1",
        }
    )
    assert validate(batch) == []
    assert batch["observations"][0]["retrieved_at"] == "2026-09-06T12:00:00Z"
    batch["retrieval_receipts"][0]["source_snapshot_ref"] = "snapshot-r2"
    assert "RECEIPT_SOURCE" in codes(batch)


def test_r1_older_material_cannot_be_supported_correction(batch):
    r = batch["observations"][-1]
    r["source_updated_at"]["value"] = "2026-09-05T11:00:00Z"
    assert "SOURCE_ORDER_CONFLICT" in codes(batch)
    r["source_relationship"].update(status="older_discovered_later", basis="none", evidence_refs=[])
    r["supersedes"] = None
    r["revision_reason"] = None
    assert validate(batch) == []
    with pytest.raises(ValueError, match="unresolved"):
        corrected_leaf_ids(batch)


def test_r1_unordered_source_with_missing_clock_or_digest(batch):
    r = append_competitor(batch)
    assert validate(batch) == []
    with pytest.raises(ValueError, match="unresolved"):
        corrected_leaf_ids(batch)
    r["source_relationship"].update(
        status="established_supersession",
        basis="provider_explicit_correction",
        evidence_refs=["snapshot-different"],
    )
    r.update(supersedes="synthetic-observation-rb", revision_reason="SYNTHETIC claimed")
    assert "RELATIONSHIP_BASIS" in codes(batch)
    # Different retained bytes identify content; they do not authorize ordering.
    r["source_revision_id"] = "sha256:" + "a" * 64
    r["revision_origin"] = "retained_snapshot_digest"
    batch["evidence"]["snapshot-different"]["scope"]["source_revision_id"] = r["source_revision_id"]
    assert "RELATIONSHIP_BASIS" in codes(batch)


def test_r1_source_revision_without_clock_but_explicit_provider_evidence(batch):
    r = batch["observations"][-1]
    r["source_updated_at"].update(value=None, origin="not_supplied_by_source")
    assert validate(batch) == []  # independently recorded source correction claim
    batch["evidence"]["snapshot-r2"]["source_order_claim"] = None
    assert "RELATIONSHIP_BASIS" in codes(batch)


def test_r1_retrieval_order_alone_never_authorizes_supersession(batch):
    r = append_competitor(
        batch, status="older_discovered_later", source_time="2026-09-05T10:00:00Z"
    )
    assert validate(batch) == []
    with pytest.raises(ValueError):
        corrected_leaf_ids(batch)
    assert r["retrieved_at"] > batch["observations"][1]["retrieved_at"]


def identity_evidence(batch, label, known, source_revision_id=None):
    e = copy.deepcopy(batch["evidence"]["identity"])
    e.update(locator="synthetic:" + label, known_at=known, alias_claim=None)
    e["scope"]["source_revision_id"] = source_revision_id
    batch["evidence"][label] = e


def test_r2_attribution_becomes_resolved_without_source_revision(batch):
    row = batch["observations"][4]
    identity_evidence(batch, "identity-later", "2026-09-08T12:00:00Z")
    state = copy.deepcopy(row["identity"])
    state.update(
        status="resolved",
        canonical_college_player_id="synthetic-college-resolved",
        aggregation_status="eligible",
        evidence_refs=["identity-later"],
    )
    batch["attributions"].append(
        {
            "attribution_id": "synthetic-attr-1",
            "source_observation_id": row["observation_id"],
            "supersedes_attribution_id": None,
            "recorded_at": "2026-09-08T12:00:00Z",
            "state": state,
        }
    )
    original = copy.deepcopy(row)
    assert validate(batch) == []
    assert row == original
    assert row["source_revision_id"] == "synthetic-r1"
    assert row["identity"]["status"] == "unresolved"
    assert batch["attributions"][0]["recorded_at"] > "2026-09-07T00:00:00Z"
    assert state["status"] == "resolved"
    state["evidence_refs"] = ["identity"]
    assert validate(batch) == []  # independently earlier evidence can be cited later
    state["evidence_refs"] = ["identity-later"]
    batch["attributions"][0]["recorded_at"] = "2026-09-07T00:00:00Z"
    assert "EVIDENCE_FUTURE" in codes(batch)


def test_r3_later_or_wrong_revision_evidence_rejected(batch):
    batch["observations"][0]["observed"]["passing"]["yards"]["evidence_refs"] = ["snapshot-r2"]
    assert {"EVIDENCE_FUTURE", "EVIDENCE_SCOPE", "RAW_EVIDENCE_BINDING"} & codes(batch)
    batch["observations"][0]["observed"]["passing"]["yards"]["evidence_refs"] = ["snapshot-r1"]
    assert validate(batch) == []
    batch["observations"][0]["source_snapshot_ref"] = "snapshot-r2"
    assert "EVIDENCE_REVISION" in codes(batch)
    batch["observations"][0]["source_snapshot_ref"] = "snapshot-r1"
    batch["evidence"]["identity"]["known_at"] = "2026-09-08T00:00:00Z"
    assert "EVIDENCE_FUTURE" in codes(batch)


def test_r4_resolved_alias_quarantined_and_reviewed(batch):
    wr = batch["observations"][2]
    alias = copy.deepcopy(wr)
    alias.update(observation_id="synthetic-wr-alias", retrieved_at="2026-09-08T12:00:00Z")
    alias["identity"]["source_player_id"] = "synthetic-player-wr-alias"
    alias["identity"]["aggregation_status"] = "eligible"
    batch["observations"].append(alias)
    assert "ALIAS_CONFLICT" in codes(batch)
    reviewed = copy.deepcopy(batch)
    alias["identity"].update(aggregation_status="blocked_alias_conflict")
    identity_evidence(batch, "identity-conflict", "2026-09-08T12:00:00Z")
    blocked = copy.deepcopy(wr["identity"])
    blocked.update(aggregation_status="blocked_alias_conflict", evidence_refs=["identity-conflict"])
    batch["attributions"].append(
        {
            "attribution_id": "synthetic-alias-quarantine",
            "source_observation_id": wr["observation_id"],
            "supersedes_attribution_id": None,
            "recorded_at": "2026-09-08T12:00:00Z",
            "state": blocked,
        }
    )
    assert validate(batch) == []  # source rows preserved, canonical aggregation blocked
    # Reviewed representative: explicit identity evidence supports exclusion.
    alias = reviewed["observations"][-1]
    alias["identity"].update(
        aggregation_status="excluded_reconciled_alias",
        alias_of_observation_id=wr["observation_id"],
        evidence_refs=["identity-alias"],
    )
    identity_evidence(reviewed, "identity-alias", "2026-09-08T12:00:00Z")
    reviewed["evidence"]["identity-alias"]["scope"].update(
        season=2026, source_game_id="synthetic-game-1", source_player_id="synthetic-player-wr-alias"
    )
    reviewed["evidence"]["identity-alias"]["alias_claim"] = {
        "alias_source_player_id": "synthetic-player-wr-alias",
        "alias_observation_id": "synthetic-wr-alias",
        "representative_observation_id": wr["observation_id"],
        "representative_source_player_id": "synthetic-player-wr",
        "season": 2026,
        "source_game_id": "synthetic-game-1",
        "canonical_college_player_id": "synthetic-college-wr",
    }
    assert validate(reviewed) == []
    reviewed["evidence"]["identity-alias"]["alias_claim"]["representative_source_player_id"] = (
        "synthetic-other"
    )
    assert "ALIAS_EVIDENCE" in codes(reviewed)


def test_r4_same_name_distinct_players_and_transfer_safe(batch):
    assert (
        batch["observations"][4]["identity"]["name"] == batch["observations"][5]["identity"]["name"]
    )
    assert (
        batch["observations"][4]["identity"]["source_player_id"]
        != batch["observations"][5]["identity"]["source_player_id"]
    )
    old, new = batch["observations"][6:8]
    assert (
        old["identity"]["canonical_college_player_id"]
        == new["identity"]["canonical_college_player_id"]
    )
    assert old["game"]["team"] != new["game"]["team"]
    assert validate(batch) == []


def test_r5_not_applicable_requires_field_record_rule_not_position(batch):
    row = batch["observations"][0]
    m = row["observed"]["receiving"]["targets"]
    m["availability"] = "not_applicable"
    assert "APPLICABILITY" in codes(batch)
    snapshot(batch, "snapshot-special", "synthetic-r1", known="2026-09-06T12:00:00Z")
    batch["evidence"]["snapshot-special"]["scope"]["source_record_type"] = (
        "synthetic-receiving-only-record"
    )
    row["source_record_type"] = "synthetic-receiving-only-record"
    row["source_snapshot_ref"] = "snapshot-special"
    row["game"]["status_evidence_refs"] = ["snapshot-special"]
    row["source_updated_at"]["evidence_refs"] = ["snapshot-special"]
    for group in row["observed"].values():
        for cell in group.values():
            cell["evidence_refs"] = ["snapshot-special"]
    basis = {
        "rule_id": "field_not_defined_for_source_record_type",
        "source_record_type": "synthetic-receiving-only-record",
        "evidence_refs": ["mapping", "snapshot-special"],
    }
    m["applicability_basis"] = basis
    assert "APPLICABILITY" in codes(batch)
    batch["evidence"]["mapping"]["applicability_rules"].append(
        {
            "source_record_type": "synthetic-receiving-only-record",
            "field": "receiving.targets",
            "rule_id": basis["rule_id"],
        }
    )
    assert validate(batch) == []
    basis["source_record_type"] = "QB"
    assert "APPLICABILITY" in codes(batch)


def test_r5_trick_plays_allowed(batch):
    qb = batch["observations"][0]
    rb = batch["observations"][1]
    qb["observed"]["receiving"]["receptions"].update(value=1, availability="observed_value")
    rb["observed"]["passing"]["attempts"].update(value=1, availability="observed_value")
    rb["observed"]["passing"]["completions"].update(value=1, availability="observed_value")
    assert validate(batch) == []


def test_r6_reused_game_ids_across_seasons_are_distinct(batch):
    row = batch["observations"][6]
    row["game"]["source_game_id"] = "synthetic-game-2"
    scope = batch["coverage"]["game_scope"]
    scope["observed_game_ids"].remove({"season": 2025, "source_game_id": "synthetic-game-prior"})
    scope["expected_game_ids"].remove({"season": 2025, "source_game_id": "synthetic-game-prior"})
    scope["observed_game_ids"].append({"season": 2025, "source_game_id": "synthetic-game-2"})
    scope["expected_game_ids"].append({"season": 2025, "source_game_id": "synthetic-game-2"})
    assert validate(batch) == []
    scope["observed_game_ids"].remove({"season": 2025, "source_game_id": "synthetic-game-2"})
    assert "GAME_SCOPE" in codes(batch)


def test_r7_final_future_rejected_scheduled_allowed_and_postseason(batch):
    game = batch["observations"][2]["game"]
    game["date"] = "2035-09-05"
    assert "FINAL_EVENT_CHRONOLOGY" in codes(batch)
    game["status"] = "scheduled"
    assert validate(batch) == []
    game.update(status="final", date="2027-01-01")
    assert "FINAL_EVENT_CHRONOLOGY" in codes(batch)  # fixture known September 2026
    batch["observations"][2]["retrieved_at"] = "2027-01-02T12:00:00Z"
    batch["generated_at"] = "2027-01-03T12:00:00Z"
    assert validate(batch) == []  # postseason date can differ from season


def test_revisions_still_distinct_from_event_and_known_clocks(batch):
    old, new = batch["observations"][0], batch["observations"][-1]
    assert old["game"]["date"] == new["game"]["date"]
    assert old["source_revision_id"] != new["source_revision_id"]
    assert old["retrieved_at"] < new["retrieved_at"]
    assert validate(batch) == []


def test_r4_same_provider_player_source_correction_is_not_alias_conflict(batch):
    wr = batch["observations"][2]
    corrected = copy.deepcopy(wr)
    corrected.update(
        observation_id="synthetic-wr-corrected",
        source_revision_id="synthetic-r2",
        retrieved_at="2026-09-08T12:00:00Z",
        source_snapshot_ref="snapshot-r2",
        supersedes=wr["observation_id"],
        revision_reason="SYNTHETIC source correction",
        source_relationship={
            "status": "established_supersession",
            "related_observation_id": wr["observation_id"],
            "basis": "provider_explicit_correction",
            "evidence_refs": ["snapshot-r2"],
        },
    )
    corrected["source_updated_at"].update(
        value="2026-09-08T11:00:00Z", evidence_refs=["snapshot-r2"]
    )
    corrected["game"]["status_evidence_refs"] = ["snapshot-r2"]
    for group in corrected["observed"].values():
        for field in group.values():
            field["evidence_refs"] = ["snapshot-r2"]
    batch["observations"].append(corrected)
    assert validate(batch) == []
    assert corrected["observation_id"] in corrected_leaf_ids(batch)


def test_r4_excluded_alias_cannot_reference_future_representative(batch):
    wr = batch["observations"][2]
    alias = copy.deepcopy(wr)
    alias.update(observation_id="synthetic-alias-early", retrieved_at="2026-09-06T12:00:00Z")
    alias["identity"].update(
        source_player_id="synthetic-alias-source",
        aggregation_status="excluded_reconciled_alias",
        alias_of_observation_id="synthetic-future-representative",
        evidence_refs=["identity"],
    )
    future = copy.deepcopy(wr)
    future.update(
        observation_id="synthetic-future-representative", retrieved_at="2026-09-08T12:00:00Z"
    )
    future["identity"]["source_player_id"] = "synthetic-future-source"
    future["identity"]["aggregation_status"] = "blocked_alias_conflict"
    batch["observations"].extend([alias, future])
    assert "ALIAS_REFERENCE" in codes(batch)

"""Synthetic historical identity and revision intervals; no provider observations."""

import copy
import json
from pathlib import Path

import pytest

from src.contracts.college_player_game_observations_v0 import validate

FIXTURE = Path(__file__).parent / "fixtures/college_observations/player_games.synthetic.json"
T7 = "2026-09-07T12:00:00Z"
T8 = "2026-09-08T12:00:00Z"
T9 = "2026-09-09T09:00:00Z"


@pytest.fixture
def batch():
    return json.loads(FIXTURE.read_text())


def evidence(batch, label, known, kind="identity", claim=None):
    item = copy.deepcopy(batch["evidence"]["identity" if kind == "identity" else "snapshot-r1"])
    item.update(kind=kind, locator="synthetic:" + label, known_at=known, alias_claim=claim)
    if kind == "source_snapshot":
        item["scope"]["source_revision_id"] = "synthetic-r2"
        item["source_order_claim"] = {
            "older_revision_id": "synthetic-r1",
            "newer_revision_id": "synthetic-r2",
            "assertion": "explicit_correction",
        }
    batch["evidence"][label] = item


def attribute(batch, row, ident, label, time, parent=None):
    state = copy.deepcopy(row["identity"])
    state.update(**ident, evidence_refs=[label])
    aid = "synthetic-attr-" + str(len(batch["attributions"]))
    batch["attributions"].append(
        {
            "attribution_id": aid,
            "source_observation_id": row["observation_id"],
            "supersedes_attribution_id": parent,
            "recorded_at": time,
            "state": state,
        }
    )
    return aid


def codes(batch):
    return {f["code"] for f in validate(batch)}


def as_known(batch, oid, cutoff):
    row = next(r for r in batch["observations"] if r["observation_id"] == oid)
    states = [(row["retrieved_at"], row["identity"])]
    states += [
        (e["recorded_at"], e["state"])
        for e in batch["attributions"]
        if e["source_observation_id"] == oid
    ]
    return max((x for x in states if x[0] <= cutoff), key=lambda x: x[0])[1]


@pytest.mark.parametrize("initial", ["unresolved", "ambiguous"])
def test_valid_multistage_resolution_and_checkpoint(batch, initial):
    row = next(r for r in batch["observations"] if r["identity"]["status"] == initial)
    evidence(batch, "resolve-7", T7)
    aid = attribute(
        batch,
        row,
        {
            "status": "resolved",
            "canonical_college_player_id": "synthetic-college-a",
            "aggregation_status": "eligible",
        },
        "resolve-7",
        T7,
    )
    evidence(batch, "resolve-9", T9)
    attribute(
        batch,
        row,
        {
            "status": "resolved",
            "canonical_college_player_id": "synthetic-college-b",
            "aggregation_status": "eligible",
        },
        "resolve-9",
        T9,
        aid,
    )
    assert validate(batch) == []
    assert (
        as_known(batch, row["observation_id"], "2026-09-06T12:00:00Z")[
            "canonical_college_player_id"
        ]
        is None
    )
    assert (
        as_known(batch, row["observation_id"], T8)["canonical_college_player_id"]
        == "synthetic-college-a"
    )
    assert (
        as_known(batch, row["observation_id"], T9)["canonical_college_player_id"]
        == "synthetic-college-b"
    )


def test_invalid_intermediate_is_never_sanitized(batch):
    row = batch["observations"][4]
    evidence(batch, "identity-7", T7)
    bad = attribute(
        batch,
        row,
        {
            "status": "resolved",
            "canonical_college_player_id": None,
            "aggregation_status": "eligible",
        },
        "identity-7",
        T7,
    )
    evidence(batch, "identity-9", T9)
    attribute(
        batch,
        row,
        {
            "status": "resolved",
            "canonical_college_player_id": "synthetic-college-a",
            "aggregation_status": "eligible",
        },
        "identity-9",
        T9,
        bad,
    )
    assert "IDENTITY_STATUS" in codes(batch)
    assert any(f["path"] == "/attributions/0/state" for f in validate(batch))
    assert as_known(batch, row["observation_id"], T8)["canonical_college_player_id"] is None
    assert (
        as_known(batch, row["observation_id"], T9)["canonical_college_player_id"]
        == "synthetic-college-a"
    )
    batch["attributions"][0]["state"]["canonical_college_player_id"] = "synthetic-college-a"
    batch["attributions"][0]["state"]["evidence_refs"] = ["identity-9"]
    assert "EVIDENCE_FUTURE" in codes(batch)


def test_invalid_initial_is_never_sanitized(batch):
    row = batch["observations"][4]
    row["identity"]["canonical_college_player_id"] = "synthetic-college-a"
    evidence(batch, "identity-9", T9)
    attribute(
        batch, row, {"status": "resolved", "aggregation_status": "eligible"}, "identity-9", T9
    )
    assert "IDENTITY_STATUS" in codes(batch)
    assert as_known(batch, row["observation_id"], T8)["status"] == "unresolved"


def test_intermediate_alias_and_eligibility_cannot_be_sanitized(batch):
    row = batch["observations"][4]
    evidence(batch, "identity-7", T7)
    aid = attribute(
        batch,
        row,
        {
            "status": "resolved",
            "canonical_college_player_id": "synthetic-college-a",
            "aggregation_status": "excluded_reconciled_alias",
            "alias_of_observation_id": batch["observations"][2]["observation_id"],
        },
        "identity-7",
        T7,
    )
    evidence(batch, "identity-9", T9)
    attribute(
        batch,
        row,
        {
            "status": "resolved",
            "canonical_college_player_id": "synthetic-college-a",
            "aggregation_status": "eligible",
            "alias_of_observation_id": None,
        },
        "identity-9",
        T9,
        aid,
    )
    assert {"ALIAS_REFERENCE", "ALIAS_EVIDENCE"} <= codes(batch)
    assert any(f["path"] == "/attributions/0/state" for f in validate(batch))


def alias_claim(alias, rep):
    return {
        "alias_source_player_id": alias["identity"]["source_player_id"],
        "alias_observation_id": alias["observation_id"],
        "representative_source_player_id": rep["identity"]["source_player_id"],
        "representative_observation_id": rep["observation_id"],
        "season": alias["game"]["season"],
        "source_game_id": alias["game"]["source_game_id"],
        "canonical_college_player_id": alias["identity"]["canonical_college_player_id"],
    }


def reviewed_alias(batch):
    rep = batch["observations"][2]
    alias = copy.deepcopy(rep)
    alias.update(observation_id="synthetic-alias-r1", retrieved_at=T7)
    alias["identity"].update(
        source_player_id="synthetic-provider-alias",
        aggregation_status="excluded_reconciled_alias",
        alias_of_observation_id=rep["observation_id"],
        evidence_refs=["alias-7"],
    )
    evidence(batch, "alias-7", T7, claim=alias_claim(alias, rep))
    batch["observations"].append(alias)
    assert validate(batch) == []
    return rep, alias


def correct(batch, old, name):
    new = copy.deepcopy(old)
    new.update(
        observation_id=name,
        source_revision_id="synthetic-r2",
        retrieved_at=T8,
        supersedes=old["observation_id"],
        revision_reason="SYNTHETIC provider correction",
        source_snapshot_ref="snapshot-" + name,
    )
    new["source_relationship"] = {
        "status": "established_supersession",
        "related_observation_id": old["observation_id"],
        "basis": "provider_explicit_correction",
        "evidence_refs": ["snapshot-" + name],
    }
    new["source_updated_at"].update(
        value="2026-09-08T11:00:00Z", origin="source_supplied", evidence_refs=["snapshot-" + name]
    )
    new["game"]["status_evidence_refs"] = ["snapshot-" + name]
    for group in new["observed"].values():
        for metric in group.values():
            metric["evidence_refs"] = ["snapshot-" + name]
    new["identity"].update(
        aggregation_status="blocked_alias_conflict",
        alias_of_observation_id=None,
        evidence_refs=["identity"],
    )
    evidence(batch, "snapshot-" + name, T8, kind="source_snapshot")
    batch["observations"].append(new)
    return new


@pytest.mark.parametrize("correct_rep,correct_alias", [(True, False), (False, True), (True, True)])
def test_reviewed_alias_survives_source_corrections_and_requires_new_review(
    batch, correct_rep, correct_alias
):
    rep, alias = reviewed_alias(batch)
    before = copy.deepcopy(alias)
    rep2 = correct(batch, rep, "synthetic-representative-r2") if correct_rep else rep
    alias2 = correct(batch, alias, "synthetic-alias-r2") if correct_alias else alias
    assert validate(batch) == []
    assert alias == before
    assert (
        as_known(batch, alias["observation_id"], T7)["alias_of_observation_id"]
        == rep["observation_id"]
    )
    # The old decision is retained at its original cutoff, but does not confer
    # canonical eligibility on either corrected revision.
    assert rep2["identity"]["aggregation_status"] == (
        "blocked_alias_conflict" if correct_rep else "eligible"
    )
    assert alias2["identity"]["aggregation_status"] == (
        "blocked_alias_conflict" if correct_alias else "excluded_reconciled_alias"
    )
    evidence(batch, "representative-9", T9)
    attribute(batch, rep2, {"aggregation_status": "eligible"}, "representative-9", T9)
    evidence(batch, "alias-9", T9, claim=alias_claim(alias2, rep2))
    attribute(
        batch,
        alias2,
        {
            "aggregation_status": "excluded_reconciled_alias",
            "alias_of_observation_id": rep2["observation_id"],
        },
        "alias-9",
        T9,
    )
    assert validate(batch) == []
    assert (
        as_known(batch, alias["observation_id"], T7)["alias_of_observation_id"]
        == rep["observation_id"]
    )
    assert (
        as_known(batch, alias2["observation_id"], T9)["alias_of_observation_id"]
        == rep2["observation_id"]
    )
    assert len(batch["observations"]) == 9 + correct_rep + 1 + correct_alias


def test_later_distinct_canonical_identity_does_not_rewrite_alias(batch):
    rep, alias = reviewed_alias(batch)
    new_alias = correct(batch, alias, "synthetic-alias-r2")
    evidence(batch, "independent-9", T9)
    attribute(
        batch,
        new_alias,
        {
            "status": "resolved",
            "canonical_college_player_id": "synthetic-different-player",
            "aggregation_status": "eligible",
        },
        "independent-9",
        T9,
    )
    evidence(batch, "representative-distinct-9", T9)
    attribute(batch, rep, {"aggregation_status": "eligible"}, "representative-distinct-9", T9)
    assert validate(batch) == []
    assert alias["identity"]["alias_of_observation_id"] == rep["observation_id"]
    assert new_alias["identity"]["aggregation_status"] == "blocked_alias_conflict"


def test_historical_alias_evidence_cannot_switch_revision_binding(batch):
    rep, alias = reviewed_alias(batch)
    new_rep = correct(batch, rep, "synthetic-representative-r2")
    assert validate(batch) == []
    batch["evidence"]["alias-7"]["alias_claim"]["representative_observation_id"] = new_rep[
        "observation_id"
    ]
    assert "ALIAS_EVIDENCE" in codes(batch)


@pytest.mark.parametrize("reference", ["identity", "mapping", "snapshot-r1"])
def test_source_record_type_is_part_of_evidence_scope(batch, reference):
    assert validate(batch) == []
    batch["evidence"][reference]["scope"]["source_record_type"] = "synthetic-different-record-type"
    assert "EVIDENCE_SCOPE" in codes(batch)
    batch["evidence"][reference]["scope"]["source_record_type"] = "synthetic-boxscore-record"
    assert validate(batch) == []


def test_later_attribution_evidence_rejects_wrong_record_type(batch):
    row = batch["observations"][4]
    evidence(batch, "identity-7", T7)
    batch["evidence"]["identity-7"]["scope"]["source_record_type"] = (
        "synthetic-different-record-type"
    )
    attribute(
        batch,
        row,
        {
            "status": "resolved",
            "canonical_college_player_id": "synthetic-college-a",
            "aggregation_status": "eligible",
        },
        "identity-7",
        T7,
    )
    assert "EVIDENCE_SCOPE" in codes(batch)


def test_attribution_chain_accepts_newest_first_serialization(batch):
    row = batch["observations"][4]
    evidence(batch, "identity-7", T7)
    first = attribute(
        batch,
        row,
        {
            "status": "resolved",
            "canonical_college_player_id": "synthetic-college-a",
            "aggregation_status": "eligible",
        },
        "identity-7",
        T7,
    )
    evidence(batch, "identity-9", T9)
    attribute(
        batch,
        row,
        {
            "status": "resolved",
            "canonical_college_player_id": "synthetic-college-b",
            "aggregation_status": "eligible",
        },
        "identity-9",
        T9,
        first,
    )
    assert validate(batch) == []
    batch["attributions"].reverse()
    assert validate(batch) == []
    batch["attributions"][0]["supersedes_attribution_id"] = "synthetic-missing-ancestor"
    assert {"ATTRIBUTION_MISSING", "ATTRIBUTION_LINEAGE"} <= codes(batch)

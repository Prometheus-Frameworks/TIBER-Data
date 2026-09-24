"""SYNTHETIC direct representative graph at every knowledge cutoff."""

import copy
import json
from pathlib import Path

import pytest

from src.contracts.college_player_game_observations_v0 import validate
from tests.test_college_player_game_observations_v0_history import (
    T7,
    T8,
    T9,
    alias_claim,
    attribute,
    correct,
    evidence,
)

FIXTURE = Path(__file__).parent / "fixtures/college_observations/player_games.synthetic.json"


@pytest.fixture
def batch():
    return json.loads(FIXTURE.read_text())


def codes(batch):
    return {item["code"] for item in validate(batch)}


def add_alias(batch, name, representative):
    row = copy.deepcopy(batch["observations"][2])
    row.update(observation_id="synthetic-graph-" + name, retrieved_at=T7)
    row["identity"].update(
        source_player_id="synthetic-provider-" + name,
        aggregation_status="excluded_reconciled_alias",
        alias_of_observation_id=representative["observation_id"],
        evidence_refs=["synthetic-evidence-" + name],
    )
    evidence(
        batch,
        "synthetic-evidence-" + name,
        T7,
        claim=alias_claim(row, representative),
    )
    batch["observations"].append(row)
    return row


def retarget(batch, alias, representative):
    alias["identity"]["alias_of_observation_id"] = representative["observation_id"]
    label = alias["identity"]["evidence_refs"][0]
    batch["evidence"][label]["alias_claim"] = alias_claim(alias, representative)


def triple(batch):
    representative = batch["observations"][2]
    a = add_alias(batch, "a", representative)
    b = add_alias(batch, "b", representative)
    return representative, a, b


def test_two_direct_aliases_to_one_eligible_representative(batch):
    c, a, b = triple(batch)
    assert validate(batch) == []
    assert a["identity"]["alias_of_observation_id"] == c["observation_id"]
    assert b["identity"]["alias_of_observation_id"] == c["observation_id"]


def test_mutual_alias_cycle_with_eligible_third_is_invalid(batch):
    _, a, b = triple(batch)
    retarget(batch, a, b)
    retarget(batch, b, a)
    assert "ALIAS_REPRESENTATIVE" in codes(batch)


def test_self_alias_is_invalid(batch):
    _, a, _ = triple(batch)
    retarget(batch, a, a)
    assert "ALIAS_REFERENCE" in codes(batch)


def test_alias_chain_and_noneligible_target_are_invalid(batch):
    _, a, b = triple(batch)
    retarget(batch, a, b)
    assert "ALIAS_REPRESENTATIVE" in codes(batch)
    b["identity"]["aggregation_status"] = "blocked_alias_conflict"
    b["identity"]["alias_of_observation_id"] = None
    assert "ALIAS_REPRESENTATIVE" in codes(batch)


def test_two_or_zero_eligible_representatives_fail_closed(batch):
    _, a, b = triple(batch)
    a["identity"].update(aggregation_status="eligible", alias_of_observation_id=None)
    assert "ALIAS_CONFLICT" in codes(batch)
    a["identity"].update(
        aggregation_status="excluded_reconciled_alias",
        alias_of_observation_id=batch["observations"][2]["observation_id"],
    )
    batch["observations"][2]["identity"]["aggregation_status"] = "blocked_alias_conflict"
    assert "ALIAS_CONFLICT" in codes(batch)
    b["identity"].update(aggregation_status="blocked_alias_conflict", alias_of_observation_id=None)
    a["identity"].update(aggregation_status="blocked_alias_conflict", alias_of_observation_id=None)
    assert validate(batch) == []  # Explicit all-blocked quarantine is permitted.


@pytest.mark.parametrize("target_index", [0, 6, 8])
def test_wrong_canonical_game_or_future_revision_target(batch, target_index):
    _, a, _ = triple(batch)
    retarget(batch, a, batch["observations"][target_index])
    assert "ALIAS_REFERENCE" in codes(batch)


def test_wrong_provider_representative_is_invalid(batch):
    _, a, _ = triple(batch)
    target = copy.deepcopy(batch["observations"][2])
    target.update(
        observation_id="synthetic-other-provider-representative",
        provider="synthetic-other-provider",
    )
    batch["observations"].append(target)
    retarget(batch, a, target)
    assert "ALIAS_REFERENCE" in codes(batch)


def test_historical_cycle_stays_invalid_after_valid_later_rebinding(batch):
    c, a, b = triple(batch)
    retarget(batch, a, b)
    retarget(batch, b, a)
    assert "ALIAS_REPRESENTATIVE" in codes(batch)
    for row in (a, b):
        label = "synthetic-later-" + row["observation_id"]
        evidence(batch, label, T9, claim=alias_claim(row, c))
        attribute(
            batch,
            row,
            {"alias_of_observation_id": c["observation_id"]},
            label,
            T9,
        )
    findings = validate(batch)
    assert any(
        f["code"] == "ALIAS_REPRESENTATIVE" and f["path"].endswith("/identity") for f in findings
    )


def test_correction_preserves_old_review_and_requires_fresh_direct_binding(batch):
    c, a, b = triple(batch)
    old_a = copy.deepcopy(a)
    corrected = correct(batch, c, "synthetic-graph-representative-r2")
    assert validate(batch) == []
    assert old_a == a
    assert a["identity"]["alias_of_observation_id"] == c["observation_id"]
    assert corrected["identity"]["aggregation_status"] == "blocked_alias_conflict"
    evidence(batch, "synthetic-representative-new-review", T9)
    attribute(
        batch,
        corrected,
        {"aggregation_status": "eligible"},
        "synthetic-representative-new-review",
        T9,
    )
    assert "ALIAS_CONFLICT" in codes(batch)  # Neither old decision transfers.
    for row in (a, b):
        label = "synthetic-new-review-" + row["observation_id"]
        evidence(batch, label, T9, claim=alias_claim(row, corrected))
        attribute(
            batch,
            row,
            {"alias_of_observation_id": corrected["observation_id"]},
            label,
            T9,
        )
    assert validate(batch) == []
    assert a["identity"]["alias_of_observation_id"] == c["observation_id"]
    assert corrected["retrieved_at"] == T8

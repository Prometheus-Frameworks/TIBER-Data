"""All observations in this suite are deliberately synthetic; no I/O to providers."""

import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from src.contracts.college_player_game_observations_v0 import SCHEMA_PATH, validate

FIXTURE = Path(__file__).parent / "fixtures/college_observations/player_games.synthetic.json"


@pytest.fixture
def batch():
    return json.loads(FIXTURE.read_text())


def codes(batch):
    return {f["code"] for f in validate(batch)}


def test_schema_and_positions(batch):
    Draft202012Validator.check_schema(json.loads(SCHEMA_PATH.read_text()))
    assert validate(batch) == []
    rows = batch["observations"]
    assert {r["position"] for r in rows} == {"QB", "RB", "WR", "TE"}
    assert rows[0]["observed"]["passing"]["attempts"]["value"] == 30
    assert rows[0]["observed"]["rushing"]["yards"]["value"] == -3
    assert rows[1]["observed"]["rushing"]["carries"]["value"] == 15
    assert rows[1]["observed"]["receiving"]["receptions"]["value"] == 3


def test_targets_missing_and_explicit_zero(batch):
    wr, te = batch["observations"][2:4]
    assert wr["observed"]["receiving"]["receptions"]["value"] == 5
    assert wr["observed"]["receiving"]["targets"]["value"] is None
    assert wr["observed"]["receiving"]["targets"]["availability"] == "unavailable_from_source"
    assert te["observed"]["receiving"]["receptions"]["availability"] == "observed_zero"
    assert te["observed"]["receiving"]["receptions"]["value"] == 0
    assert validate(batch) == []


@pytest.mark.parametrize(
    "state",
    [
        "unavailable_from_source",
        "not_applicable",
        "unresolved_identity",
        "incomplete_coverage",
        "source_conflict",
        "excluded_by_contract",
    ],
)
def test_missing_states_never_accept_zero(batch, state):
    m = batch["observations"][2]["observed"]["receiving"]["targets"]
    m["availability"] = state
    if state == "not_applicable":
        batch["evidence"]["mapping"]["applicability_rules"].append(
            {
                "source_record_type": "synthetic-boxscore-record",
                "field": "receiving.targets",
                "rule_id": "field_not_defined_for_source_record_type",
            }
        )
        m["applicability_basis"] = {
            "rule_id": "field_not_defined_for_source_record_type",
            "source_record_type": "synthetic-boxscore-record",
            "evidence_refs": ["mapping", "snapshot-r1"],
        }
    assert validate(batch) == []
    m["value"] = 0
    assert "SCHEMA" in codes(batch)


@pytest.mark.parametrize(
    "state,value",
    [
        ("observed_zero", None),
        ("observed_value", None),
        ("observed_value", 0),
        ("observed_zero", 1),
        ("observed_value", True),
        ("observed_value", 1.5),
        ("observed_value", float("nan")),
    ],
)
def test_invalid_stat_values(batch, state, value):
    batch["observations"][2]["observed"]["receiving"]["targets"].update(
        availability=state, value=value
    )
    assert "SCHEMA" in codes(batch)


def test_negative_count_and_impossible_passing(batch):
    qb = batch["observations"][0]
    qb["observed"]["passing"]["attempts"]["value"] = -1
    assert {"STAT_DOMAIN", "PASS_COUNTS"} <= codes(batch)


def test_absence_is_not_zero_or_participation(batch):
    before = copy.deepcopy(batch)
    assert not any(
        r["identity"]["source_player_id"] == "synthetic-player-absent"
        for r in batch["observations"]
    )
    assert validate(batch) == []
    assert batch == before  # gate never manufactures absent rows
    batch["observations"] = []  # a scope can contain source games with no player rows
    batch["coverage"]["population_status"] = "unknown"
    assert validate(batch) == []


def test_identity_collision_and_transfer(batch):
    unresolved, ambiguous = batch["observations"][4:6]
    assert unresolved["identity"]["name"] == ambiguous["identity"]["name"]
    assert unresolved["identity"]["source_player_id"] != ambiguous["identity"]["source_player_id"]
    assert unresolved["identity"]["canonical_college_player_id"] is None
    assert ambiguous["identity"]["canonical_college_player_id"] is None
    old, new = batch["observations"][6:8]
    assert (
        old["identity"]["canonical_college_player_id"]
        == new["identity"]["canonical_college_player_id"]
    )
    assert old["game"]["team"] != new["game"]["team"]
    assert old["game"]["season"] == 2025
    assert new["game"]["season"] == 2026
    assert validate(batch) == []
    ambiguous["identity"]["canonical_college_player_id"] = "synthetic-fake-resolution"
    assert "IDENTITY_STATUS" in codes(batch)


@pytest.mark.parametrize("conflict", [False, True])
def test_duplicate_source_revision_different_row_id(batch, conflict):
    duplicate = copy.deepcopy(batch["observations"][0])
    duplicate["observation_id"] = "synthetic-duplicate"
    if conflict:
        duplicate["observed"]["passing"]["yards"]["value"] = 999
    batch["observations"].append(duplicate)
    assert ("CONFLICTING_REVISION" if conflict else "DUPLICATE_REVISION") in codes(batch)


def test_same_row_id_rejected(batch):
    batch["observations"].append(copy.deepcopy(batch["observations"][0]))
    assert "DUPLICATE_ID" in codes(batch)


def test_revision_history_and_as_known_evidence(batch):
    old, corrected = batch["observations"][0], batch["observations"][-1]
    assert corrected["supersedes"] == old["observation_id"]
    assert old["game"]["date"] == corrected["game"]["date"] == "2026-09-05"
    assert old["observed"]["passing"]["yards"]["value"] == 240
    assert corrected["observed"]["passing"]["yards"]["value"] == 245
    assert old["retrieved_at"] < "2026-09-07T00:00:00Z" < corrected["retrieved_at"]
    assert validate(batch) == []
    batch["observations"].reverse()  # lineage is independent of array ordering
    assert validate(batch) == []


@pytest.mark.parametrize(
    "change,code",
    [
        ("missing", "LINEAGE_MISSING"),
        ("wrong_game", "LINEAGE_GRAIN"),
        ("same_clock", "LINEAGE_CLOCK"),
        ("fork", "LINEAGE_FORK"),
        ("cycle", "LINEAGE_CLOCK"),
        ("unlinked", "UNLINKED_REVISION"),
        ("no_reason", "REVISION_REASON"),
    ],
)
def test_bad_lineage(batch, change, code):
    old, corrected = batch["observations"][0], batch["observations"][-1]
    if change == "missing":
        batch["observations"].pop(0)
    elif change == "wrong_game":
        corrected["game"]["source_game_id"] = "synthetic-game-2"
    elif change == "same_clock":
        corrected["retrieved_at"] = old["retrieved_at"]
    elif change == "fork":
        extra = copy.deepcopy(corrected)
        extra.update(observation_id="synthetic-fork", source_revision_id="synthetic-r3")
        batch["observations"].append(extra)
    elif change == "cycle":
        old.update(supersedes=corrected["observation_id"], revision_reason="SYNTHETIC cycle")
    elif change == "unlinked":
        corrected.update(supersedes=None, revision_reason=None)
    else:
        corrected["revision_reason"] = None
    assert code in codes(batch)


def test_partial_categories_games_and_population(batch):
    assert validate(batch) == []
    batch["coverage"]["population_status"] = "complete"
    assert "COVERAGE_COMPLETE" in codes(batch)
    batch["coverage"]["population_status"] = "partial"
    batch["observations"][2]["category_completeness"]["receiving"] = "complete"
    assert "CATEGORY_COMPLETE" in codes(batch)


def test_complete_declared_scope_and_unknown_expectations(batch):
    scope = batch["coverage"]["game_scope"]
    scope["expected_game_ids"] = scope["observed_game_ids"][:]
    batch["coverage"]["population_status"] = "complete"
    assert validate(batch) == []
    scope.update(expected_game_ids=None, expectation_evidence_refs=[])
    batch["coverage"]["population_status"] = "unknown"
    assert validate(batch) == []
    scope["expected_game_ids"] = [{"season": 2026, "source_game_id": "synthetic-game-1"}]
    assert "GAME_EXPECTATION" in codes(batch)


def test_game_finality_is_not_inferred(batch):
    batch["observations"][2]["game"]["status"] = "in_progress"
    batch["observations"][2]["observed"]["receiving"]["targets"]["availability"] = (
        "incomplete_coverage"
    )
    assert validate(batch) == []


def test_clock_origins_and_unknown_source_time(batch):
    clock = batch["observations"][0]["source_updated_at"]
    clock.update(value=None, origin="not_supplied_by_source")
    assert validate(batch) == []
    clock["value"] = batch["observations"][0]["retrieved_at"]
    assert "SOURCE_CLOCK" in codes(batch)
    clock["origin"] = "retrieval_clock"
    assert "SCHEMA" in codes(batch)


def test_unknown_event_date_and_clock_order(batch):
    row = batch["observations"][0]
    row["game"].update(date=None, date_origin="not_supplied_by_source")
    assert validate(batch) == []
    row["game"]["date"] = "2026-09-06"
    assert "EVENT_CLOCK" in codes(batch)
    row["retrieved_at"] = "2026-09-10T00:00:00Z"
    assert "CLOCK_ORDER" in codes(batch)


def test_timestamp_validation_and_timezones(batch):
    batch["observations"][0]["retrieved_at"] = "2026-09-06T14:00:00+02:00"
    assert validate(batch) == []
    batch["generated_at"] = "yesterday"
    assert "SCHEMA" in codes(batch)


def test_evidence_refs_and_no_fixture_promotion(batch):
    batch["observations"][0]["mapping_ref"] = "missing"
    assert "EVIDENCE_REF" in codes(batch)
    batch["evidence_mode"] = "source_observation"
    assert "SYNTHETIC_PROVENANCE" in codes(batch)
    batch["artifact_position"] = "promoted"
    assert "SCHEMA" in codes(batch)


@pytest.mark.parametrize("key", ["fantasy_points", "devy_score", "estimated_targets", "derived"])
def test_interpretation_and_derivation_not_accepted_as_raw(batch, key):
    batch["observations"][2]["observed"]["receiving"][key] = 7
    assert "SCHEMA" in codes(batch)


def test_deterministic_validation_and_cli(batch):
    before = copy.deepcopy(batch)
    assert validate(batch) == validate(batch) == []
    assert batch == before
    cmd = [sys.executable, "-m", "src.contracts.college_player_game_observations_v0", str(FIXTURE)]
    first = subprocess.run(cmd, text=True, capture_output=True, check=True)
    second = subprocess.run(cmd, text=True, capture_output=True, check=True)
    assert first.stdout == second.stdout == '{"findings": [], "valid": true}\n'


def test_provider_scope_and_reference_kind(batch):
    batch["observations"][0]["provider"] = "synthetic-other-provider"
    assert "PROVIDER_SCOPE" in codes(batch)
    batch["observations"][0]["mapping_ref"] = "identity"
    assert "EVIDENCE_KIND" in codes(batch)


def test_digest_revision_and_category_contradiction(batch):
    row = batch["observations"][1]
    row.update(revision_origin="retained_snapshot_digest", source_revision_id="sha256:" + "a" * 64)
    batch["evidence"]["snapshot-digest"] = copy.deepcopy(batch["evidence"]["snapshot-r1"])
    batch["evidence"]["snapshot-digest"]["locator"] = "synthetic:snapshot-digest"
    batch["evidence"]["snapshot-digest"]["scope"]["source_revision_id"] = row["source_revision_id"]
    row["source_snapshot_ref"] = "snapshot-digest"
    row["source_updated_at"]["evidence_refs"] = ["snapshot-digest"]
    row["game"]["status_evidence_refs"] = ["snapshot-digest"]
    for group in row["observed"].values():
        for metric in group.values():
            metric["evidence_refs"] = ["snapshot-digest"]
    assert validate(batch) == []
    row["source_revision_id"] = "retrieval-2026-09-06"
    assert "REVISION_DIGEST" in codes(batch)
    row["category_completeness"]["rushing"] = "unavailable"
    assert "CATEGORY_UNAVAILABLE" in codes(batch)


def test_cli_rejects_duplicate_json_keys(tmp_path):
    path = tmp_path / "duplicate.synthetic.json"
    path.write_text('{"artifact_type": "first", "artifact_type": "second"}')
    result = subprocess.run(
        [sys.executable, "-m", "src.contracts.college_player_game_observations_v0", str(path)],
        text=True,
        capture_output=True,
    )
    assert result.returncode == 1
    assert "Duplicate JSON key" in result.stdout

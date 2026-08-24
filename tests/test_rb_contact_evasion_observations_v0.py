"""Schema-boundary tests for rb_contact_evasion_observations_v0 (TIBER-Data #234, Slice A).

Scope note. This slice ships a contract, a schema, documentation, and a fixture
corpus. It ships **no** builder, no candidate or promoted artifact, and no
Python artifact validator or manifest gate (those are Slice B and are not
authorized here). So these tests exercise the committed JSON schema directly as
the shape gate, and assert honestly where that gate stops:

- the schema closes the vocabularies, requires all seven clocks, and rejects
  unknown fields at every level;
- the schema is a SHAPE gate only. Every N1-N15 fixture is deliberately
  shape-valid, so the schema accepts all of them. Their rejection is the job of
  the cross-field contract layer in
  ``src/contracts/v1/rbContactEvasionObservationsV0.ts``, proven in
  ``test/rbContactEvasionObservationsV0.contract.test.ts``. This module asserts
  that split explicitly rather than implying the schema catches more than it does.
"""

from __future__ import annotations

import copy
import json
import re
from pathlib import Path

import jsonschema
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = REPO_ROOT / "schemas/rb_contact_evasion_observations_v0.schema.json"
CONTRACT_TS_PATH = REPO_ROOT / "src/contracts/v1/rbContactEvasionObservationsV0.ts"
DOC_PATH = REPO_ROOT / "docs/contracts/rb-contact-evasion-observations-v0.md"
FIXTURE_ROOT = REPO_ROOT / "test/fixtures/rb_contact_evasion"

# P1-P7 are the corpus TIBER-Data #234 mandates; P8 was added in the
# review-repair round to show an unavailable source clock staying honestly null.
MANDATED_POSITIVE_FIXTURES = [
    "p1_complete_derived_explosiveness_rate.json",
    "p2_raw_count_without_denominator.json",
    "p3_historical_testing_classified.json",
    "p4_rights_blocked_missing_component.json",
    "p5_declared_snapshot_supersession.json",
    "p6_weekly_and_season_windows_coexist.json",
    "p7_bucky_receipt_remains_partial.json",
]
SUPPLEMENTARY_POSITIVE_FIXTURES = ["p8_absent_source_clock_stays_null.json"]
POSITIVE_FIXTURES = MANDATED_POSITIVE_FIXTURES + SUPPLEMENTARY_POSITIVE_FIXTURES

# Fixture file -> the single reason code the contract layer must reject it with.
# N1-N15 are the corpus #234 mandates.
MANDATED_NEGATIVE_FIXTURES = {
    "n01_rate_missing_denominator.json": "RATE_MISSING_DENOMINATOR",
    "n02_denominator_unsupported_by_source.json": "DENOMINATOR_OPPORTUNITY_UNSUPPORTED_BY_SOURCE",
    "n03_rushing_receiving_silently_combined.json": "RUSHING_RECEIVING_SILENTLY_COMBINED",
    "n04_metric_definition_drift.json": "METRIC_DEFINITION_DRIFT_UNDER_STABLE_ID",
    "n05_reference_only_source_overclaimed.json": "RESTRICTED_SOURCE_ACCESS_OVERCLAIMED",
    "n06_external_opinion_labeled_observation.json": "EXTERNAL_OPINION_LABELED_AS_OBSERVATION",
    "n07_partial_full_window_comparison_undisclosed.json": (
        "WINDOW_COMPLETENESS_COMPARISON_UNDISCLOSED"
    ),
    "n08_below_minimum_sample_rate_emitted.json": "MINIMUM_SAMPLE_NOT_MET_RATE_EMITTED",
    "n09_cohort_scope_mismatch.json": "COHORT_SCOPE_MISMATCH",
    "n10_retrieval_clock_substituted.json": "RETRIEVAL_CLOCK_SUBSTITUTED_FOR_SOURCE_CLOCK",
    "n11_canonical_identity_unresolved.json": "CANONICAL_IDENTITY_UNRESOLVED",
    "n12_mechanism_metric_binding_violation.json": "MECHANISM_METRIC_BINDING_VIOLATION",
    "n13_default_value_for_missing_component.json": "MISSING_COMPONENT_CARRIES_VALUE",
    "n14_incompatible_transform_inputs.json": "INCOMPATIBLE_METRIC_TRANSFORM_INPUT",
    "n15_fixture_provenance_in_candidate_position.json": (
        "FIXTURE_PROVENANCE_IN_CANDIDATE_POSITION"
    ),
}

# N16-N28 were added in the review-repair round: one fixture per escape the first
# exact-head review reproduced against the public evaluator.
SUPPLEMENTARY_NEGATIVE_FIXTURES = {
    "n16_promotable_without_permissions.json": (
        "SOURCE_PERMISSIONS_INCOMPATIBLE_WITH_PROMOTABLE"
    ),
    "n17_direct_observation_without_retention.json": (
        "SOURCE_PERMISSIONS_INCOMPATIBLE_WITH_EVIDENCE_CLASS"
    ),
    "n18_snapshot_without_content_digest.json": "SNAPSHOT_WITHOUT_CONTENT_DIGEST",
    "n19_duplicate_observation_id.json": "DUPLICATE_OBSERVATION_ID",
    "n20_duplicate_observation_grain.json": "DUPLICATE_OBSERVATION_GRAIN",
    "n21_rate_value_inconsistent_with_components.json": (
        "RATE_VALUE_INCONSISTENT_WITH_COMPONENTS"
    ),
    "n22_rate_component_metric_mismatch.json": "RATE_COMPONENT_METRIC_MISMATCH",
    "n23_rate_denominator_not_positive.json": "RATE_DENOMINATOR_NOT_POSITIVE",
    "n24_metric_descriptor_contradicted.json": "METRIC_DESCRIPTOR_CONTRADICTED",
    "n25_eligible_opportunities_absent.json": "ELIGIBLE_OPPORTUNITIES_REQUIRED_FOR_RATE",
    "n26_clock_availability_contradicted.json": "CLOCK_AVAILABILITY_CONTRADICTED",
    "n27_minimum_sample_rule_not_code_owned.json": "MINIMUM_SAMPLE_RULE_NOT_CODE_OWNED",
    "n28_minimum_sample_rule_not_admitted_for_position.json": (
        "MINIMUM_SAMPLE_RULE_NOT_ADMITTED_FOR_POSITION"
    ),
}

NEGATIVE_FIXTURES = {**MANDATED_NEGATIVE_FIXTURES, **SUPPLEMENTARY_NEGATIVE_FIXTURES}

MECHANISMS = [
    "speed",
    "agility_change_of_direction",
    "contact_avoidance",
    "contact_survival",
    "explosiveness",
]
EVIDENCE_CLASSES = ["direct", "normalized", "derived", "external_opinion"]
SOURCE_ACCESS_CLASSES = [
    "open_and_ingestible",
    "public_but_terms_constrained",
    "licensed_or_gated",
    "reference_only",
    "unavailable",
    "unknown",
]
PROVENANCE_MODES = ["live", "snapshot", "fixture"]
CLOCK_PROVENANCE = [
    "football_window",
    "source_supplied",
    "not_supplied_by_source",
    "retrieval_clock",
    "artifact_build_clock",
]
PERMISSION_DISPOSITIONS = ["permitted", "prohibited", "unknown"]
ATTRIBUTION_DISPOSITIONS = ["required", "not_required", "unknown"]
MINIMUM_SAMPLE_RULE_ID = "rb_contact_evasion_fixture_only_minimum_sample_v0"
REQUIRED_CLOCKS = [
    "window_start",
    "window_end",
    "source_observed_at",
    "source_generated_at",
    "source_available_at",
    "retrieved_at",
    "artifact_generated_at",
]

FORBIDDEN_VOCABULARY = re.compile(
    r"score|composite|grade|ranking|percentile|tier|rating|fantasy|overall|elite"
    r"|neutral_default",
    re.IGNORECASE,
)


def load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def load_fixture(kind: str, name: str) -> dict:
    return json.loads((FIXTURE_ROOT / kind / name).read_text(encoding="utf-8"))


def schema_errors(payload: dict) -> list[str]:
    validator = jsonschema.Draft202012Validator(load_schema())
    return [
        f"{'/'.join(str(part) for part in error.path)}: {error.message}"
        for error in validator.iter_errors(payload)
    ]


def test_schema_is_itself_a_valid_draft_2020_12_schema():
    jsonschema.Draft202012Validator.check_schema(load_schema())


@pytest.mark.parametrize("name", POSITIVE_FIXTURES)
def test_positive_fixtures_satisfy_the_schema(name: str):
    assert schema_errors(load_fixture("positive", name)) == []


def test_fixture_corpus_matches_the_declared_lists():
    positives = sorted(p.name for p in (FIXTURE_ROOT / "positive").glob("*.json"))
    negatives = sorted(p.name for p in (FIXTURE_ROOT / "negative").glob("*.json"))
    assert positives == sorted(POSITIVE_FIXTURES)
    assert negatives == sorted(NEGATIVE_FIXTURES)


def test_the_mandated_234_corpus_remains_intact():
    """The review round added fixtures; it must not have dropped #234's own."""
    assert len(MANDATED_POSITIVE_FIXTURES) == 7
    assert len(MANDATED_NEGATIVE_FIXTURES) == 15
    for name in MANDATED_POSITIVE_FIXTURES:
        assert (FIXTURE_ROOT / "positive" / name).is_file()
    for name in MANDATED_NEGATIVE_FIXTURES:
        assert (FIXTURE_ROOT / "negative" / name).is_file()


@pytest.mark.parametrize("name", sorted(NEGATIVE_FIXTURES))
def test_negative_fixtures_are_shape_valid_so_rejection_is_attributable(name: str):
    """Every negative fixture must PASS the shape gate.

    This is the point of the corpus: if a negative fixture failed here, its
    rejection by the contract layer could not be attributed to the contract rule
    it exists to exercise -- it would just be malformed JSON.
    """
    assert schema_errors(load_fixture("negative", name)) == []


def test_negative_reason_codes_are_distinct():
    codes = list(NEGATIVE_FIXTURES.values())
    assert len(set(codes)) == len(codes)
    assert len(set(MANDATED_NEGATIVE_FIXTURES.values())) == 15


def test_every_negative_reason_code_exists_in_the_contract_implementation():
    contract_source = CONTRACT_TS_PATH.read_text(encoding="utf-8")
    for name, code in NEGATIVE_FIXTURES.items():
        assert f"'{code}'" in contract_source, f"{name} maps to unknown reason code {code}"


def test_documentation_lists_every_fixture_and_reason_code():
    doc = DOC_PATH.read_text(encoding="utf-8")
    for name in POSITIVE_FIXTURES:
        assert name in doc, f"positive fixture {name} is undocumented"
    for name, code in NEGATIVE_FIXTURES.items():
        assert name in doc, f"negative fixture {name} is undocumented"
        assert code in doc, f"reason code {code} is undocumented"


def test_schema_closes_every_object_against_unknown_fields():
    schema = load_schema()
    open_objects: list[str] = []

    def walk(node, trail: str) -> None:
        if isinstance(node, list):
            for index, item in enumerate(node):
                walk(item, f"{trail}[{index}]")
            return
        if not isinstance(node, dict):
            return
        if node.get("type") == "object" and node.get("additionalProperties") is not False:
            open_objects.append(trail)
        for key, value in node.items():
            walk(value, f"{trail}.{key}")

    walk(schema, "$")
    assert open_objects == [], f"unknown-field escape hatches at: {open_objects}"


@pytest.mark.parametrize(
    "pointer",
    [
        ("elusiveness_score", None),
        ("observations", "row"),
        ("observations", "measurement"),
        ("observations", "source"),
    ],
)
def test_schema_rejects_injected_unknown_fields(pointer):
    payload = load_fixture("positive", "p1_complete_derived_explosiveness_rate.json")
    top_key, level = pointer
    mutated = copy.deepcopy(payload)
    if level is None:
        mutated[top_key] = 0.9
    elif level == "row":
        mutated["observations"][0]["elusiveness_grade"] = "A"
    else:
        mutated["observations"][0][level]["percentile"] = 0.91
    assert schema_errors(mutated) != []


def test_schema_closes_the_five_mechanism_universe():
    defs = load_schema()["$defs"]
    assert defs["mechanismId"]["enum"] == MECHANISMS
    payload = load_fixture("positive", "p1_complete_derived_explosiveness_rate.json")
    for rejected in ("elusiveness", "unknown", "vision", "balance"):
        mutated = copy.deepcopy(payload)
        mutated["observations"][0]["mechanism_id"] = rejected
        assert schema_errors(mutated) != [], f"{rejected} must not enter the mechanism universe"


def test_schema_closes_the_governance_vocabularies():
    defs = load_schema()["$defs"]
    assert defs["evidenceClass"]["enum"] == EVIDENCE_CLASSES
    assert defs["sourceAccessClass"]["enum"] == SOURCE_ACCESS_CLASSES
    assert defs["provenanceMode"]["enum"] == PROVENANCE_MODES
    assert defs["artifactPosition"]["enum"] == ["fixture_only", "candidate", "promoted"]
    assert defs["clockProvenance"]["enum"] == CLOCK_PROVENANCE
    assert defs["permissionDisposition"]["enum"] == PERMISSION_DISPOSITIONS
    assert defs["attributionDisposition"]["enum"] == ATTRIBUTION_DISPOSITIONS


def test_schema_requires_separate_rights_dispositions_and_a_digest_slot():
    """#234 requires attribution, retention, redistribution, and automation
    to be stated independently, plus a payload digest slot where permitted."""
    defs = load_schema()["$defs"]
    assert sorted(defs["sourcePermissions"]["required"]) == [
        "attribution",
        "automated_access",
        "redistribution_and_display",
        "retention_and_reproduction",
    ]
    assert "permissions" in defs["source"]["required"]
    assert "content_digest" in defs["source"]["required"]
    payload = load_fixture("positive", "p1_complete_derived_explosiveness_rate.json")
    for field in ("attribution", "retention_and_reproduction",
                  "redistribution_and_display", "automated_access"):
        mutated = copy.deepcopy(payload)
        del mutated["observations"][0]["source"]["permissions"][field]
        assert schema_errors(mutated) != [], f"permissions.{field} must be required"


def test_schema_lets_an_unavailable_source_clock_stay_null():
    """An unavailable source clock must be representable as null with a declared
    origin, rather than forced to carry a backfilled timestamp."""
    payload = load_fixture("positive", "p8_absent_source_clock_stays_null.json")
    assert payload["observations"][0]["clocks"]["source_generated_at"] is None
    assert (
        payload["observations"][0]["clock_provenance"]["source_generated_at"]
        == "not_supplied_by_source"
    )
    assert schema_errors(payload) == []


def test_schema_requires_a_declared_origin_for_every_clock():
    defs = load_schema()["$defs"]
    assert sorted(defs["clockProvenanceMap"]["required"]) == sorted(REQUIRED_CLOCKS)
    payload = load_fixture("positive", "p1_complete_derived_explosiveness_rate.json")
    for clock in REQUIRED_CLOCKS:
        mutated = copy.deepcopy(payload)
        del mutated["observations"][0]["clock_provenance"][clock]
        assert schema_errors(mutated) != [], f"{clock} must declare an origin"


def test_schema_gives_a_row_no_self_declared_minimum_sample_threshold():
    """The governing minimum is code-owned; a row names the rule, never a number."""
    defs = load_schema()["$defs"]
    assert "minimum_sample_rule_id" in defs["metric"]["required"]
    assert "minimum_eligible_opportunities" not in defs["metric"]["properties"]
    assert "minimum_eligible_opportunities" not in defs["cohortScope"]["properties"]
    payload = load_fixture("positive", "p1_complete_derived_explosiveness_rate.json")
    assert (
        payload["observations"][0]["metric"]["minimum_sample_rule_id"]
        == MINIMUM_SAMPLE_RULE_ID
    )
    mutated = copy.deepcopy(payload)
    mutated["observations"][0]["metric"]["minimum_eligible_opportunities"] = 1
    assert schema_errors(mutated) != [], "a row must not be able to state its own threshold"


def test_schema_requires_all_seven_clocks_separately():
    clocks = load_schema()["$defs"]["clocks"]
    assert sorted(clocks["required"]) == sorted(REQUIRED_CLOCKS)
    assert sorted(clocks["properties"]) == sorted(REQUIRED_CLOCKS)
    payload = load_fixture("positive", "p1_complete_derived_explosiveness_rate.json")
    for clock in REQUIRED_CLOCKS:
        mutated = copy.deepcopy(payload)
        del mutated["observations"][0]["clocks"][clock]
        assert schema_errors(mutated) != [], f"{clock} must be individually required"


def test_schema_requires_explicit_provenance_mode_and_access_class():
    payload = load_fixture("positive", "p1_complete_derived_explosiveness_rate.json")
    for field in ("provenance_mode", "access_class", "promotable", "material_kind"):
        mutated = copy.deepcopy(payload)
        del mutated["observations"][0]["source"][field]
        assert schema_errors(mutated) != [], f"source.{field} must be required"


def test_schema_names_no_score_composite_grade_ranking_or_fantasy_field():
    schema = load_schema()
    offenders: list[str] = []

    def walk(node, trail: str) -> None:
        if isinstance(node, list):
            for index, item in enumerate(node):
                walk(item, f"{trail}[{index}]")
            return
        if not isinstance(node, dict):
            return
        for key, value in node.items():
            if key == "properties" and isinstance(value, dict):
                offenders.extend(
                    f"{trail}.{prop}" for prop in value if FORBIDDEN_VOCABULARY.search(prop)
                )
            if key in {"$defs", "properties"} and isinstance(value, dict):
                offenders.extend(
                    f"{trail}.$defs.{name}"
                    for name in value
                    if key == "$defs" and FORBIDDEN_VOCABULARY.search(name)
                )
            walk(value, f"{trail}.{key}")

    walk(schema, "$")
    assert offenders == []

    for enum_name in ("mechanismId", "evidenceClass", "missingnessReason", "valueKind"):
        for option in schema["$defs"][enum_name]["enum"]:
            assert not FORBIDDEN_VOCABULARY.search(option), option


def test_no_fixture_sits_in_a_promoted_position_and_no_export_path_is_touched():
    for name in POSITIVE_FIXTURES:
        assert load_fixture("positive", name)["artifact_position"] == "fixture_only"
    # Exactly two fixtures model a candidate position, each so the contract
    # layer has an illegal state to reject there: N15 (fixture provenance in a
    # candidate artifact) and N28 (an observed rate where no admitted
    # minimum-sample rule is bound). Nothing sits in a promoted position at all.
    positions = {
        name: load_fixture("negative", name)["artifact_position"] for name in NEGATIVE_FIXTURES
    }
    candidate_fixtures = {
        "n15_fixture_provenance_in_candidate_position.json",
        "n28_minimum_sample_rule_not_admitted_for_position.json",
    }
    assert {name for name, pos in positions.items() if pos == "candidate"} == candidate_fixtures
    assert all(
        position == "fixture_only"
        for name, position in positions.items()
        if name not in candidate_fixtures
    )
    assert all(position != "promoted" for position in positions.values())


def test_only_the_governed_bucky_trace_carries_a_real_canonical_identity():
    """No fixture carries acquired provider data or a second real player identity."""
    bucky = "00-0039361"
    for kind, names in (("positive", POSITIVE_FIXTURES), ("negative", list(NEGATIVE_FIXTURES))):
        for name in names:
            payload = load_fixture(kind, name)
            for observation in payload["observations"]:
                gsis_id = observation["identity"]["gsis_id"]
                display = observation["identity"]["display_name_non_authoritative"]
                if name == "p7_bucky_receipt_remains_partial.json":
                    assert gsis_id == bucky
                    assert display == "Bucky Irving"
                else:
                    assert gsis_id != bucky, f"{name} uses the golden-trace identity"
                    assert display in (None, "Synthetic Fixture Player")
                assert observation["source"]["owner"].startswith("example_")
                assert "synthetic" in observation["source"]["snapshot_id"]
                assert any(
                    "synthetic contract-fixture value" in warning
                    for warning in observation["warnings"]
                ), f"{name}/{observation['observation_id']} must declare synthetic values"

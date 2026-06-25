from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import probe_team_week_raw_v0_2024_sources as probe

REQUIRED_FIELDS = {
    "season",
    "week",
    "teamCode",
    "opponentCode",
    "offensivePlays",
    "neutralPlays",
    "secondsPerPlay",
    "passRate",
    "neutralPassRate",
    "rushRate",
    "epaPerPlay",
    "passEpaPerPlay",
    "rushEpaPerPlay",
    "successRate",
    "explosivePlayRate",
    "drives",
    "pointsPerDrive",
    "pointsFor",
    "pointsAgainst",
    "pressureRateAllowed",
    "turnovers",
    "sacksAllowed",
    "redZoneTrips",
    "redZoneTdRate",
}

OPTIONAL_FIELDS = {
    "fantasyPointsForQB",
    "fantasyPointsForRB",
    "fantasyPointsForWR",
    "fantasyPointsForTE",
    "fantasyPointsAllowedQB",
    "fantasyPointsAllowedRB",
    "fantasyPointsAllowedWR",
    "fantasyPointsAllowedTE",
}


def test_required_field_mapping_is_complete_and_bounded() -> None:
    fields = {mapping.field for mapping in probe.REQUIRED_FIELD_MAPPINGS}
    assert fields == REQUIRED_FIELDS
    assert {mapping.classification for mapping in probe.REQUIRED_FIELD_MAPPINGS} <= {
        probe.CLASS_DIRECT,
        probe.CLASS_DERIVABLE,
        probe.CLASS_REQUIRES_PBP,
        probe.CLASS_REQUIRES_ADDITIONAL_SOURCE,
        probe.CLASS_DEFERRED_BLOCKED,
    }


def test_optional_fantasy_fields_are_deferred_and_non_blocking() -> None:
    fields = {mapping.field for mapping in probe.OPTIONAL_FIELD_MAPPINGS}
    assert fields == OPTIONAL_FIELDS
    assert {mapping.status for mapping in probe.OPTIONAL_FIELD_MAPPINGS} == {
        "deferred_not_blocking"
    }
    assert all("do not block" in mapping.note for mapping in probe.OPTIONAL_FIELD_MAPPINGS)


def test_default_probe_does_not_attempt_fetch_or_create_candidate_artifact() -> None:
    payload = probe.build_payload(fetch_schemas=False)
    assert payload["mode"] == "dry_run_schema_mapping_only"
    assert "no real 2024 artifact emitted" in payload["guardrails"]
    assert payload["candidatePathsNotCreated"]["artifact"].startswith("exports/candidates/")
    assert all(not source["fetch_attempted"] for source in payload["sources"])


def test_rendered_report_keeps_governance_and_window_boundaries() -> None:
    markdown = probe.render_markdown(probe.build_payload(fetch_schemas=False))
    assert "No artifact can be marked `governed_real_data` from this probe" in markdown
    assert "path inference is not governance" in markdown
    assert "full Week 1-18 regular-season window vs fantasy-aligned window" in markdown
    assert "Insufficient for full governed 2024 all-32 coverage" in markdown

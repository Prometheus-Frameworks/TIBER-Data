# ruff: noqa: E501
from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import importlib.util
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any

SEASON = 2024
SPEC_PATH = "docs/data/team-week-raw-v0-2024-source-artifact-spec.md"
REPORT_PATH = "docs/data/team-week-raw-v0-2024-source-probe.md"
CANDIDATE_ARTIFACT_PATH = (
    "exports/candidates/team_week_raw/team_week_raw_v0_2024_real_source_candidate.json"
)
CANDIDATE_VALIDATION_REPORT_PATH = (
    "exports/candidates/team_week_raw/team_week_raw_v0_2024_real_source_candidate.validation.json"
)
LINEAGE_MANIFEST_PATH = "data/manifests/team_week_raw_v0_2024_real_source_candidate.manifest.json"

CLASS_DIRECT = "direct"
CLASS_DERIVABLE = "derivable"
CLASS_REQUIRES_PBP = "requires_play_by_play"
CLASS_REQUIRES_ADDITIONAL_SOURCE = "requires_additional_source"
CLASS_DEFERRED_BLOCKED = "deferred_or_blocked"


@dataclass(frozen=True)
class FieldMapping:
    field: str
    classification: str
    source_basis: str
    deterministic_rule_needed: str
    unresolved_or_blocked: str


@dataclass(frozen=True)
class OptionalFieldMapping:
    field: str
    status: str
    note: str


@dataclass(frozen=True)
class SourceProbe:
    source_name: str
    source_type: str
    retrieval_method: str
    available_without_fetch: bool
    package_version: str | None
    fetch_attempted: bool
    fetch_status: str
    columns: list[str]
    limitations: list[str]


REQUIRED_FIELD_MAPPINGS: tuple[FieldMapping, ...] = (
    FieldMapping(
        "season",
        CLASS_DIRECT,
        "weekly team stats or play-by-play season column",
        "Normalize to integer season=2024.",
        "None after source availability is confirmed.",
    ),
    FieldMapping(
        "week",
        CLASS_DIRECT,
        "weekly team stats or play-by-play week column",
        "Normalize to integer NFL week and filter to the unresolved approved window.",
        "Window remains unresolved.",
    ),
    FieldMapping(
        "teamCode",
        CLASS_DIRECT,
        "weekly team stats team column or play-by-play possession team",
        "Canonicalize to TIBER team abbreviation set before validation.",
        "Team alias policy must be enforced.",
    ),
    FieldMapping(
        "opponentCode",
        CLASS_REQUIRES_PBP,
        "play-by-play defensive/opponent team or schedule/game join",
        "Derive from paired game context and validate reciprocal team-game rows.",
        "Weekly team stats alone may not provide opponent.",
    ),
    FieldMapping(
        "offensivePlays",
        CLASS_DERIVABLE,
        "weekly team pass/rush attempts or play-by-play filtered offensive plays",
        "Define included offensive plays and aggregate by team/week.",
        "Play inclusion rules must be settled.",
    ),
    FieldMapping(
        "neutralPlays",
        CLASS_REQUIRES_PBP,
        "play-by-play game state",
        "Define neutral script, filter eligible plays, and count by team/week.",
        "Neutral script thresholds are unresolved.",
    ),
    FieldMapping(
        "secondsPerPlay",
        CLASS_REQUIRES_PBP,
        "play-by-play game clock / elapsed time",
        "Compute elapsed offensive seconds divided by included offensive plays.",
        "Clock handling, period boundaries, and no-play treatment are unresolved.",
    ),
    FieldMapping(
        "passRate",
        CLASS_DERIVABLE,
        "weekly team pass attempts and offensive plays or play-by-play pass flags",
        "Pass attempts divided by included offensive plays using the same denominator as offensivePlays.",
        "Scramble/sack/dropback treatment must be explicit.",
    ),
    FieldMapping(
        "neutralPassRate",
        CLASS_REQUIRES_PBP,
        "play-by-play neutral-script subset",
        "Pass attempts in neutral subset divided by neutralPlays.",
        "Neutral script and pass/dropback treatment unresolved.",
    ),
    FieldMapping(
        "rushRate",
        CLASS_DERIVABLE,
        "weekly team rush attempts and offensive plays or play-by-play rush flags",
        "Rush attempts divided by included offensive plays using the same denominator as offensivePlays.",
        "Kneel/spike/scramble treatment must be explicit.",
    ),
    FieldMapping(
        "epaPerPlay",
        CLASS_REQUIRES_PBP,
        "play-by-play EPA field",
        "Average EPA over included offensive plays by team/week.",
        "EPA provider/version and inclusion rules must be recorded.",
    ),
    FieldMapping(
        "passEpaPerPlay",
        CLASS_REQUIRES_PBP,
        "play-by-play EPA and pass/dropback flag",
        "Average EPA over included pass/dropback plays by team/week.",
        "Sacks/scrambles/dropbacks must be defined.",
    ),
    FieldMapping(
        "rushEpaPerPlay",
        CLASS_REQUIRES_PBP,
        "play-by-play EPA and rush flag",
        "Average EPA over included rush plays by team/week.",
        "Kneels and scrambles must be defined.",
    ),
    FieldMapping(
        "successRate",
        CLASS_REQUIRES_PBP,
        "play-by-play success indicator or EPA/down-distance derivation",
        "Aggregate agreed success definition over included offensive plays.",
        "Success definition/source version unresolved.",
    ),
    FieldMapping(
        "explosivePlayRate",
        CLASS_REQUIRES_PBP,
        "play-by-play gained yards and play type",
        "Count plays meeting agreed explosive thresholds divided by included plays.",
        "Explosive thresholds unresolved.",
    ),
    FieldMapping(
        "drives",
        CLASS_REQUIRES_PBP,
        "play-by-play drive id or drive table",
        "Count offensive drives by team/week after drive inclusion exclusions.",
        "End-of-half/game and kneel-only drives need rules.",
    ),
    FieldMapping(
        "pointsPerDrive",
        CLASS_REQUIRES_PBP,
        "drive count plus points scored by drive/team",
        "pointsFor divided by included offensive drives, or sum drive points divided by drives.",
        "Drive scoring attribution must be explicit.",
    ),
    FieldMapping(
        "pointsFor",
        CLASS_DIRECT,
        "weekly team stats points/total_points or game score",
        "Normalize source points scored by team/week.",
        "Confirm source column semantics include team points, not fantasy points.",
    ),
    FieldMapping(
        "pointsAgainst",
        CLASS_REQUIRES_PBP,
        "schedule/game score join or opponent paired rows",
        "Derive from opponent score for the same game/week and validate reciprocity.",
        "Weekly team stats alone may not provide points against.",
    ),
    FieldMapping(
        "pressureRateAllowed",
        CLASS_REQUIRES_ADDITIONAL_SOURCE,
        "not confirmed in weekly team stats or standard play-by-play probe",
        "If available, divide pressures allowed by governed dropback/pass-block denominator.",
        "Likely needs charting/provider source or explicit deferral.",
    ),
    FieldMapping(
        "turnovers",
        CLASS_REQUIRES_PBP,
        "play-by-play interception/fumble turnover events",
        "Attribute offensive turnovers to possession team by week.",
        "Aborted plays, laterals, and special teams exclusions need rules.",
    ),
    FieldMapping(
        "sacksAllowed",
        CLASS_REQUIRES_PBP,
        "play-by-play sack/dropback fields",
        "Attribute offensive sacks to possession team by week.",
        "Scramble/aborted-play treatment must be explicit.",
    ),
    FieldMapping(
        "redZoneTrips",
        CLASS_REQUIRES_PBP,
        "play-by-play yardline/drive data",
        "Count offensive drives with a snap at or inside the opponent 20.",
        "Drive and penalty/no-play treatment unresolved.",
    ),
    FieldMapping(
        "redZoneTdRate",
        CLASS_REQUIRES_PBP,
        "red-zone trips plus drive result/touchdown events",
        "Red-zone touchdown drives divided by redZoneTrips.",
        "TD attribution and drive result source must be settled.",
    ),
)

OPTIONAL_FIELD_MAPPINGS: tuple[OptionalFieldMapping, ...] = tuple(
    OptionalFieldMapping(
        field,
        "deferred_not_blocking",
        "Fantasy-point splits do not block the real Teamstate lane; movement v1 drops them and forecast-features v1 forbids them.",
    )
    for field in (
        "fantasyPointsForQB",
        "fantasyPointsForRB",
        "fantasyPointsForWR",
        "fantasyPointsForTE",
        "fantasyPointsAllowedQB",
        "fantasyPointsAllowedRB",
        "fantasyPointsAllowedWR",
        "fantasyPointsAllowedTE",
    )
)


def _package_version(package_name: str) -> str | None:
    try:
        return importlib.metadata.version(package_name)
    except importlib.metadata.PackageNotFoundError:
        return None


def _columns_from_table(table: Any) -> list[str]:
    columns = getattr(table, "columns", None)
    if columns is not None:
        return sorted(str(column) for column in columns)
    if isinstance(table, list) and table and isinstance(table[0], dict):
        return sorted(str(column) for column in table[0].keys())
    return []


def _fetch_nflreadpy_columns(module: Any, method_name: str) -> tuple[str, list[str]]:
    if not hasattr(module, method_name):
        return f"unavailable: nflreadpy has no {method_name}", []
    method = getattr(module, method_name)
    try:
        if method_name == "load_team_stats":
            table = method([SEASON], summary_level="week")
        else:
            table = method([SEASON])
    except Exception as exc:  # noqa: BLE001 - probe reports source-access failures without failing import.
        return f"failed: {type(exc).__name__}: {exc}", []
    return "succeeded", _columns_from_table(table)


def probe_sources(fetch_schemas: bool = False) -> list[SourceProbe]:
    nflreadpy_spec = importlib.util.find_spec("nflreadpy")
    nflreadpy_available = nflreadpy_spec is not None
    nflreadpy_version = _package_version("nflreadpy") if nflreadpy_available else None
    nflreadpy_module = importlib.import_module("nflreadpy") if nflreadpy_available else None

    team_fetch_status = "not_attempted"
    team_columns: list[str] = []
    pbp_fetch_status = "not_attempted"
    pbp_columns: list[str] = []

    if fetch_schemas and nflreadpy_module is not None:
        team_fetch_status, team_columns = _fetch_nflreadpy_columns(
            nflreadpy_module,
            "load_team_stats",
        )
        pbp_fetch_status, pbp_columns = _fetch_nflreadpy_columns(
            nflreadpy_module,
            "load_pbp",
        )

    return [
        SourceProbe(
            source_name="nflreadpy / nflverse weekly team stats",
            source_type="nflverse",
            retrieval_method='nflreadpy.load_team_stats([2024], summary_level="week")',
            available_without_fetch=nflreadpy_available,
            package_version=nflreadpy_version,
            fetch_attempted=fetch_schemas,
            fetch_status=team_fetch_status,
            columns=team_columns,
            limitations=[
                "Weekly team stats alone do not settle neutral-script, EPA, success, drives, red-zone trips, or pressure-rate requirements.",
                "A later source-fetch PR must record retrieval date, source version, and raw source refs.",
            ],
        ),
        SourceProbe(
            source_name="nflfastR / nflverse play-by-play via nflreadpy if exposed",
            source_type="nflverse",
            retrieval_method="nflreadpy.load_pbp([2024]) or selected deterministic nflverse play-by-play retrieval path",
            available_without_fetch=nflreadpy_available,
            package_version=nflreadpy_version,
            fetch_attempted=fetch_schemas,
            fetch_status=pbp_fetch_status,
            columns=pbp_columns,
            limitations=[
                "The accepted play-by-play loader and EPA/source version remain governance decisions.",
                "The probe must not commit real rows; PR C would need a validation report and lineage manifest before candidate emission.",
            ],
        ),
        SourceProbe(
            source_name="existing offline fixture / FORGE proof-of-path data",
            source_type="fixture_or_proof_reference",
            retrieval_method="committed repo files and existing FORGE audits only",
            available_without_fetch=True,
            package_version=None,
            fetch_attempted=False,
            fetch_status="context_only_not_full_coverage",
            columns=[],
            limitations=[
                "Insufficient for full governed 2024 all-32 coverage.",
                "Must not be promoted by path inference or used as real all-32 source support.",
            ],
        ),
    ]


def build_payload(fetch_schemas: bool = False) -> dict[str, Any]:
    return {
        "report": "team_week_raw_v0_2024_source_probe",
        "season": SEASON,
        "generatedAt": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "mode": "dry_run_schema_mapping_only",
        "guardrails": [
            "no real 2024 artifact emitted",
            "no promoted output/export",
            "no governed_real_data claim",
            "no Teamstate or PPM changes",
            "no invented values or placeholder field fills",
        ],
        "candidatePathsNotCreated": {
            "artifact": CANDIDATE_ARTIFACT_PATH,
            "validationReport": CANDIDATE_VALIDATION_REPORT_PATH,
            "lineageManifest": LINEAGE_MANIFEST_PATH,
        },
        "sources": [asdict(source) for source in probe_sources(fetch_schemas=fetch_schemas)],
        "requiredFieldMappings": [asdict(mapping) for mapping in REQUIRED_FIELD_MAPPINGS],
        "optionalFieldMappings": [asdict(mapping) for mapping in OPTIONAL_FIELD_MAPPINGS],
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines: list[str] = [
        "# team_week_raw_v0 2024 source probe",
        "",
        "## Status",
        "",
        "Dry-run schema mapping only. This report does not create, emit, promote, or validate the future real 2024 artifact.",
        "",
        f"Spec reference: `{SPEC_PATH}`.",
        "",
        "Candidate paths named by the spec remain future-only and were not created by this probe:",
        "",
        f"- artifact: `{payload['candidatePathsNotCreated']['artifact']}`",
        f"- validation report: `{payload['candidatePathsNotCreated']['validationReport']}`",
        f"- lineage manifest: `{payload['candidatePathsNotCreated']['lineageManifest']}`",
        "",
        "## Source availability",
        "",
        "| Source | Type | Retrieval method | Available without fetch | Package version | Fetch status | Limitations |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for source in payload["sources"]:
        limitations = "<br>".join(source["limitations"])
        source_row = {
            **source,
            "package_version": source["package_version"] or "not_available",
            "limitations": limitations,
        }
        lines.append(
            "| {source_name} | {source_type} | `{retrieval_method}` | {available_without_fetch} | {package_version} | {fetch_status} | {limitations} |".format(
                **source_row
            )
        )
    lines.extend(
        [
            "",
            "## Required field mapping",
            "",
            "| Field | Classification | Source basis | Deterministic rule needed | Unresolved/blocker |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for mapping in payload["requiredFieldMappings"]:
        lines.append(
            "| `{field}` | `{classification}` | {source_basis} | {deterministic_rule_needed} | {unresolved_or_blocked} |".format(
                **mapping
            )
        )
    lines.extend(
        [
            "",
            "## Optional/deferred fantasy-point split fields",
            "",
            "These fields do not block the real Teamstate lane because movement v1 drops them and forecast-features v1 forbids them.",
            "",
            "| Field | Status | Note |",
            "| --- | --- | --- |",
        ]
    )
    for mapping in payload["optionalFieldMappings"]:
        lines.append("| `{field}` | `{status}` | {note} |".format(**mapping))
    lines.extend(
        [
            "",
            "## Blockers and unresolved decisions",
            "",
            "- `pressureRateAllowed` likely requires an additional charting/provider source or explicit contract deferral.",
            "- EPA and success-rate values require a selected source version and documented inclusion rules.",
            "- Neutral-script filters, explosive-play thresholds, and seconds-per-play clock handling remain unresolved.",
            "- Drive counting, points-per-drive, red-zone trips, and red-zone touchdown rate require drive rules and play inclusion rules.",
            "- The full Week 1-18 regular-season window vs fantasy-aligned window decision remains unresolved.",
            "- Retrieval metadata must include source name, source type, retrieval method, package/library version where available, retrieval date, dataset identifier or URL where available, transform code path, and validation report path candidate.",
            "",
            "## PR C validation plan",
            "",
            "Before PR C emits any non-promoted candidate artifact, it must validate:",
            "",
            "- all 32 NFL teams for the selected window;",
            "- expected weeks/window;",
            "- duplicate team-week rows;",
            "- valid team/opponent codes and reciprocal opponent consistency;",
            "- bounded rates;",
            "- finite numeric required fields;",
            "- explicit null/deferred fields;",
            "- source refs, retrieval metadata, validation report, and lineage manifest.",
            "",
            "No artifact can be marked `governed_real_data` from this probe. Governance requires explicit markers and promotion review; path inference is not governance.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Dry-run source/schema probe for future team_week_raw_v0 2024 artifact."
    )
    parser.add_argument(
        "--fetch-schemas",
        action="store_true",
        help="Attempt source schema fetches and print column names; does not print or write rows.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON instead of Markdown.",
    )
    args = parser.parse_args()

    payload = build_payload(fetch_schemas=args.fetch_schemas)
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(render_markdown(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

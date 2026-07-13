"""Build the `formation_summary_v0` 2024 REG team-season candidate (TIBER-Data #214).

Source-backed, candidate-only build. It writes ONLY under candidate paths and never
promotes: no `exports/promoted/**`, no `governed_real_data`, no Teamstate/Fantasy/
Forecast wiring. Semantics are locked by `docs/specs/formation-summary-v0-source-boundary.md`
(#208/#209), the live verification recorded in #214, and the `team_week_raw_v0`
precedent (`scripts/build_team_week_raw_v0_2024_candidate.py`):

- Grain: exactly `team_season`; one row per canonical NFL team.
- Qualifying denominator: 2024 REG rows with non-null `posteam`,
  `play_type in {"pass", "run"}`, null-safe exclusion of `two_point_attempt == 1`
  and `aborted_play == 1`. A null `two_point_attempt`/`aborted_play` is NOT itself
  an exclusion.
- Alignment vocabulary: exactly `shotgun` / `non_shotgun` /
  `unknown_or_unclassified_alignment`. `shotgun == 1` -> shotgun; `shotgun == 0` ->
  non_shotgun; null/missing -> unknown bucket. `under_center` is never emitted,
  derived, displayed, or aliased (spec section 3.3 hard block).
- Pass/run split inside each alignment bucket uses `qb_dropback`, never `play_type`
  (spec section 3.1b): a QB scramble (`play_type == "run"`, `qb_dropback == 1`) is a
  pass play. Any qualifying play with null `qb_dropback` fail-closes the affected
  row's split fields (null-blocked, machine-readable note), never guessed.
- Success rate is TIBER's own down/distance rule (mirrors
  `src/team_state/compute.py::is_success` exactly), NOT nflverse's native `success`
  column. The fork is disclosed in metadata (spec section 3.2).
- Sample thresholds (spec section 6.1 / #209): a team-season row needs >= 250
  qualifying plays to be emitted at all; alignment-bucket efficiency fields
  (`*_epa_per_play`, `*_success_rate`) need >= 100 bucket plays, else they are
  null-blocked with a typed sample note — never a manufactured zero.
- If `unknown_or_unclassified_alignment_plays` exceeds 10% of `offensive_plays`
  for a row, the row carries an explicit uncertainty flag (spec section 7).
- Reconciliation must hold exactly per row:
  shotgun + non_shotgun + unknown == offensive_plays.
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import io
import json
import sys
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import httpx
import polars as pl

SEASON = 2024
ARTIFACT_NAME = "formation_summary_v0"
ARTIFACT_VERSION = "0.1.0"
GRAIN = "team_season"
SEASON_TYPE = "REG"

CANDIDATE_ARTIFACT_PATH = Path(
    "exports/candidates/formation_summary/formation_summary_v0_2024_real_source_candidate.json"
)
CANDIDATE_VALIDATION_REPORT_PATH = Path(
    "exports/candidates/formation_summary/"
    "formation_summary_v0_2024_real_source_candidate.validation.json"
)
LINEAGE_MANIFEST_PATH = Path(
    "data/manifests/formation_summary_v0_2024_real_source_candidate.manifest.json"
)
SCHEMA_PATH = Path("schemas/formation_summary_v0.schema.json")
TRANSFORM_CODE_PATH = "scripts/build_formation_summary_v0_2024_candidate.py"
SPEC_DOC_PATH = "docs/specs/formation-summary-v0-source-boundary.md"
BUILD_COMMAND = "python scripts/build_formation_summary_v0_2024_candidate.py"

TEAM_CODE_CANONICAL_MAP = {"LA": "LAR"}
CANONICAL_TEAMS = frozenset(
    {
        "ARI", "ATL", "BAL", "BUF", "CAR", "CHI", "CIN", "CLE", "DAL", "DEN",
        "DET", "GB", "HOU", "IND", "JAX", "KC", "LAC", "LAR", "LV", "MIA",
        "MIN", "NE", "NO", "NYG", "NYJ", "PHI", "PIT", "SEA", "SF", "TB",
        "TEN", "WAS",
    }
)

QUALIFYING_PLAY_TYPES = frozenset({"pass", "run"})

ALIGNMENT_SHOTGUN = "shotgun"
ALIGNMENT_NON_SHOTGUN = "non_shotgun"
ALIGNMENT_UNKNOWN = "unknown_or_unclassified_alignment"
ALIGNMENT_VOCABULARY = (ALIGNMENT_SHOTGUN, ALIGNMENT_NON_SHOTGUN, ALIGNMENT_UNKNOWN)
# Never emitted; the validator greps the serialized artifact for it (spec section 7).
FORBIDDEN_ALIGNMENT_LABEL = "under_" + "center"

MIN_ROW_OFFENSIVE_PLAYS = 250
MIN_BUCKET_PLAYS_FOR_EFFICIENCY = 100
UNKNOWN_SHARE_UNCERTAINTY_THRESHOLD = 0.10

# Columns the build refuses to run without (fail closed, spec section 7).
REQUIRED_SOURCE_COLUMNS = (
    "season", "season_type", "posteam", "play_type", "two_point_attempt",
    "aborted_play", "shotgun", "qb_dropback", "epa", "down", "ydstogo",
    "yards_gained",
)

DENOMINATOR_RULE = (
    f"{SEASON} {SEASON_TYPE} play-by-play rows with non-null posteam and play_type in "
    "{pass, run}; two_point_attempt == 1 and aborted_play == 1 rows are excluded "
    "null-safely (a null flag is not itself an exclusion). Kneels, spikes, no-plays, "
    "penalty-only/no-snap rows, special teams, two-point attempts, and aborted plays "
    "are all outside this denominator. This is the team_week_raw_v0 competitivePlays-"
    "equivalent (spec section 3.1a), extended with the explicit aborted_play exclusion "
    "verified live in #214 (111 aborted rows inside play_type pass/run in the 2024 "
    "REG slice)."
)
PASS_RUN_SPLIT_RULE = (
    "Pass vs. run inside each alignment bucket is classified by qb_dropback "
    "(1 -> pass, 0 -> run), never by play_type, so valid QB scrambles stay in the "
    "pass split (spec section 3.1b). If any qualifying play for a team-season has a "
    "null qb_dropback, that row's shotgun/non_shotgun pass/run split fields are "
    "null-blocked (fail closed) with a machine-readable sample note."
)
ALIGNMENT_RULE = (
    "shotgun == 1 -> shotgun; shotgun == 0 -> non_shotgun; null/missing shotgun -> "
    "unknown_or_unclassified_alignment. non_shotgun means shotgun-negative only: it "
    "may silently include pistol formations if the source does not separately flag "
    "them (no pistol-disambiguation field was found in the 2024 source, #214). It is "
    "not an under-center claim and must not be read as one. Any other observed "
    "shotgun value aborts the build (fail closed)."
)
SUCCESS_DEFINITION = {
    "name": "tiber_team_state_distance_success",
    "rule": (
        "yards_gained >= 40% of ydstogo on 1st down, >= 60% on 2nd down, >= 100% on "
        "3rd/4th down; a play with null down, ydstogo, or yards_gained counts as "
        "not-successful (mirrors fill_null(False) in src/team_state/compute.py)."
    ),
    "codeReference": "src/team_state/compute.py (is_success expression)",
    "disclosure": (
        "This is TIBER's existing team_state success definition computed explicitly "
        "from down/ydstogo/yards_gained. It is NOT nflverse's native `success` "
        "column; that provider-modeled field is not consumed by this artifact "
        "(spec section 3.2 anti-drift rule)."
    ),
}
EPA_DISCLOSURE = (
    "epa is nflverse's own modeled advanced stat (provider_model_derived), not a raw "
    "NFL measurement. *_epa_per_play averages the non-null epa values on qualifying "
    "plays in the alignment bucket and is null-blocked below the declared sample "
    "threshold; a missing value is null, never zero."
)
SOURCE_MUTABILITY_NOTE = (
    "sourceUrlOrDatasetId is a mutable nflverse rolling release asset; no immutable "
    "release tag/ref is exposed at retrieval, so immutableSourceRef is not set. The "
    "sha256 checksum pins the exact source bytes consumed at retrievalTimestamp so a "
    "future rebuild can detect upstream drift; the upstream URL itself remains mutable."
)

PROVENANCE_REAL = "candidate_real_data"
PROVENANCE_FIXTURE = "candidate_fixture_data"
ALLOWED_PROVENANCE_STATUSES = frozenset({PROVENANCE_REAL, PROVENANCE_FIXTURE})
ROW_PROVENANCE_STATUS = "candidate_source_backed_not_promoted"

RATE_FIELDS: tuple[str, ...] = (
    "shotgun_rate", "non_shotgun_rate", "unknown_alignment_rate",
    "shotgun_pass_rate", "shotgun_run_rate", "non_shotgun_pass_rate",
    "non_shotgun_run_rate", "shotgun_success_rate", "non_shotgun_success_rate",
)
SPLIT_RATE_FIELDS: tuple[str, ...] = (
    "shotgun_pass_rate", "shotgun_run_rate", "non_shotgun_pass_rate", "non_shotgun_run_rate",
)
EFFICIENCY_FIELDS_BY_BUCKET: dict[str, tuple[str, str]] = {
    ALIGNMENT_SHOTGUN: ("shotgun_epa_per_play", "shotgun_success_rate"),
    ALIGNMENT_NON_SHOTGUN: ("non_shotgun_epa_per_play", "non_shotgun_success_rate"),
}

NOTE_SAMPLE_THRESHOLD_NOT_MET = "sample_threshold_not_met"
NOTE_DROPBACK_SPLIT_BLOCKED = "dropback_split_blocked"
NOTE_EMPTY_ALIGNMENT_BUCKET = "empty_alignment_bucket"
NOTE_NO_EPA_VALUES = "no_epa_values"
NOTE_EPA_NULL_ROWS_IGNORED = "epa_null_rows_ignored"
NOTE_HIGH_UNKNOWN_ALIGNMENT_SHARE = "high_unknown_alignment_share"

REQUIRED_RETRIEVAL_KEYS = (
    "sourceName", "sourceType", "retrievalMethod", "retrievalTimestamp",
    "packageVersion", "sourceUrlOrDatasetId", "transformCodePath", "sourceRefs",
)


# ---------------------------------------------------------------------------
# Pure play-classification helpers
# ---------------------------------------------------------------------------

def canon_team(code: str | None) -> str | None:
    if code is None:
        return None
    return TEAM_CODE_CANONICAL_MAP.get(code, code)


def flag_is_set(value: Any) -> bool:
    """Null-safe binary-indicator test: only an explicit truthy 1 counts as set.

    None (null/missing) is NOT set — a null two_point_attempt or aborted_play must
    never exclude a play by itself (spec section 3.1 null-safe guard).
    """
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    return value == 1


def is_qualifying_play(row: dict[str, Any]) -> bool:
    """The formation-eligible denominator test (spec sections 3.1/3.1a + #214).

    play_type membership handles kneels, spikes, no-plays, penalty-only rows, and
    special teams (all outside {pass, run}); two-point attempts and aborted plays
    are excluded explicitly and null-safely because they DO appear inside
    play_type in {pass, run} (111 aborted rows in the 2024 REG slice, #214).
    """
    if row.get("posteam") is None:
        return False
    if row.get("play_type") not in QUALIFYING_PLAY_TYPES:
        return False
    if flag_is_set(row.get("two_point_attempt")):
        return False
    if flag_is_set(row.get("aborted_play")):
        return False
    return True


def classify_alignment(row: dict[str, Any]) -> str:
    """Three-bucket alignment split, partitioned strictly by the observed value.

    The unknown bucket is ONLY for null/missing shotgun (spec section 3.3); an
    unexpected non-binary value is a source-contract violation and aborts the
    build rather than being guessed into a bucket.
    """
    shotgun = row.get("shotgun")
    if shotgun is None:
        return ALIGNMENT_UNKNOWN
    if shotgun == 1:
        return ALIGNMENT_SHOTGUN
    if shotgun == 0:
        return ALIGNMENT_NON_SHOTGUN
    raise ValueError(
        f"Unexpected shotgun value {shotgun!r} on a qualifying play; the alignment "
        "vocabulary only defines 1, 0, and null. Build fails closed."
    )


def is_tiber_success(row: dict[str, Any]) -> bool:
    """TIBER team_state down/distance success rule, computed explicitly.

    Mirrors src/team_state/compute.py exactly, including fill_null(False): a play
    with null down/ydstogo/yards_gained is not-successful, never a guess. This is
    deliberately NOT nflverse's native `success` column (spec section 3.2).
    """
    down = row.get("down")
    ydstogo = row.get("ydstogo")
    yards_gained = row.get("yards_gained")
    if down is None or ydstogo is None or yards_gained is None:
        return False
    if down == 1:
        return yards_gained >= ydstogo * 0.4
    if down == 2:
        return yards_gained >= ydstogo * 0.6
    if down in (3, 4):
        return yards_gained >= ydstogo
    return False


def safe_ratio(numerator: float, denominator: float) -> float | None:
    if not denominator:
        return None
    return numerator / denominator


def _round(value: float | None, digits: int = 6) -> float | None:
    if value is None:
        return None
    return round(value, digits)


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------

class AlignmentBucketStats:
    def __init__(self) -> None:
        self.plays = 0
        self.pass_plays = 0
        self.run_plays = 0
        self.dropback_null_rows = 0
        self.epa_values: list[float] = []
        self.epa_null_rows = 0
        self.success_count = 0


class TeamSeasonStats:
    def __init__(self) -> None:
        self.qualifying_plays = 0
        self.buckets: dict[str, AlignmentBucketStats] = {
            alignment: AlignmentBucketStats() for alignment in ALIGNMENT_VOCABULARY
        }
        self.two_point_plays = 0
        self.aborted_plays_excluded = 0


def aggregate_season(pbp_rows: list[dict[str, Any]]) -> dict[str, TeamSeasonStats]:
    stats_by_team: dict[str, TeamSeasonStats] = defaultdict(TeamSeasonStats)
    for row in pbp_rows:
        team = canon_team(row.get("posteam"))
        if team is None:
            continue
        if row.get("play_type") not in QUALIFYING_PLAY_TYPES:
            continue
        stats = stats_by_team[team]
        # Tracked-exclusion counts are independent tallies over pass/run rows (a row
        # flagged as both two-point and aborted increments both); the qualifying
        # test itself excludes on either flag.
        two_point = flag_is_set(row.get("two_point_attempt"))
        aborted = flag_is_set(row.get("aborted_play"))
        if two_point:
            stats.two_point_plays += 1
        if aborted:
            stats.aborted_plays_excluded += 1
        if not is_qualifying_play(row):
            continue
        stats.qualifying_plays += 1
        bucket = stats.buckets[classify_alignment(row)]
        bucket.plays += 1

        dropback = row.get("qb_dropback")
        if dropback is None:
            bucket.dropback_null_rows += 1
        elif flag_is_set(dropback):
            bucket.pass_plays += 1
        else:
            bucket.run_plays += 1

        epa = row.get("epa")
        if epa is None:
            bucket.epa_null_rows += 1
        else:
            bucket.epa_values.append(float(epa))

        if is_tiber_success(row):
            bucket.success_count += 1
    return dict(stats_by_team)


# ---------------------------------------------------------------------------
# Row construction
# ---------------------------------------------------------------------------

def build_team_row(
    *, season: int, team: str, stats: TeamSeasonStats, source_refs: list[str]
) -> tuple[dict[str, Any], dict[str, Any]]:
    offensive_plays = stats.qualifying_plays
    shotgun = stats.buckets[ALIGNMENT_SHOTGUN]
    non_shotgun = stats.buckets[ALIGNMENT_NON_SHOTGUN]
    unknown = stats.buckets[ALIGNMENT_UNKNOWN]
    sample_notes: list[dict[str, Any]] = []

    dropback_null_rows_total = sum(
        stats.buckets[alignment].dropback_null_rows for alignment in ALIGNMENT_VOCABULARY
    )
    dropback_split_blocked = dropback_null_rows_total > 0

    def bucket_split(bucket: AlignmentBucketStats, prefix: str) -> dict[str, float | None]:
        if dropback_split_blocked:
            return {f"{prefix}_pass_rate": None, f"{prefix}_run_rate": None}
        if bucket.plays == 0:
            sample_notes.append(
                {
                    "code": NOTE_EMPTY_ALIGNMENT_BUCKET,
                    "fields": [f"{prefix}_pass_rate", f"{prefix}_run_rate"],
                    "detail": f"No qualifying {prefix} plays; split rates are null, not zero.",
                }
            )
            return {f"{prefix}_pass_rate": None, f"{prefix}_run_rate": None}
        return {
            f"{prefix}_pass_rate": _round(safe_ratio(bucket.pass_plays, bucket.plays)),
            f"{prefix}_run_rate": _round(safe_ratio(bucket.run_plays, bucket.plays)),
        }

    if dropback_split_blocked:
        sample_notes.append(
            {
                "code": NOTE_DROPBACK_SPLIT_BLOCKED,
                "fields": list(SPLIT_RATE_FIELDS),
                "detail": (
                    f"{dropback_null_rows_total} qualifying play(s) had a null "
                    "qb_dropback; pass/run split fields are null-blocked for this row "
                    "(fail closed, spec section 3.1b) rather than guessed from play_type."
                ),
                "dropbackNullRows": dropback_null_rows_total,
            }
        )

    split_fields: dict[str, float | None] = {}
    split_fields.update(bucket_split(shotgun, ALIGNMENT_SHOTGUN))
    split_fields.update(bucket_split(non_shotgun, ALIGNMENT_NON_SHOTGUN))

    efficiency_fields: dict[str, float | None] = {}
    for alignment, (epa_field, success_field) in EFFICIENCY_FIELDS_BY_BUCKET.items():
        bucket = stats.buckets[alignment]
        if bucket.plays < MIN_BUCKET_PLAYS_FOR_EFFICIENCY:
            efficiency_fields[epa_field] = None
            efficiency_fields[success_field] = None
            sample_notes.append(
                {
                    "code": NOTE_SAMPLE_THRESHOLD_NOT_MET,
                    "fields": [epa_field, success_field],
                    "detail": (
                        f"{alignment} bucket has {bucket.plays} qualifying play(s), "
                        f"below the {MIN_BUCKET_PLAYS_FOR_EFFICIENCY}-play efficiency "
                        "threshold (spec section 6.1); efficiency fields are "
                        "null-blocked, never a manufactured zero."
                    ),
                    "bucketPlays": bucket.plays,
                    "requiredPlays": MIN_BUCKET_PLAYS_FOR_EFFICIENCY,
                }
            )
            continue
        if bucket.epa_values:
            efficiency_fields[epa_field] = _round(
                sum(bucket.epa_values) / len(bucket.epa_values)
            )
            if bucket.epa_null_rows:
                sample_notes.append(
                    {
                        "code": NOTE_EPA_NULL_ROWS_IGNORED,
                        "fields": [epa_field],
                        "detail": (
                            f"{bucket.epa_null_rows} qualifying {alignment} play(s) had "
                            "null epa and were excluded from the epa-per-play numerator "
                            "and denominator."
                        ),
                        "epaNullRows": bucket.epa_null_rows,
                    }
                )
        else:
            efficiency_fields[epa_field] = None
            sample_notes.append(
                {
                    "code": NOTE_NO_EPA_VALUES,
                    "fields": [epa_field],
                    "detail": (
                        f"No non-null epa values on {alignment} plays; "
                        "epa-per-play is null, not zero."
                    ),
                }
            )
        efficiency_fields[success_field] = _round(
            safe_ratio(bucket.success_count, bucket.plays)
        )

    unknown_share = safe_ratio(unknown.plays, offensive_plays)
    uncertainty_flag = (
        unknown_share is not None and unknown_share > UNKNOWN_SHARE_UNCERTAINTY_THRESHOLD
    )
    if uncertainty_flag:
        sample_notes.append(
            {
                "code": NOTE_HIGH_UNKNOWN_ALIGNMENT_SHARE,
                "fields": ["unknown_alignment_rate"],
                "detail": (
                    f"unknown_or_unclassified_alignment share {unknown_share:.4f} exceeds "
                    f"the {UNKNOWN_SHARE_UNCERTAINTY_THRESHOLD:.0%} high-uncertainty "
                    "threshold (spec section 7); alignment rates on this row must not be "
                    "read as fully resolved."
                ),
            }
        )

    row = {
        "season": season,
        "grain": GRAIN,
        "team": team,
        "offensive_plays": offensive_plays,
        "shotgun_plays": shotgun.plays,
        "non_shotgun_plays": non_shotgun.plays,
        "unknown_or_unclassified_alignment_plays": unknown.plays,
        "shotgun_rate": _round(safe_ratio(shotgun.plays, offensive_plays)),
        "non_shotgun_rate": _round(safe_ratio(non_shotgun.plays, offensive_plays)),
        "unknown_alignment_rate": _round(unknown_share),
        **split_fields,
        "two_point_plays": stats.two_point_plays,
        "aborted_plays_excluded": stats.aborted_plays_excluded,
        **efficiency_fields,
        "unknown_alignment_uncertainty_flag": uncertainty_flag,
        "sample_notes": sample_notes,
        "sourceRefs": source_refs,
        "provenanceStatus": ROW_PROVENANCE_STATUS,
    }
    diagnostics = {
        "team": team,
        "offensivePlays": offensive_plays,
        "dropbackSplitBlocked": dropback_split_blocked,
        "dropbackNullRows": dropback_null_rows_total,
        "twoPointPlaysExcluded": stats.two_point_plays,
        "abortedPlaysExcluded": stats.aborted_plays_excluded,
        "unknownAlignmentPlays": unknown.plays,
        "epaNullRows": {
            alignment: stats.buckets[alignment].epa_null_rows
            for alignment in ALIGNMENT_VOCABULARY
        },
    }
    return row, diagnostics


def build_rows(
    pbp_rows: list[dict[str, Any]], source_refs: list[str]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Returns (rows, diagnostics, suppressed_rows).

    Team-seasons below MIN_ROW_OFFENSIVE_PLAYS are suppressed entirely (spec
    section 6.1) and recorded machine-readably, never emitted with thin-sample
    rates.
    """
    stats_by_team = aggregate_season(pbp_rows)
    rows: list[dict[str, Any]] = []
    diagnostics: list[dict[str, Any]] = []
    suppressed: list[dict[str, Any]] = []
    for team in sorted(stats_by_team):
        stats = stats_by_team[team]
        if stats.qualifying_plays < MIN_ROW_OFFENSIVE_PLAYS:
            suppressed.append(
                {
                    "team": team,
                    "offensivePlays": stats.qualifying_plays,
                    "requiredPlays": MIN_ROW_OFFENSIVE_PLAYS,
                    "reason": (
                        "team-season qualifying-play count below the minimum row "
                        "emission threshold (spec section 6.1); row suppressed, not "
                        "emitted with thin-sample rates"
                    ),
                }
            )
            continue
        row, diag = build_team_row(
            season=SEASON, team=team, stats=stats, source_refs=source_refs
        )
        rows.append(row)
        diagnostics.append(diag)
    return rows, diagnostics, suppressed


# ---------------------------------------------------------------------------
# Retrieval
# ---------------------------------------------------------------------------

def _package_version(package_name: str) -> str | None:
    try:
        return importlib.metadata.version(package_name)
    except importlib.metadata.PackageNotFoundError:
        return None


def _nflverse_data_url(path: str) -> str:
    from nflreadpy.downloader import NflverseDownloader

    base_url = NflverseDownloader.BASE_URLS["nflverse-data"]
    if not path.endswith((".parquet", ".csv")):
        path = f"{path}.parquet"
    return urljoin(base_url, path)


def _fetch_source_bytes(url: str) -> bytes:
    """Fetch the exact source bytes consumed, so the recorded sha256 pins them."""
    user_agent = f"nflverse/nflreadpy {_package_version('nflreadpy')}"
    with httpx.Client(
        follow_redirects=True, timeout=180, headers={"User-Agent": user_agent}
    ) as client:
        response = client.get(url)
        response.raise_for_status()
        return response.content


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def retrieve_pbp() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Download 2024 nflverse pbp, checksum the consumed bytes, filter to REG.

    Same retrieval pattern as scripts/build_team_week_raw_v0_2024_candidate.py:
    httpx GET against the release-asset URL nflreadpy.load_pbp([2024]) resolves,
    sha256 over exactly the bytes parsed. Fails closed if any required column is
    absent from the retrieved schema.
    """
    retrieval_timestamp = datetime.now(UTC).replace(microsecond=0).isoformat()
    url = _nflverse_data_url(f"pbp/play_by_play_{SEASON}")
    content = _fetch_source_bytes(url)
    checksum = _sha256(content)
    table = pl.read_parquet(io.BytesIO(content))

    missing_columns = [
        column for column in REQUIRED_SOURCE_COLUMNS if column not in table.columns
    ]
    if missing_columns:
        raise ValueError(
            f"Source schema is missing required columns {missing_columns}; "
            "build fails closed (spec section 7)."
        )

    reg = table.filter((pl.col("season_type") == SEASON_TYPE) & (pl.col("season") == SEASON))
    if reg.height == 0:
        raise ValueError(
            f"No {SEASON} {SEASON_TYPE} rows found in the retrieved source; "
            "build fails closed."
        )
    source_info = {
        "sourceName": "nflverse play-by-play",
        "sourceType": "nflverse",
        "retrievalMethod": (
            f"httpx GET {url} (same nflverse release asset as "
            f"nflreadpy.load_pbp([{SEASON}])), parsed via polars.read_parquet, "
            f"filtered to season_type == {SEASON_TYPE!r} and season == {SEASON}"
        ),
        "retrievalTimestamp": retrieval_timestamp,
        "packageVersion": _package_version("nflreadpy"),
        "polarsVersion": _package_version("polars"),
        "sourceUrlOrDatasetId": url,
        "transformCodePath": TRANSFORM_CODE_PATH,
        "sourceRefs": [f"nflverse-data:pbp/play_by_play_{SEASON}"],
        "checksum": {"algorithm": "sha256", "value": checksum},
        "immutableSourceRef": None,
        "mutabilityNote": SOURCE_MUTABILITY_NOTE,
        "buildCommand": BUILD_COMMAND,
        "sourceRowCount": table.height,
        "regularSeasonRowCount": reg.height,
        "sourceColumnCount": table.width,
    }
    return reg.to_dicts(), source_info


# ---------------------------------------------------------------------------
# Coverage / metadata / envelope
# ---------------------------------------------------------------------------

def build_coverage(
    rows: list[dict[str, Any]], suppressed: list[dict[str, Any]]
) -> dict[str, Any]:
    present_teams = sorted({row["team"] for row in rows})
    missing_teams = sorted(CANONICAL_TEAMS - set(present_teams))
    unexpected_teams = sorted(set(present_teams) - CANONICAL_TEAMS)
    return {
        "season": SEASON,
        "expectedTeams": sorted(CANONICAL_TEAMS),
        "presentTeams": present_teams,
        "missingTeams": missing_teams,
        "unexpectedTeams": unexpected_teams,
        "teamsCovered": len(present_teams),
        "isFullLeague": not missing_teams and not unexpected_teams,
        "suppressedTeams": sorted(entry["team"] for entry in suppressed),
        # Empty when the build succeeded: retrieval fails closed on any missing
        # required column, so a successful build implies none were missing.
        "missingFields": [],
    }


def build_metadata(
    *,
    rows: list[dict[str, Any]],
    diagnostics: list[dict[str, Any]],
    suppressed: list[dict[str, Any]],
    input_sources_meta: list[dict[str, Any]],
    provenance_status: str = PROVENANCE_REAL,
) -> dict[str, Any]:
    if provenance_status not in ALLOWED_PROVENANCE_STATUSES:
        raise ValueError(f"Unrecognized provenanceStatus {provenance_status!r}")
    coverage = build_coverage(rows, suppressed)
    dropback_blocked_rows = [d for d in diagnostics if d["dropbackSplitBlocked"]]
    qualifying_total = sum(d["offensivePlays"] for d in diagnostics)
    aborted_total = sum(d["abortedPlaysExcluded"] for d in diagnostics)
    two_point_total = sum(d["twoPointPlaysExcluded"] for d in diagnostics)
    unknown_total = sum(d["unknownAlignmentPlays"] for d in diagnostics)

    provenance_notes = [
        "Candidate-only artifact per TIBER-Data #214: written only under a candidate "
        "path, never promoted, and no Teamstate, Fantasy, or Forecast consumer is "
        "wired to it.",
        "Alignment vocabulary is exactly shotgun / non_shotgun / "
        "unknown_or_unclassified_alignment. non_shotgun is shotgun-negative only and "
        "may silently include pistol formations; it is not an under-center claim "
        "(spec section 3.3).",
        f"{aborted_total} aborted play(s) (aborted_play == 1) inside play_type "
        "{pass, run} were explicitly excluded from the qualifying denominator; a "
        "naive play_type-only denominator would have wrongly included them (#214).",
        f"{two_point_total} two-point attempt(s) inside play_type {{pass, run}} were "
        "excluded from the qualifying denominator and tracked separately.",
        f"{len(dropback_blocked_rows)} team-season row(s) had pass/run split fields "
        "null-blocked because one or more qualifying plays had a null qb_dropback "
        "(fail closed, spec section 3.1b).",
        "Success rates use TIBER's own team_state down/distance rule computed "
        "explicitly; nflverse's native `success` column is not consumed "
        "(spec section 3.2).",
        "No governance marker is set by this build. Promotion to governed status "
        "requires a separate, explicitly authorized human promotion review; build "
        "success and validation passing do not constitute governance.",
        f"Each source records a sha256 checksum over the exact bytes consumed. "
        f"{SOURCE_MUTABILITY_NOTE}",
    ]

    return {
        "seasonType": SEASON_TYPE,
        "grain": GRAIN,
        "denominatorRule": DENOMINATOR_RULE,
        "alignmentVocabulary": list(ALIGNMENT_VOCABULARY),
        "alignmentRule": ALIGNMENT_RULE,
        "passRunSplitRule": PASS_RUN_SPLIT_RULE,
        "successDefinition": SUCCESS_DEFINITION,
        "epaDisclosure": EPA_DISCLOSURE,
        "sampleThresholds": {
            "minOffensivePlaysPerRow": MIN_ROW_OFFENSIVE_PLAYS,
            "minBucketPlaysForEfficiency": MIN_BUCKET_PLAYS_FOR_EFFICIENCY,
            "unknownShareUncertaintyThreshold": UNKNOWN_SHARE_UNCERTAINTY_THRESHOLD,
        },
        "provenanceStatus": provenance_status,
        "provenanceNotes": provenance_notes,
        "inputSources": input_sources_meta,
        "coverage": coverage,
        "governance": {
            "governanceStatus": "ungoverned",
            "governanceSource": "not_set",
            "notes": (
                "No human promotion review has been performed. Build success and "
                "validation passing do not constitute governance."
            ),
        },
        "suppressedRows": suppressed,
        "blockedFieldRows": {
            "dropbackSplit(shotgun_pass_rate/shotgun_run_rate/"
            "non_shotgun_pass_rate/non_shotgun_run_rate)": [
                {"season": SEASON, "team": d["team"]} for d in dropback_blocked_rows
            ],
        },
        "buildDiagnostics": {
            "qualifyingPlaysTotal": qualifying_total,
            "abortedPlaysExcludedTotal": aborted_total,
            "twoPointPlaysExcludedTotal": two_point_total,
            "unknownAlignmentPlaysTotal": unknown_total,
            "dropbackSplitBlockedRowCount": len(dropback_blocked_rows),
            "suppressedRowCount": len(suppressed),
        },
        "validationReportPath": str(CANDIDATE_VALIDATION_REPORT_PATH),
        "lineageManifestPath": str(LINEAGE_MANIFEST_PATH),
    }


def build_artifact(
    rows: list[dict[str, Any]], metadata: dict[str, Any], source_refs: list[str]
) -> dict[str, Any]:
    return {
        "artifact": ARTIFACT_NAME,
        "artifactVersion": ARTIFACT_VERSION,
        "generatedAt": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "season": SEASON,
        "sourceArtifacts": source_refs,
        "metadata": metadata,
        "rows": rows,
    }


def build_lineage_manifest(source_infos: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "artifact": "formation_summary_v0_2024_real_source_candidate",
        "season": SEASON,
        "generatedAt": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "buildCommand": BUILD_COMMAND,
        "sources": source_infos,
        "validationReportPath": str(CANDIDATE_VALIDATION_REPORT_PATH),
        "lineageManifestPath": str(LINEAGE_MANIFEST_PATH),
        "governanceStatus": "ungoverned",
        "governanceSource": "not_set",
        "notes": [
            "This manifest documents source retrieval for a candidate artifact only.",
            "No governed_real_data claim is made or implied by this manifest.",
            "Promotion to governed status requires a separate, explicitly authorized "
            "human review.",
        ],
    }


# ---------------------------------------------------------------------------
# Validation report
# ---------------------------------------------------------------------------

def _check(name: str, passed: bool, details: Any) -> dict[str, Any]:
    return {"name": name, "passed": bool(passed), "details": details}


def build_validation_report(
    artifact: dict[str, Any],
    diagnostics: list[dict[str, Any]],
    lineage_manifest: dict[str, Any],
) -> dict[str, Any]:
    rows = artifact["rows"]
    metadata = artifact["metadata"]
    coverage = metadata["coverage"]
    checks: list[dict[str, Any]] = []

    checks.append(
        _check(
            "all_32_teams_present",
            not coverage["missingTeams"] and not coverage["unexpectedTeams"],
            {
                "missingTeams": coverage["missingTeams"],
                "unexpectedTeams": coverage["unexpectedTeams"],
                "teamsCovered": coverage["teamsCovered"],
            },
        )
    )

    teams = [row["team"] for row in rows]
    duplicate_teams = sorted({team for team in teams if teams.count(team) > 1})
    checks.append(
        _check("one_row_per_team", not duplicate_teams, {"duplicateTeams": duplicate_teams})
    )

    wrong_grain = [row["team"] for row in rows if row.get("grain") != GRAIN]
    checks.append(
        _check(
            "grain_is_team_season",
            not wrong_grain and metadata.get("grain") == GRAIN,
            {"rowsWithWrongGrain": wrong_grain, "metadataGrain": metadata.get("grain")},
        )
    )

    checks.append(
        _check(
            "season_type_is_reg",
            metadata.get("seasonType") == SEASON_TYPE,
            {"seasonType": metadata.get("seasonType")},
        )
    )

    reconciliation_failures = []
    for row in rows:
        total = (
            row["shotgun_plays"]
            + row["non_shotgun_plays"]
            + row["unknown_or_unclassified_alignment_plays"]
        )
        if total != row["offensive_plays"]:
            reconciliation_failures.append(
                {"team": row["team"], "bucketSum": total, "offensivePlays": row["offensive_plays"]}
            )
    checks.append(
        _check(
            "three_bucket_reconciliation_exact",
            not reconciliation_failures,
            {"failures": reconciliation_failures},
        )
    )

    vocabulary_ok = metadata.get("alignmentVocabulary") == list(ALIGNMENT_VOCABULARY)
    serialized = json.dumps(artifact)
    forbidden_label_found = FORBIDDEN_ALIGNMENT_LABEL in serialized
    checks.append(
        _check(
            "alignment_vocabulary_exact_no_forbidden_label",
            vocabulary_ok and not forbidden_label_found,
            {
                "alignmentVocabulary": metadata.get("alignmentVocabulary"),
                "forbiddenLabel": FORBIDDEN_ALIGNMENT_LABEL,
                "forbiddenLabelFound": forbidden_label_found,
            },
        )
    )

    out_of_bounds = []
    for row in rows:
        for field in RATE_FIELDS:
            value = row[field]
            if value is not None and not (0.0 <= value <= 1.0):
                out_of_bounds.append({"team": row["team"], "field": field, "value": value})
    checks.append(
        _check("rate_fields_bounded_0_1_or_null", not out_of_bounds, {"outOfBounds": out_of_bounds})
    )

    rate_mismatches = []
    for row in rows:
        expected = {
            "shotgun_rate": safe_ratio(row["shotgun_plays"], row["offensive_plays"]),
            "non_shotgun_rate": safe_ratio(row["non_shotgun_plays"], row["offensive_plays"]),
            "unknown_alignment_rate": safe_ratio(
                row["unknown_or_unclassified_alignment_plays"], row["offensive_plays"]
            ),
        }
        for field, expected_value in expected.items():
            actual = row[field]
            if expected_value is None or actual is None:
                if expected_value != actual:
                    rate_mismatches.append({"team": row["team"], "field": field})
                continue
            if abs(actual - expected_value) > 1e-6:
                rate_mismatches.append(
                    {"team": row["team"], "field": field, "actual": actual,
                     "expected": round(expected_value, 6)}
                )
    checks.append(
        _check("alignment_rates_match_counts", not rate_mismatches, {"mismatches": rate_mismatches})
    )

    unknown_bucket_missing = [
        row["team"]
        for row in rows
        if row.get("unknown_or_unclassified_alignment_plays") is None
        or row.get("unknown_alignment_rate") is None
    ]
    checks.append(
        _check(
            "unknown_bucket_explicit_even_when_zero",
            not unknown_bucket_missing,
            {"rowsMissingUnknownBucket": unknown_bucket_missing},
        )
    )

    diagnostics_by_team = {d["team"]: d for d in diagnostics}
    split_violations = []
    for row in rows:
        diag = diagnostics_by_team.get(row["team"], {})
        if diag.get("dropbackSplitBlocked"):
            leaked = [f for f in SPLIT_RATE_FIELDS if row[f] is not None]
            if leaked:
                split_violations.append({"team": row["team"], "nonNullBlockedFields": leaked})
            if not any(
                note["code"] == NOTE_DROPBACK_SPLIT_BLOCKED for note in row["sample_notes"]
            ):
                split_violations.append({"team": row["team"], "missingNote": True})
    checks.append(
        _check(
            "dropback_split_fail_closed",
            not split_violations,
            {"violations": split_violations},
        )
    )

    threshold_violations = []
    for row in rows:
        if row["offensive_plays"] < MIN_ROW_OFFENSIVE_PLAYS:
            threshold_violations.append(
                {"team": row["team"], "offensivePlays": row["offensive_plays"],
                 "violation": "row_below_min_offensive_plays"}
            )
        for alignment, (epa_field, success_field) in EFFICIENCY_FIELDS_BY_BUCKET.items():
            bucket_plays = row[f"{alignment}_plays"]
            if bucket_plays < MIN_BUCKET_PLAYS_FOR_EFFICIENCY:
                emitted = [f for f in (epa_field, success_field) if row[f] is not None]
                if emitted:
                    threshold_violations.append(
                        {"team": row["team"], "bucket": alignment, "emittedFields": emitted,
                         "violation": "efficiency_emitted_below_threshold"}
                    )
                if not any(
                    note["code"] == NOTE_SAMPLE_THRESHOLD_NOT_MET
                    and epa_field in note.get("fields", [])
                    for note in row["sample_notes"]
                ):
                    threshold_violations.append(
                        {"team": row["team"], "bucket": alignment,
                         "violation": "missing_sample_threshold_note"}
                    )
    checks.append(
        _check(
            "sample_thresholds_enforced",
            not threshold_violations,
            {"violations": threshold_violations},
        )
    )

    uncertainty_violations = []
    for row in rows:
        share = safe_ratio(
            row["unknown_or_unclassified_alignment_plays"], row["offensive_plays"]
        )
        should_flag = share is not None and share > UNKNOWN_SHARE_UNCERTAINTY_THRESHOLD
        if bool(row["unknown_alignment_uncertainty_flag"]) != should_flag:
            uncertainty_violations.append(
                {"team": row["team"], "unknownShare": share,
                 "flag": row["unknown_alignment_uncertainty_flag"]}
            )
    checks.append(
        _check(
            "unknown_share_uncertainty_flag_consistent",
            not uncertainty_violations,
            {"violations": uncertainty_violations},
        )
    )

    exclusion_metadata_ok = (
        "abortedPlaysExcludedTotal" in metadata["buildDiagnostics"]
        and "twoPointPlaysExcludedTotal" in metadata["buildDiagnostics"]
        and all("aborted_plays_excluded" in row and "two_point_plays" in row for row in rows)
    )
    checks.append(
        _check(
            "aborted_and_two_point_exclusions_explicit",
            exclusion_metadata_ok,
            {
                "abortedPlaysExcludedTotal": metadata["buildDiagnostics"].get(
                    "abortedPlaysExcludedTotal"
                ),
                "twoPointPlaysExcludedTotal": metadata["buildDiagnostics"].get(
                    "twoPointPlaysExcludedTotal"
                ),
            },
        )
    )

    success_definition = metadata.get("successDefinition") or {}
    checks.append(
        _check(
            "success_definition_disclosed",
            success_definition.get("name") == SUCCESS_DEFINITION["name"]
            and bool(success_definition.get("disclosure")),
            {"successDefinition": success_definition.get("name")},
        )
    )

    checks.append(
        _check(
            "epa_disclosure_present",
            bool(metadata.get("epaDisclosure")),
            {"epaDisclosure": bool(metadata.get("epaDisclosure"))},
        )
    )

    lineage_sources = lineage_manifest.get("sources", [])
    incomplete_sources = []
    for source in lineage_sources:
        missing_keys = sorted(key for key in REQUIRED_RETRIEVAL_KEYS if not source.get(key))
        if missing_keys:
            incomplete_sources.append(
                {"sourceName": source.get("sourceName"), "missingKeys": missing_keys}
            )
    checks.append(
        _check(
            "retrieval_metadata_complete",
            bool(lineage_sources) and not incomplete_sources,
            {"incompleteSources": incomplete_sources, "sourceCount": len(lineage_sources)},
        )
    )

    sources_missing_checksum = [
        source.get("sourceName")
        for source in lineage_sources
        if not (
            isinstance(source.get("checksum"), dict)
            and source["checksum"].get("algorithm")
            and source["checksum"].get("value")
        )
    ]
    checks.append(
        _check(
            "source_checksums_present",
            bool(lineage_sources) and not sources_missing_checksum,
            {"sourcesMissingChecksum": sources_missing_checksum},
        )
    )

    governance_status = metadata.get("governance", {}).get("governanceStatus")
    provenance_status = metadata.get("provenanceStatus")
    checks.append(
        _check(
            "non_governed_non_promoted_status",
            governance_status == "ungoverned"
            and provenance_status in ALLOWED_PROVENANCE_STATUSES,
            {"governanceStatus": governance_status, "provenanceStatus": provenance_status},
        )
    )

    all_passed = all(check["passed"] for check in checks)
    return {
        "report": "formation_summary_v0_2024_real_source_candidate_validation",
        "season": SEASON,
        "generatedAt": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "artifactPath": str(CANDIDATE_ARTIFACT_PATH),
        "rowCount": len(rows),
        "teamCount": coverage["teamsCovered"],
        "qualifyingPlaysTotal": metadata["buildDiagnostics"]["qualifyingPlaysTotal"],
        "abortedPlaysExcludedTotal": metadata["buildDiagnostics"]["abortedPlaysExcludedTotal"],
        "allPassed": all_passed,
        "checks": checks,
    }


def validate_against_schema(artifact: dict[str, Any]) -> list[str]:
    """Structural validation against schemas/formation_summary_v0.schema.json."""
    import jsonschema

    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    return [
        f"{'/'.join(str(part) for part in error.absolute_path) or '<root>'}: {error.message}"
        for error in validator.iter_errors(artifact)
    ]


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def main() -> int:
    pbp_rows, pbp_source_info = retrieve_pbp()
    source_refs = list(pbp_source_info["sourceRefs"])

    rows, diagnostics, suppressed = build_rows(pbp_rows, source_refs)
    metadata = build_metadata(
        rows=rows,
        diagnostics=diagnostics,
        suppressed=suppressed,
        input_sources_meta=[pbp_source_info],
    )
    artifact = build_artifact(rows, metadata, source_refs)
    lineage_manifest = build_lineage_manifest([pbp_source_info])
    validation_report = build_validation_report(artifact, diagnostics, lineage_manifest)

    schema_errors = validate_against_schema(artifact)
    validation_report["checks"].append(
        _check("json_schema_validation", not schema_errors, {"errors": schema_errors})
    )
    validation_report["allPassed"] = all(
        check["passed"] for check in validation_report["checks"]
    )

    print(
        f"Built {len(rows)} team-season rows "
        f"({metadata['buildDiagnostics']['qualifyingPlaysTotal']} qualifying plays; "
        f"{metadata['buildDiagnostics']['abortedPlaysExcludedTotal']} aborted plays excluded)."
    )
    for check in validation_report["checks"]:
        status = "PASS" if check["passed"] else "FAIL"
        print(f"  [{status}] {check['name']}")

    if not validation_report["allPassed"]:
        print(
            "ERROR: validation failed; refusing to emit candidate artifact, validation "
            "report, or lineage manifest.",
            file=sys.stderr,
        )
        return 1

    CANDIDATE_ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    LINEAGE_MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    CANDIDATE_ARTIFACT_PATH.write_text(f"{json.dumps(artifact, indent=2)}\n", encoding="utf-8")
    CANDIDATE_VALIDATION_REPORT_PATH.write_text(
        f"{json.dumps(validation_report, indent=2)}\n", encoding="utf-8"
    )
    LINEAGE_MANIFEST_PATH.write_text(
        f"{json.dumps(lineage_manifest, indent=2)}\n", encoding="utf-8"
    )

    print(f"Wrote candidate artifact: {CANDIDATE_ARTIFACT_PATH.resolve()}")
    print(f"Wrote validation report: {CANDIDATE_VALIDATION_REPORT_PATH.resolve()}")
    print(f"Wrote lineage manifest: {LINEAGE_MANIFEST_PATH.resolve()}")
    print(
        f"provenanceStatus: {metadata['provenanceStatus']}  "
        f"governanceStatus: {metadata['governance']['governanceStatus']}"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # fail closed with a clear reason
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

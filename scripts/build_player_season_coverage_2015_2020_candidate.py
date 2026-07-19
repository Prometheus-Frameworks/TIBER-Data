"""Build the bounded player_season_coverage_v0 CANDIDATE artifact for 2015-2020 REG.

TIBER-Data #222 (G2 implementation activation) under the accepted #220 design:
docs/design/player-season-coverage-v0-2015-2020-candidate-build-spec.md
(design blob 27aae171cb7b4138b272af32e42e06bb147900b2). The design document is
normative; this builder encodes it without weakening, silently generalizing, or
reinterpreting any accepted requirement.

Scope (design SS5-SS10):
- seasons: exactly 2015-2020, REG only, positions QB/RB/WR/TE;
- sources: per-season isolated nflreadpy.load_player_stats calls (week + reg
  summary levels, one pair per season) plus one shared nflreadpy.load_players();
- nflreadpy version must be exactly 0.1.5 (the version the accepted #218 audit
  observed) -- any other version aborts before any source call;
- every season must agree exactly with the accepted #218 structural fingerprint
  (row counts, week set, wrong-season/duplicate counts, max games, identity join
  rate) before any output is staged;
- thirteen deterministic source-content hashes (six week-level, six REG-summary,
  one joined-identity-fields) pin the exact consumed source content;
- historical REG week span is exactly 1-17 per season (never the 2021+ 1-18 rule);
- FULL_SEASON_MIN_WEEKS_2015_2020 = 14 (tolerance-preserving mapping of the 2021+
  rule to the 16-game/17-week era; see methodology in the emitted artifact);
- ordinary games cap 16; games_played == 17 is accepted only with source-backed
  multi-team disjoint-week evidence -- an overage is never inferred to be a trade;
- gsis_id identity joins must be exactly 1.0 under the current #218 evidence lock;
  the family floor 0.95 is retained only as defense in depth. No publishable
  provisional identity state exists in this build;
- optional draft metadata is honestly nullable (null in, null out, never zero).

Publication (design SS13) is an all-or-nothing journaled set transaction over the
five candidate outputs (artifact, manifest, validation result, md report, json
report): phase-0 residue preflight, phase-1 staging to temp files, phase-2
journaled commit with backups, rollback restoring the exact pre-run state
(presence and bytes, or absence) on every caught failure, deliberate backup
retention plus a fatal torn-state diagnostic when rollback itself fails, and a
mandatory post-publication integrity gate that rejects torn output states.

Exit codes: 0 = candidate built, validated, all outputs written; 1 = source or
feasibility failure (nothing written); 2 = post-assembly validation failure (the
artifact is withheld, nothing is written, diagnostics go to stderr only).

Only main() performs network calls. build_candidate_payload() and every check,
hash, render, and publication function is pure/offline and fixture-testable.

This artifact is a CANDIDATE / evidence artifact, not a promoted dataset. It
never contains 2021+ rows, never merges with the promoted 2021-2025 artifact,
never widens the promoted support window, and authorizes no promotion, Forecast,
ADP, research, or product behavior.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import sys
from collections import defaultdict
from datetime import date, datetime, timezone
from importlib import metadata as importlib_metadata
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

SEASONS = (2015, 2016, 2017, 2018, 2019, 2020)
SEASON_TYPE = "REG"
INCLUDED_POSITIONS = {"QB", "RB", "WR", "TE"}

# Historical era constants (design SS7-SS9). These are deliberately era-scoped
# names: the 2021+ builders' EXPECTED_REG_WEEKS = set(range(1, 19)) and
# full-season threshold 15 are neither imported, modified, nor reinterpreted here.
EXPECTED_REG_WEEKS_2015_2020 = set(range(1, 18))  # weeks 1-17, evidence: #218 audit
FULL_SEASON_MIN_WEEKS_2015_2020 = 14  # of the 17-week span (tolerance mapping, design SS8)
ORDINARY_GAMES_CAP_2015_2020 = 16  # single-team per-player maximum (16 games, one bye)
ABSOLUTE_GAMES_CAP_2015_2020 = 17  # multi-team-only maximum (byes in different weeks)
IDENTITY_JOIN_RATE_FLOOR = 0.95  # family defense-in-depth floor; the binding gate is exact 1.0

REQUIRED_NFLREADPY_VERSION = "0.1.5"  # the exact version the accepted #218 audit observed

# Accepted evidence lock (design SS3). Any change to these pins requires a new
# source-audit issue and explicit operator acceptance -- never an inline edit.
ACCEPTED_MAIN_SHA = "251f2369bd5700d9a3afe66269aaae4a60d61fa8"
ACCEPTED_AUDIT_SCRIPT_BLOB = "529f832b050dba494146f4b133c202072f587c0e"
ACCEPTED_DESIGN_DOC = "docs/design/player-season-coverage-v0-2015-2020-candidate-build-spec.md"
ACCEPTED_DESIGN_BLOB = "27aae171cb7b4138b272af32e42e06bb147900b2"
AUDIT_EVIDENCE_REPORTS = (
    "docs/reports/player-season-coverage-v0-2015-2020-source-availability.md",
    "docs/reports/player-season-coverage-v0-2015-2020-source-availability.json",
)
TRACKING_ISSUE = "TIBER-Data#222 (G2 implementation activation under the #220 design; audit evidence #216/#218)"

# Accepted #218 per-season structural fingerprint (design SS6). Values are copied
# verbatim from the committed machine-readable evidence report
# docs/reports/player-season-coverage-v0-2015-2020-source-availability.json.
# A test asserts this constant equals the committed evidence, so it cannot drift
# silently from the accepted authority.
ACCEPTED_SOURCE_FINGERPRINT_2015_2020 = {
    2015: {
        "week_level_rows_total": 17613,
        "week_level_rows_reg": 16905,
        "reg_level_rows_total": 1846,
        "reg_level_rows_reg_qb_rb_wr_te": 556,
        "row_counts_by_position_reg_level": {"QB": 74, "RB": 151, "WR": 212, "TE": 119},
        "player_counts_by_position": {"QB": 74, "RB": 151, "WR": 212, "TE": 119},
        "unique_players_all_positions": 556,
        "reg_week_numbers_observed": list(range(1, 18)),
        "wrong_season_week_row_count": 0,
        "wrong_season_reg_row_count": 0,
        "duplicate_grain_pairs": 0,
        "max_games_reg_level": 16,
        "identity_join_rate_gsis_id": 1.0,
    },
    2016: {
        "week_level_rows_total": 17552,
        "week_level_rows_reg": 16840,
        "reg_level_rows_total": 1856,
        "reg_level_rows_reg_qb_rb_wr_te": 557,
        "row_counts_by_position_reg_level": {"QB": 71, "RB": 151, "WR": 210, "TE": 125},
        "player_counts_by_position": {"QB": 71, "RB": 151, "WR": 210, "TE": 125},
        "unique_players_all_positions": 557,
        "reg_week_numbers_observed": list(range(1, 18)),
        "wrong_season_week_row_count": 0,
        "wrong_season_reg_row_count": 0,
        "duplicate_grain_pairs": 0,
        "max_games_reg_level": 16,
        "identity_join_rate_gsis_id": 1.0,
    },
    2017: {
        "week_level_rows_total": 17477,
        "week_level_rows_reg": 16786,
        "reg_level_rows_total": 1869,
        "reg_level_rows_reg_qb_rb_wr_te": 553,
        "row_counts_by_position_reg_level": {"QB": 73, "RB": 143, "WR": 214, "TE": 123},
        "player_counts_by_position": {"QB": 73, "RB": 143, "WR": 214, "TE": 123},
        "unique_players_all_positions": 553,
        "reg_week_numbers_observed": list(range(1, 18)),
        "wrong_season_week_row_count": 0,
        "wrong_season_reg_row_count": 0,
        "duplicate_grain_pairs": 0,
        "max_games_reg_level": 16,
        "identity_join_rate_gsis_id": 1.0,
    },
    2018: {
        "week_level_rows_total": 17414,
        "week_level_rows_reg": 16728,
        "reg_level_rows_total": 1884,
        "reg_level_rows_reg_qb_rb_wr_te": 577,
        "row_counts_by_position_reg_level": {"QB": 72, "RB": 149, "WR": 228, "TE": 128},
        "player_counts_by_position": {"QB": 72, "RB": 149, "WR": 228, "TE": 128},
        "unique_players_all_positions": 577,
        "reg_week_numbers_observed": list(range(1, 18)),
        "wrong_season_week_row_count": 0,
        "wrong_season_reg_row_count": 0,
        "duplicate_grain_pairs": 0,
        "max_games_reg_level": 16,
        "identity_join_rate_gsis_id": 1.0,
    },
    2019: {
        "week_level_rows_total": 17362,
        "week_level_rows_reg": 16663,
        "reg_level_rows_total": 1889,
        "reg_level_rows_reg_qb_rb_wr_te": 572,
        "row_counts_by_position_reg_level": {"QB": 71, "RB": 146, "WR": 230, "TE": 125},
        "player_counts_by_position": {"QB": 71, "RB": 146, "WR": 230, "TE": 125},
        "unique_players_all_positions": 572,
        "reg_week_numbers_observed": list(range(1, 18)),
        "wrong_season_week_row_count": 0,
        "wrong_season_reg_row_count": 0,
        "duplicate_grain_pairs": 0,
        "max_games_reg_level": 17,
        "identity_join_rate_gsis_id": 1.0,
    },
    2020: {
        "week_level_rows_total": 17602,
        "week_level_rows_reg": 16774,
        "reg_level_rows_total": 1984,
        "reg_level_rows_reg_qb_rb_wr_te": 602,
        "row_counts_by_position_reg_level": {"QB": 82, "RB": 157, "WR": 233, "TE": 130},
        "player_counts_by_position": {"QB": 82, "RB": 157, "WR": 233, "TE": 130},
        "unique_players_all_positions": 602,
        "reg_week_numbers_observed": list(range(1, 18)),
        "wrong_season_week_row_count": 0,
        "wrong_season_reg_row_count": 0,
        "duplicate_grain_pairs": 0,
        "max_games_reg_level": 16,
        "identity_join_rate_gsis_id": 1.0,
    },
}

# Output surfaces (design SS5). All candidate-scoped; none collides with a promoted
# or accepted path. OUTPUT_BASE_DIR exists so offline tests can point the entire
# output set at an isolated temporary directory without touching the repository.
OUTPUT_BASE_DIR = REPO_ROOT
ARTIFACT_RELPATH = "data/processed/evidence/player_season_coverage_2015_2020_candidate.source_backed.json"
MANIFEST_RELPATH = "data/processed/evidence/player_season_coverage_2015_2020_candidate.source_backed.MANIFEST.json"
VALIDATION_RELPATH = "docs/reports/player-season-coverage-v0-2015-2020-candidate-validation.json"
REPORT_MD_RELPATH = "docs/reports/player-season-coverage-v0-2015-2020-candidate-build.md"
REPORT_JSON_RELPATH = "docs/reports/player-season-coverage-v0-2015-2020-candidate-build.json"

VALIDATOR_RELPATH = "scripts/validate_player_season_coverage_v0.py"
SCHEMA_RELPATH = "schemas/player_season_coverage_v0.schema.json"

ARTIFACT_ID = "player_season_coverage_2015_2020_candidate.source_backed"
CANDIDATE_STATUS = "candidate_evidence_artifact_not_promoted"

# Support-claim guard (design SS4/G-4): this exact availability claim (in either
# dash form) must never appear in any output this builder publishes.
PROHIBITED_SUPPORT_CLAIM_VARIANTS = ("2015-2025 is available", "2015–2025 is available")

IDENTITY_CONTRADICTION_FIELDS = (
    "birth_date",
    "rookie_season",
    "draft_year",
    "draft_round",
    "draft_pick",
    "draft_team",
)

PRIMARY_TEAM_RULE = (
    "most weeks_observed in REG week-level production rows for the season; "
    "ties broken by earliest week of first appearance, then alphabetical team code"
)
TEAM_CONTEXT_SOURCE_NOTE = (
    "Team context (teams[], primary_team, team_weeks) is derived from the team-of-record "
    "on each week-level row in nflreadpy.load_player_stats (game appearances with a "
    "recorded stat line), not from a separate roster-membership pull. It reflects teams "
    "the player recorded production for in a given week, not full roster-membership weeks."
)
COVERAGE_STATUS_RULE = (
    "Historical 2015-2020 rule: full_season: weeks_observed >= 14; partial_season: "
    "1 < weeks_observed < 14; single_week: weeks_observed == 1. weeks_observed counts "
    "distinct REG week NUMBERS (1-17, the full week span of a 2015-2020 season) with a "
    "recorded stat line. The 2021+ threshold (15 of 18) is a tolerance of up to 3 missed "
    "week-numbers, not a percentage; mapping that same tolerance to the 16-game/17-week "
    "era yields 14 (17 - 3 = 14; equivalently the single-team ordinary ceiling 16 minus 2). "
    "The 2021+ constant is never silently reused for this era in either direction."
)
GAMES_CAP_NOTE = (
    "Ordinary single-team per-player maximum games_played is 16 (16 team games, one bye). "
    "games_played == 17 is accepted only when the row's own week-level team context shows "
    ">= 2 distinct teams with disjoint production weeks consistent with the games count "
    "(source-backed multi-team evidence). An overage is never inferred to be a trade; "
    "absent that evidence the build fails closed."
)
AGE_REFERENCE_NOTE = "season_age computed against a fixed reference date of September 1 of `season`."


class SourceFeasibilityError(ValueError):
    """Raised when the approved source family fails one of this build's fail-closed checks."""


class SourceEvidenceDriftError(SourceFeasibilityError):
    """Raised when the freshly loaded source disagrees with the accepted #218 evidence lock.

    Diagnostics are bounded: aggregate expected-vs-observed values only, never player rows.
    Resolution requires a new source-audit issue plus explicit operator acceptance -- the
    evidence lock never moves silently.
    """


class CandidateValidationError(RuntimeError):
    """Raised when the assembled payload fails post-assembly validation (exit code 2).

    The artifact is withheld: nothing is written, diagnostics go to stderr only.
    """


class PublicationError(RuntimeError):
    """Raised when the journaled set publication fails and rollback restored the pre-run state."""


class ResidueError(PublicationError):
    """Raised in phase 0 when pre-existing .tmp-*/.prev-* residue is found.

    The residue (which may include the only recoverable prior copy left by a prior
    hard kill) is left exactly as found; recovery is a deliberate operator step.
    """


class RollbackFailureError(PublicationError):
    """Fatal torn-state failure: rollback itself could not complete.

    Every recoverable backup is deliberately retained on disk; the message names the
    per-path journal state.
    """


class TornStateError(PublicationError):
    """Raised when the published output set fails the mandatory integrity rejection gate."""


class BackupCleanupError(PublicationError):
    """Raised when all five outputs installed successfully but a backup file left over

    from the transaction could not be deleted afterward. This is not data loss and not
    a torn state (every final output is correct on disk); it means final housekeeping
    did not complete and a retained backup must be cleared by an operator before the
    next run's phase-0 residue preflight would otherwise reject it.
    """


# ---------------------------------------------------------------------------
# Generic helpers (family conventions shared with the accepted 2021 builder)
# ---------------------------------------------------------------------------


def _records_from_dataframe(df) -> list[dict]:
    if hasattr(df, "to_dicts"):
        return df.to_dicts()
    return df.to_dict("records")


def _json_safe_value(value):
    if value is None:
        return None
    try:
        if isinstance(value, float) and math.isnan(value):
            return None
        if isinstance(value, float) and not math.isfinite(value):
            return None
    except TypeError:
        pass
    if isinstance(value, date) and not isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def _resolve_column(columns: set[str], candidates: list[str], field_name: str, required: bool = True) -> str | None:
    for candidate in candidates:
        if candidate in columns:
            return candidate
    if required:
        raise SourceFeasibilityError(
            f"Missing required column for '{field_name}'. Expected one of {candidates}, found columns={sorted(columns)}"
        )
    return None


def _round_or_none(value, ndigits: int = 4):
    if value is None:
        return None
    try:
        if isinstance(value, float) and (math.isnan(value) or not math.isfinite(value)):
            return None
        return round(float(value), ndigits)
    except (TypeError, ValueError):
        return None


def _season_age(birth_date_value, season: int) -> float | None:
    if birth_date_value is None:
        return None
    if isinstance(birth_date_value, datetime):
        birth_date_value = birth_date_value.date()
    elif isinstance(birth_date_value, str):
        try:
            birth_date_value = date.fromisoformat(birth_date_value.strip()[:10])
        except ValueError:
            return None
    if not isinstance(birth_date_value, date):
        return None
    reference_date = date(season, 9, 1)
    days = (reference_date - birth_date_value).days
    if days < 0:
        return None
    return round(days / 365.25, 2)


def _canonical_hash_json(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _serialize_json_output(payload: dict) -> str:
    """Canonical family serialization: indent=2, allow_nan=False, single trailing newline."""
    return f"{json.dumps(payload, indent=2, allow_nan=False)}\n"


# ---------------------------------------------------------------------------
# Column resolution (required sets per the accepted #218 audit, including
# `season` at BOTH summary levels per the PR #217 correction)
# ---------------------------------------------------------------------------


def _resolve_week_columns(week_df) -> dict[str, str]:
    columns = set(week_df.columns)
    return {
        "season": _resolve_column(columns, ["season"], "season"),
        "week": _resolve_column(columns, ["week"], "week"),
        "player_id": _resolve_column(columns, ["player_id", "gsis_id"], "player_id"),
        "team": _resolve_column(columns, ["team", "recent_team"], "team"),
        "season_type": _resolve_column(columns, ["season_type"], "season_type"),
    }


def _resolve_reg_columns(reg_df) -> dict[str, str | None]:
    columns = set(reg_df.columns)
    resolved: dict[str, str | None] = {
        "season": _resolve_column(columns, ["season"], "season"),
        "player_id": _resolve_column(columns, ["player_id", "gsis_id"], "player_id"),
        "player_name": _resolve_column(columns, ["player_display_name", "player_name"], "player_name"),
        "position": _resolve_column(columns, ["position"], "position"),
        "games": _resolve_column(columns, ["games"], "games"),
        "season_type": _resolve_column(columns, ["season_type"], "season_type", required=False),
    }
    for optional in (
        "completions",
        "attempts",
        "passing_yards",
        "passing_tds",
        "passing_interceptions",
        "carries",
        "rushing_yards",
        "rushing_tds",
        "receptions",
        "targets",
        "receiving_yards",
        "receiving_tds",
        "receiving_air_yards",
        "target_share",
        "air_yards_share",
        "wopr",
        "racr",
        "fantasy_points_ppr",
    ):
        resolved[optional] = _resolve_column(columns, [optional], optional, required=False)
    return resolved


def _included_reg_records(reg_df, reg_cols: dict[str, str | None]) -> list[dict]:
    """REG rows for the included positions with a non-empty player_id, in source order."""
    included: list[dict] = []
    for row in _records_from_dataframe(reg_df):
        player_id = row.get(reg_cols["player_id"])
        if player_id is None or str(player_id).strip() == "":
            continue
        position = str(row.get(reg_cols["position"]) or "").strip().upper()
        if position not in INCLUDED_POSITIONS:
            continue
        season_type_col = reg_cols["season_type"]
        season_type_value = (
            str(row.get(season_type_col, SEASON_TYPE)).strip().upper() if season_type_col else SEASON_TYPE
        )
        if season_type_value != SEASON_TYPE:
            continue
        included.append(row)
    return included


def _reg_week_records(week_df, week_cols: dict[str, str]) -> list[dict]:
    """Week-level REG rows with a non-empty player_id. POST rows are excluded here and
    never contribute to REG evidence, but their presence alone is never an error."""
    kept: list[dict] = []
    for row in _records_from_dataframe(week_df):
        if str(row.get(week_cols["season_type"], "")).strip().upper() != SEASON_TYPE:
            continue
        player_id = row.get(week_cols["player_id"])
        if player_id is None or str(player_id).strip() == "":
            continue
        kept.append(row)
    return kept


# ---------------------------------------------------------------------------
# Identity index (design SS10)
# ---------------------------------------------------------------------------


def _load_players_index(players_df) -> dict[str, dict]:
    """Index load_players() rows by gsis_id.

    Tightened relative to the accepted 2021 builder (which is last-write-wins):
    duplicate gsis_id rows whose identity-relevant fields contradict fail the build
    closed, naming only the colliding-key count. Exact duplicates collapse silently.
    """
    columns = set(players_df.columns)
    gsis_col = _resolve_column(columns, ["gsis_id"], "gsis_id")
    index: dict[str, dict] = {}
    contradictory_keys: set[str] = set()
    for row in _records_from_dataframe(players_df):
        gsis_id = row.get(gsis_col)
        if gsis_id is None or str(gsis_id).strip() == "":
            continue
        key = str(gsis_id).strip()
        existing = index.get(key)
        if existing is None:
            index[key] = row
            continue
        for field in IDENTITY_CONTRADICTION_FIELDS:
            if _json_safe_value(existing.get(field)) != _json_safe_value(row.get(field)):
                contradictory_keys.add(key)
                break
    if contradictory_keys:
        raise SourceFeasibilityError(
            f"load_players() returned contradictory duplicate identity rows for "
            f"{len(contradictory_keys)} gsis_id key(s). Build fails closed rather than "
            "resolving contradictory identity evidence."
        )
    return index


# ---------------------------------------------------------------------------
# Per-season structural checks (design SS7)
# ---------------------------------------------------------------------------


def _verify_season_match(season: int, week_df, reg_df, week_cols, reg_cols) -> None:
    """Any wrong-season row in a season's response aborts the build. Rows are never
    silently filtered into a 'clean' subset for building (design SS7)."""
    for level, df, season_col in (
        ("week-level", week_df, week_cols["season"]),
        ("reg-summary", reg_df, reg_cols["season"]),
    ):
        observed_values: set = set()
        wrong = 0
        for row in _records_from_dataframe(df):
            value = row.get(season_col)
            observed_values.add(value)
            if value is None or int(value) != season:
                wrong += 1
        if wrong:
            raise SourceFeasibilityError(
                f"Season {season} {level} response contains {wrong} row(s) whose own season "
                f"value differs from the requested season (observed season values: "
                f"{sorted(str(v) for v in observed_values)}). The build never filters drifted "
                "responses into a usable subset; it fails closed."
            )


def _verify_week_span(season: int, week_records: list[dict], week_cols) -> None:
    """Six independent per-season checks; season N passing never excuses season M."""
    observed: set[int] = set()
    for row in week_records:
        week_value = row.get(week_cols["week"])
        if week_value is None:
            raise SourceFeasibilityError(
                f"Season {season} has REG week-level row(s) with a null week value; the "
                "historical week span cannot be verified. Build fails closed."
            )
        observed.add(int(week_value))
    if observed != EXPECTED_REG_WEEKS_2015_2020:
        missing = sorted(EXPECTED_REG_WEEKS_2015_2020 - observed)
        extra = sorted(observed - EXPECTED_REG_WEEKS_2015_2020)
        raise SourceFeasibilityError(
            f"Season {season} REG week span violates the audited historical rule "
            f"(exactly weeks 1-17). missing_weeks={missing} unexpected_weeks={extra}. "
            "Build fails closed; a season-specific exception requires a new source-audit "
            "issue amending the evidence lock, never an inline override."
        )


def _verify_no_duplicate_grain(season: int, included_reg: list[dict], reg_cols) -> None:
    seen: set[tuple[str, int, str]] = set()
    for row in included_reg:
        key = (str(row.get(reg_cols["player_id"])).strip(), season, SEASON_TYPE)
        if key in seen:
            raise SourceFeasibilityError(
                f"Duplicate player-season-season_type grain detected in season {season} "
                "REG-summary rows. Duplicates are never resolved into a merged row; build fails closed."
            )
        seen.add(key)


# ---------------------------------------------------------------------------
# Accepted-source fingerprint gate (design SS6)
# ---------------------------------------------------------------------------


def _installed_nflreadpy_version() -> str | None:
    try:
        return importlib_metadata.version("nflreadpy")
    except importlib_metadata.PackageNotFoundError:
        return None


def verify_nflreadpy_version(installed_version: str | None) -> None:
    """The installed nflreadpy version must be exactly the audited 0.1.5.

    No 'newer-but-checks-pass' acceptance exists under the current evidence lock.
    """
    if installed_version != REQUIRED_NFLREADPY_VERSION:
        raise SourceEvidenceDriftError(
            "source-evidence drift: installed nflreadpy version "
            f"{installed_version!r} is not exactly the accepted #218 audited version "
            f"{REQUIRED_NFLREADPY_VERSION!r}. No candidate is produced; changing the "
            "dependency pin requires a new source-audit issue and explicit operator "
            "acceptance of a revised evidence lock."
        )


def compute_observed_season_fingerprint(season: int, week_df, reg_df, players_index: dict[str, dict]) -> dict:
    """Aggregate structural fingerprint of one season's freshly loaded source frames,
    shaped exactly like the accepted #218 per-season evidence values."""
    week_cols = _resolve_week_columns(week_df)
    reg_cols = _resolve_reg_columns(reg_df)

    week_rows_all = _records_from_dataframe(week_df)
    reg_rows_all = _records_from_dataframe(reg_df)
    week_records = _reg_week_records(week_df, week_cols)
    included_reg = _included_reg_records(reg_df, reg_cols)

    wrong_week = sum(
        1 for row in week_rows_all if row.get(week_cols["season"]) is None or int(row[week_cols["season"]]) != season
    )
    wrong_reg = sum(
        1 for row in reg_rows_all if row.get(reg_cols["season"]) is None or int(row[reg_cols["season"]]) != season
    )

    week_numbers = sorted(
        {int(row[week_cols["week"]]) for row in week_records if row.get(week_cols["week"]) is not None}
    )

    row_counts: dict[str, int] = {p: 0 for p in sorted(INCLUDED_POSITIONS)}
    players_by_position: dict[str, set[str]] = {p: set() for p in sorted(INCLUDED_POSITIONS)}
    unique_players: set[str] = set()
    grain_seen: set[tuple[str, int, str]] = set()
    duplicate_grains = 0
    max_games = 0
    for row in included_reg:
        player_id = str(row.get(reg_cols["player_id"])).strip()
        position = str(row.get(reg_cols["position"]) or "").strip().upper()
        row_counts[position] += 1
        players_by_position[position].add(player_id)
        unique_players.add(player_id)
        grain_key = (player_id, season, SEASON_TYPE)
        if grain_key in grain_seen:
            duplicate_grains += 1
        grain_seen.add(grain_key)
        games_value = row.get(reg_cols["games"])
        if games_value is not None and int(games_value) > max_games:
            max_games = int(games_value)

    joined = sum(1 for player_id in unique_players if player_id in players_index)
    join_rate = (joined / len(unique_players)) if unique_players else 0.0

    return {
        "week_level_rows_total": len(week_rows_all),
        "week_level_rows_reg": len(week_records),
        "reg_level_rows_total": len(reg_rows_all),
        "reg_level_rows_reg_qb_rb_wr_te": len(included_reg),
        "row_counts_by_position_reg_level": row_counts,
        "player_counts_by_position": {p: len(ids) for p, ids in players_by_position.items()},
        "unique_players_all_positions": len(unique_players),
        "reg_week_numbers_observed": week_numbers,
        "wrong_season_week_row_count": wrong_week,
        "wrong_season_reg_row_count": wrong_reg,
        "duplicate_grain_pairs": duplicate_grains,
        "max_games_reg_level": max_games,
        "identity_join_rate_gsis_id": join_rate,
    }


def verify_accepted_source_fingerprint(
    per_season_frames: dict[int, dict],
    players_index: dict[str, dict],
    accepted_fingerprint: dict[int, dict] | None = None,
) -> dict[int, dict]:
    """Exact per-season agreement with the accepted #218 evidence, verified before any
    output is staged. Any mismatch aborts with a bounded aggregate-only drift diagnostic.
    Returns the observed fingerprints for reuse in the manifest/report reconciliation."""
    accepted = accepted_fingerprint if accepted_fingerprint is not None else ACCEPTED_SOURCE_FINGERPRINT_2015_2020
    observed_by_season: dict[int, dict] = {}
    mismatches: list[str] = []
    for season in SEASONS:
        frames = per_season_frames[season]
        observed = compute_observed_season_fingerprint(season, frames["week"], frames["reg"], players_index)
        observed_by_season[season] = observed
        expected = accepted[season]
        for field in expected:
            if observed.get(field) != expected[field]:
                mismatches.append(
                    f"season={season} field={field} expected={expected[field]!r} observed={observed.get(field)!r}"
                )
    if mismatches:
        raise SourceEvidenceDriftError(
            "source-evidence drift: the freshly loaded source disagrees with the accepted "
            "#218 structural fingerprint. No output was staged and no candidate exists. "
            "Aggregate expected-vs-observed mismatches: " + "; ".join(mismatches) + ". "
            "Resolution requires a new source-audit issue and explicit operator acceptance."
        )
    return observed_by_season


# ---------------------------------------------------------------------------
# Deterministic source-content hashes (design SS6)
# ---------------------------------------------------------------------------


def compute_source_content_hashes(
    per_season_frames: dict[int, dict],
    players_index: dict[str, dict],
) -> dict:
    """Thirteen deterministic sha256 hashes over canonically serialized rows restricted
    to exactly the columns the build consumes: per season one week-level hash (rows
    sorted by (season, player_id, week)) and one REG-summary hash (rows sorted by
    (season, player_id)), plus one hash over the consumed load_players() identity
    fields of joined players, sorted by gsis_id."""
    week_hashes: dict[str, str] = {}
    reg_hashes: dict[str, str] = {}
    joined_player_ids: set[str] = set()

    for season in SEASONS:
        frames = per_season_frames[season]
        week_cols = _resolve_week_columns(frames["week"])
        reg_cols = _resolve_reg_columns(frames["reg"])

        week_rows = []
        for row in _reg_week_records(frames["week"], week_cols):
            week_rows.append(
                {
                    "season": _json_safe_value(row.get(week_cols["season"])),
                    "week": _json_safe_value(row.get(week_cols["week"])),
                    "player_id": str(row.get(week_cols["player_id"])).strip(),
                    "team": _json_safe_value(row.get(week_cols["team"])),
                    "season_type": _json_safe_value(row.get(week_cols["season_type"])),
                }
            )
        week_rows.sort(key=lambda r: (r["season"] or 0, r["player_id"], r["week"] or 0))
        week_hashes[str(season)] = _sha256_text(_canonical_hash_json(week_rows))

        reg_rows = []
        for row in _included_reg_records(frames["reg"], reg_cols):
            hashed_row = {"player_id": str(row.get(reg_cols["player_id"])).strip()}
            for field, column in reg_cols.items():
                if field == "player_id":
                    continue
                hashed_row[field] = _json_safe_value(row.get(column)) if column is not None else None
            reg_rows.append(hashed_row)
            joined_player_ids.add(hashed_row["player_id"])
        reg_rows.sort(key=lambda r: (r["season"] or 0, r["player_id"]))
        reg_hashes[str(season)] = _sha256_text(_canonical_hash_json(reg_rows))

    identity_rows = []
    for player_id in sorted(joined_player_ids):
        identity_row = players_index.get(player_id)
        if identity_row is None:
            continue
        identity_rows.append(
            {
                "gsis_id": player_id,
                "birth_date": _json_safe_value(identity_row.get("birth_date")),
                "rookie_season": _json_safe_value(identity_row.get("rookie_season")),
                "draft_year": _json_safe_value(identity_row.get("draft_year")),
                "draft_round": _json_safe_value(identity_row.get("draft_round")),
                "draft_pick": _json_safe_value(identity_row.get("draft_pick")),
                "draft_team": _json_safe_value(identity_row.get("draft_team")),
                "espn_id": _json_safe_value(identity_row.get("espn_id")),
            }
        )
    identity_hash = _sha256_text(_canonical_hash_json(identity_rows))

    return {
        "week_level_by_season": week_hashes,
        "reg_summary_by_season": reg_hashes,
        "joined_identity_fields": identity_hash,
    }


def verify_accepted_content_hashes(computed: dict, accepted: dict) -> None:
    """After a candidate has been accepted (gate G5), any rebuild must reproduce the
    accepted source-content hashes exactly or abort before staging (value-level drift
    inside unchanged aggregates is bounded here, not ignored)."""
    mismatches: list[str] = []
    for season in SEASONS:
        key = str(season)
        if computed["week_level_by_season"].get(key) != accepted.get("week_level_by_season", {}).get(key):
            mismatches.append(f"week_level_by_season[{key}]")
        if computed["reg_summary_by_season"].get(key) != accepted.get("reg_summary_by_season", {}).get(key):
            mismatches.append(f"reg_summary_by_season[{key}]")
    if computed["joined_identity_fields"] != accepted.get("joined_identity_fields"):
        mismatches.append("joined_identity_fields")
    if mismatches:
        raise SourceEvidenceDriftError(
            "source-evidence value drift: the consumed source content no longer reproduces "
            "the accepted source-content hash(es) for: " + ", ".join(mismatches) + ". "
            "One or more consumed row values changed inside unchanged aggregates. No output "
            "was staged; a value-level upstream correction requires a fresh source-audit "
            "issue and explicit operator acceptance before any republication."
        )


# ---------------------------------------------------------------------------
# Team context and era semantics (design SS8-SS9)
# ---------------------------------------------------------------------------


def _build_team_context(week_records: list[dict], week_cols: dict[str, str]) -> dict[str, dict]:
    """Group one season's week-level REG production rows by player into team context.

    Retains per-team week sets (internal) so games/trade evidence can be verified
    against the same source rows that build teams[]/team_weeks[]."""
    grouped: dict[str, list[tuple[int, str]]] = defaultdict(list)
    for row in week_records:
        player_id = str(row.get(week_cols["player_id"])).strip()
        week = int(row[week_cols["week"]])
        team = str(row.get(week_cols["team"]) or "").strip()
        if not team:
            continue
        grouped[player_id].append((week, team))

    context: dict[str, dict] = {}
    for player_id, entries in grouped.items():
        entries.sort(key=lambda e: e[0])
        first_seen_week: dict[str, int] = {}
        weeks_by_team: dict[str, set[int]] = defaultdict(set)
        for week, team in entries:
            weeks_by_team[team].add(week)
            if team not in first_seen_week:
                first_seen_week[team] = week

        teams_chronological = sorted(weeks_by_team.keys(), key=lambda t: first_seen_week[t])
        team_weeks = [
            {"team": team, "weeks_observed": len(weeks_by_team[team])} for team in teams_chronological
        ]
        team_weeks.sort(key=lambda tw: (-tw["weeks_observed"], first_seen_week[tw["team"]], tw["team"]))
        primary_team = team_weeks[0]["team"] if team_weeks else None
        distinct_weeks = {w for w, _t in entries}

        context[player_id] = {
            "teams": teams_chronological,
            "primary_team": primary_team,
            "team_weeks": team_weeks,
            "team_unknown": primary_team is None,
            "weeks_observed": len(distinct_weeks),
            "weeks_by_team": {team: sorted(weeks) for team, weeks in weeks_by_team.items()},
        }
    return context


def _coverage_status(weeks_observed: int) -> str:
    if weeks_observed >= FULL_SEASON_MIN_WEEKS_2015_2020:
        return "full_season"
    if weeks_observed > 1:
        return "partial_season"
    if weeks_observed == 1:
        return "single_week"
    return "unknown"


def _verify_games_and_trade_semantics(season: int, player_id: str, games_played: int | None, ctx: dict | None) -> None:
    """Fail-closed games caps and source-backed trade evidence (design SS9).

    A games total above the ordinary cap is never inferred to be a trade: it is valid
    only when the row's own week-level team context shows >= 2 distinct teams with
    disjoint production weeks consistent with the games count."""
    weeks_observed = ctx["weeks_observed"] if ctx is not None else 0
    if weeks_observed > 17:
        raise SourceFeasibilityError(
            f"Season {season}: weeks_observed {weeks_observed} exceeds 17, which is impossible "
            "under the verified 1-17 week span. Build fails closed."
        )
    if games_played is None:
        raise SourceFeasibilityError(
            f"Season {season}: an included REG-summary row has a null games value; the audited "
            "evidence observed zero games nulls, and the era games caps cannot be verified. "
            "Build fails closed."
        )
    if games_played > ABSOLUTE_GAMES_CAP_2015_2020:
        raise SourceFeasibilityError(
            f"Season {season}: games_played {games_played} exceeds the absolute 2015-2020 cap "
            f"{ABSOLUTE_GAMES_CAP_2015_2020} (achievable only by multi-team players whose teams' "
            "byes differ). Build fails closed."
        )
    if games_played > weeks_observed:
        raise SourceFeasibilityError(
            f"Season {season}: games_played {games_played} exceeds weeks_observed {weeks_observed} "
            "(tolerance 0): a player cannot play more games than distinct observed week-numbers. "
            "Build fails closed on this reconciliation failure."
        )
    if ctx is not None and len(ctx["teams"]) > 1:
        weeks_by_team = ctx["weeks_by_team"]
        total_team_weeks = sum(len(weeks) for weeks in weeks_by_team.values())
        if total_team_weeks != weeks_observed:
            raise SourceFeasibilityError(
                f"Season {season}: a multi-team row's team_weeks do not partition the observed "
                "weeks (overlapping production weeks across teams). Build fails closed."
            )
    if games_played > ORDINARY_GAMES_CAP_2015_2020:
        if ctx is None or len(ctx["teams"]) < 2:
            raise SourceFeasibilityError(
                f"Season {season}: games_played {games_played} exceeds the ordinary single-team "
                f"cap {ORDINARY_GAMES_CAP_2015_2020} with only "
                f"{0 if ctx is None else len(ctx['teams'])} team(s) in the row's week-level "
                "context. An overage is never inferred to be a trade; absent source-backed "
                "multi-team disjoint-week evidence this is source drift and the build fails closed."
            )


# ---------------------------------------------------------------------------
# Payload assembly (pure, offline-testable; design SS13)
# ---------------------------------------------------------------------------


def build_candidate_payload(
    per_season_frames: dict[int, dict],
    players_df,
    generated_at: str,
    *,
    accepted_fingerprint: dict[int, dict] | None = None,
    accepted_source_content_hashes: dict | None = None,
) -> tuple[dict, dict]:
    """Assemble the full six-season candidate payload in memory, fail-closed-verified.

    Returns (payload, build_evidence); build_evidence carries the observed
    fingerprints, the thirteen source-content hashes, and the per-season source
    calls for the manifest and build report. Raises (writes nothing) on any
    feasibility, drift, or era-rule violation.
    """
    datetime.fromisoformat(generated_at)  # must be a parseable ISO-8601 timestamp

    if set(per_season_frames.keys()) != set(SEASONS):
        raise SourceFeasibilityError(
            f"per_season_frames must cover exactly the bounded seasons {list(SEASONS)}; "
            f"got {sorted(per_season_frames.keys())}. Build fails closed."
        )

    players_index = _load_players_index(players_df)

    resolved: dict[int, dict] = {}
    for season in SEASONS:
        frames = per_season_frames[season]
        week_cols = _resolve_week_columns(frames["week"])
        reg_cols = _resolve_reg_columns(frames["reg"])
        _verify_season_match(season, frames["week"], frames["reg"], week_cols, reg_cols)
        week_records = _reg_week_records(frames["week"], week_cols)
        if not week_records:
            raise SourceFeasibilityError(
                f"Season {season} has no REG week-level rows. Build fails closed rather than "
                "emitting an empty/partial candidate."
            )
        _verify_week_span(season, week_records, week_cols)
        included_reg = _included_reg_records(frames["reg"], reg_cols)
        _verify_no_duplicate_grain(season, included_reg, reg_cols)
        resolved[season] = {
            "week_cols": week_cols,
            "reg_cols": reg_cols,
            "week_records": week_records,
            "included_reg": included_reg,
        }

    observed_fingerprints = verify_accepted_source_fingerprint(
        per_season_frames, players_index, accepted_fingerprint
    )

    # Identity gates (design SS10): the binding requirement under the current #218
    # evidence lock is exact 1.0 (verified inside the fingerprint gate above); the
    # family floor is retained only as defense in depth for lineage consistency.
    for season in SEASONS:
        join_rate = observed_fingerprints[season]["identity_join_rate_gsis_id"]
        if join_rate < IDENTITY_JOIN_RATE_FLOOR:
            raise SourceFeasibilityError(
                f"Season {season}: load_players() identity join rate {join_rate:.4f} is below "
                f"the family floor {IDENTITY_JOIN_RATE_FLOOR}. Build fails closed."
            )

    source_content_hashes = compute_source_content_hashes(per_season_frames, players_index)
    if accepted_source_content_hashes is not None:
        verify_accepted_content_hashes(source_content_hashes, accepted_source_content_hashes)

    records: list[dict] = []
    for season in SEASONS:
        season_data = resolved[season]
        week_cols = season_data["week_cols"]
        reg_cols = season_data["reg_cols"]
        team_context = _build_team_context(season_data["week_records"], week_cols)

        week_call = f"nflreadpy.load_player_stats(seasons=[{season}], summary_level='week')"
        reg_call = f"nflreadpy.load_player_stats(seasons=[{season}], summary_level='reg')"

        def _v(row: dict, field: str):
            column = reg_cols.get(field)
            return None if column is None else _json_safe_value(row.get(column))

        for row in season_data["included_reg"]:
            player_id = str(row.get(reg_cols["player_id"])).strip()
            position = str(row.get(reg_cols["position"]) or "").strip().upper()

            ctx = team_context.get(player_id)
            missing_fields: list[str] = [
                "games_missed",
                "snap_share",
                "routes_run",
                "route_participation",
                "red_zone_targets",
                "red_zone_carries",
            ]

            if ctx is None:
                teams_list: list[str] = []
                primary_team = None
                primary_team_rule_value = None
                team_weeks_value: list[dict] = []
                team_unknown = True
                weeks_observed = 0
                missing_fields.append("team_context")
            else:
                teams_list = ctx["teams"]
                primary_team = ctx["primary_team"]
                primary_team_rule_value = PRIMARY_TEAM_RULE if len(teams_list) > 1 else None
                team_weeks_value = ctx["team_weeks"]
                team_unknown = ctx["team_unknown"]
                weeks_observed = ctx["weeks_observed"]

            games_raw = _v(row, "games")
            games_played = None if games_raw is None else int(games_raw)
            _verify_games_and_trade_semantics(season, player_id, games_played, ctx)

            identity_row = players_index.get(player_id)
            if identity_row is None:
                # Unreachable behind the exact-1.0 fingerprint gate; asserted anyway so no
                # provisional row can ever be emitted by this build (design SS10, guard G-8).
                raise SourceEvidenceDriftError(
                    f"Season {season}: an included player failed the gsis_id identity join, "
                    "contradicting the exact-1.0 gate. No provisional identity row is ever "
                    "published by this build; it fails closed."
                )

            source_refs = [
                {
                    "source_name": reg_call,
                    "source_url": None,
                    "observed_at": generated_at,
                    "source_updated_at": None,
                    "confidence": "source_verified",
                    "notes": "Per-season REG production/usage rollup (nflverse). See artifact methodology.production_summary_source_note.",
                },
                {
                    "source_name": week_call,
                    "source_url": None,
                    "observed_at": generated_at,
                    "source_updated_at": None,
                    "confidence": "source_verified",
                    "notes": "Per-season week-level team-of-record (nflverse). See artifact methodology.team_context_source_note.",
                },
                {
                    "source_name": "nflreadpy.load_players()",
                    "source_url": None,
                    "observed_at": generated_at,
                    "source_updated_at": None,
                    "confidence": "source_verified",
                    "notes": "Player master identity/age/draft index (nflverse), keyed by gsis_id.",
                },
            ]

            birth_date_value = identity_row.get("birth_date")
            birth_date_json = _json_safe_value(birth_date_value)
            season_age_value = _season_age(birth_date_value, season)
            draft_year_value = _json_safe_value(identity_row.get("draft_year"))
            rookie_year_value = _json_safe_value(identity_row.get("rookie_season"))
            draft_round_value = _json_safe_value(identity_row.get("draft_round"))
            draft_pick_value = _json_safe_value(identity_row.get("draft_pick"))
            draft_team_value = _json_safe_value(identity_row.get("draft_team"))
            espn_id_value = _json_safe_value(identity_row.get("espn_id"))

            if birth_date_json is None:
                missing_fields.append("birth_date")
            if season_age_value is None and "season_age" not in missing_fields:
                missing_fields.append("season_age")
            for optional_field, optional_value in (
                ("draft_year", draft_year_value),
                ("draft_round", draft_round_value),
                ("draft_pick", draft_pick_value),
                ("draft_team", draft_team_value),
            ):
                if optional_value is None:
                    missing_fields.append(optional_field)

            career_year_value = None
            if rookie_year_value is not None:
                try:
                    career_year_value = int(season) - int(rookie_year_value) + 1
                except (TypeError, ValueError):
                    career_year_value = None
            if rookie_year_value is None:
                missing_fields.append("rookie_year")
            if career_year_value is None and "career_year" not in missing_fields:
                missing_fields.append("career_year")

            provider_ids = {"espn_id": espn_id_value, "sleeper_id": None} if espn_id_value else None

            season_ppr = _v(row, "fantasy_points_ppr")
            production_summary = {
                "season_ppr": season_ppr,
                "games_for_ppg": games_played,
                "season_ppg": (
                    _round_or_none(season_ppr / games_played, 2)
                    if (season_ppr is not None and games_played not in (None, 0))
                    else None
                ),
                "passing": {
                    "completions": _v(row, "completions"),
                    "attempts": _v(row, "attempts"),
                    "passing_yards": _v(row, "passing_yards"),
                    "passing_tds": _v(row, "passing_tds"),
                    "interceptions": _v(row, "passing_interceptions"),
                },
                "rushing": {
                    "rushing_attempts": _v(row, "carries"),
                    "rushing_yards": _v(row, "rushing_yards"),
                    "rushing_tds": _v(row, "rushing_tds"),
                },
                "receiving": {
                    "receiving_yards": _v(row, "receiving_yards"),
                    "receiving_tds": _v(row, "receiving_tds"),
                },
                "source_note": "nflverse season rollup, passthrough (see methodology.production_summary_source_note).",
            }

            usage_summary = {
                "targets": _v(row, "targets"),
                "receptions": _v(row, "receptions"),
                "rushing_attempts": _v(row, "carries"),
                "receiving_air_yards": _v(row, "receiving_air_yards"),
                "target_share": _round_or_none(_v(row, "target_share")),
                "air_yards_share": _round_or_none(_v(row, "air_yards_share")),
                "wopr": _round_or_none(_v(row, "wopr")),
                "racr": _round_or_none(_v(row, "racr")),
                "snap_share": None,
                "routes_run": None,
                "route_participation": None,
                "red_zone_targets": None,
                "red_zone_carries": None,
                "source_note": "unavailable fields are not exposed by source (see methodology.usage_summary_source_note); null, never zero.",
            }

            records.append(
                {
                    "player_id": player_id,
                    "player_name": str(_v(row, "player_name") or "").strip() or player_id,
                    "position": position,
                    "provider_ids": provider_ids,
                    "identity_confidence": "source_verified",
                    "season": season,
                    "season_type": SEASON_TYPE,
                    "generated_at": generated_at,
                    "observed_at": generated_at,
                    "source_updated_at": None,
                    "source_refs": source_refs,
                    "teams": teams_list,
                    "primary_team": primary_team,
                    "primary_team_rule": primary_team_rule_value,
                    "team_weeks": team_weeks_value,
                    "team_unknown": team_unknown,
                    "weeks_observed": weeks_observed,
                    "games_observed": weeks_observed,
                    "games_played": games_played,
                    "games_missed": None,
                    "coverage_status": _coverage_status(weeks_observed),
                    "coverage_notes": (
                        f"{weeks_observed} of up to 17 REG week numbers observed"
                        + (f"; multi-team ({len(teams_list)}), see primary_team_rule" if len(teams_list) > 1 else "")
                        + " (see artifact methodology for thresholds and team-context source)."
                    ),
                    "missing_fields": sorted(set(missing_fields)),
                    "production_summary": production_summary,
                    "usage_summary": usage_summary,
                    "birth_date": birth_date_json,
                    "season_age": season_age_value,
                    "draft_year": draft_year_value,
                    "draft_round": draft_round_value,
                    "draft_pick": draft_pick_value,
                    "draft_team": draft_team_value,
                    "rookie_year": rookie_year_value,
                    "career_year": career_year_value,
                }
            )

    if not records:
        raise SourceFeasibilityError(
            "No valid source-backed player-season coverage records were produced for the "
            "included positions. Build fails closed."
        )

    row_counts_by_position: dict[str, int] = {p: 0 for p in sorted(INCLUDED_POSITIONS)}
    row_counts_by_season: dict[str, int] = {str(season): 0 for season in SEASONS}
    for record in records:
        row_counts_by_position[record["position"]] += 1
        row_counts_by_season[str(record["season"])] += 1
    missing_positions = sorted(p for p in INCLUDED_POSITIONS if row_counts_by_position[p] == 0)
    if missing_positions:
        raise SourceFeasibilityError(
            f"No rows produced for required position(s) {missing_positions}. Build fails "
            "closed rather than emitting a partial-position candidate."
        )

    identity_join_rate_by_season = {
        str(season): observed_fingerprints[season]["identity_join_rate_gsis_id"] for season in SEASONS
    }
    overall_join_rate = round(
        sum(1 for r in records if r["identity_confidence"] == "source_verified") / len(records), 4
    )

    records.sort(key=lambda r: (r["season"], r["player_id"]))

    source_calls_executed = []
    for season in SEASONS:
        source_calls_executed.append(f"nflreadpy.load_player_stats(seasons=[{season}], summary_level='week')")
        source_calls_executed.append(f"nflreadpy.load_player_stats(seasons=[{season}], summary_level='reg')")
    source_calls_executed.append("nflreadpy.load_players()")

    payload = {
        "artifact_id": ARTIFACT_ID,
        "spec_version": "player_season_coverage_v0_candidate",
        "status": CANDIDATE_STATUS,
        "generated_at": generated_at,
        "seasons": list(SEASONS),
        "season_type_scope": [SEASON_TYPE],
        "included_positions": sorted(INCLUDED_POSITIONS),
        "row_grain": "player_id + season + season_type",
        "provenance": "nflreadpy.load_player_stats + nflreadpy.load_players",
        "source_path": (
            "nflverse player stats (per-season isolated week + reg summary-level calls) and "
            "player master index via nflreadpy"
        ),
        "generated_from": ["scripts/build_player_season_coverage_2015_2020_candidate.py", *source_calls_executed],
        "tracking_issue": TRACKING_ISSUE,
        "evidence_lock": {
            "accepted_main_sha": ACCEPTED_MAIN_SHA,
            "accepted_audit_script_blob": ACCEPTED_AUDIT_SCRIPT_BLOB,
            "accepted_design_doc": ACCEPTED_DESIGN_DOC,
            "accepted_design_blob": ACCEPTED_DESIGN_BLOB,
            "audit_evidence_reports": list(AUDIT_EVIDENCE_REPORTS),
            "required_nflreadpy_version": REQUIRED_NFLREADPY_VERSION,
        },
        "non_goals": [
            "not promoted/governed Forecast-ready data",
            "not a Forecast input today",
            "no active/inactive/IR/practice-squad availability status is asserted",
            "POST season_type out of scope for this build slice",
            "contains no 2021+ rows; never merges with the promoted 2021-2025 artifact "
            "(any merged candidate is a separately governed step)",
            "does not widen the promoted support window (2021-2025 REG remains the only promoted claim)",
        ],
        "methodology": {
            "primary_team_rule": PRIMARY_TEAM_RULE,
            "team_context_source_note": TEAM_CONTEXT_SOURCE_NOTE,
            "coverage_status_rule": COVERAGE_STATUS_RULE,
            "games_cap_note": GAMES_CAP_NOTE,
            "age_reference_note": AGE_REFERENCE_NOTE,
            "production_summary_source_note": (
                "nflreadpy.load_player_stats(summary_level='reg').fantasy_points_ppr and yardage/TD "
                "fields are passed through directly (nflverse's own season rollup), not recomputed "
                "by this build."
            ),
            "usage_summary_source_note": (
                "snap_share/routes_run/route_participation/red_zone_* are not exposed by "
                "nflreadpy.load_player_stats and remain unavailable (null) on every row, never zero."
            ),
        },
        "identity_join_rate": overall_join_rate,
        "identity_join_rate_by_season": identity_join_rate_by_season,
        "row_counts_by_position": row_counts_by_position,
        "row_counts_by_season": row_counts_by_season,
        "records": records,
    }

    build_evidence = {
        "observed_fingerprints": observed_fingerprints,
        "accepted_fingerprint": (
            accepted_fingerprint if accepted_fingerprint is not None else ACCEPTED_SOURCE_FINGERPRINT_2015_2020
        ),
        "source_content_hashes": source_content_hashes,
        "source_calls_executed": source_calls_executed,
    }
    return payload, build_evidence


# ---------------------------------------------------------------------------
# Validation (unchanged validator reuse + era re-verification; design SS11)
# ---------------------------------------------------------------------------


def _load_validator_module():
    module_path = REPO_ROOT / VALIDATOR_RELPATH
    spec = spec_from_file_location("validate_player_season_coverage_v0", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load validator module from {module_path}")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    # The shared validator resolves its schema path relative to the process working
    # directory; anchor it to the repository root in memory. The validator file
    # itself is reused byte-for-byte unchanged.
    module.SCHEMA_PATH = REPO_ROOT / SCHEMA_RELPATH
    return module


def verify_era_rules_on_payload(payload: dict) -> list[str]:
    """Era-rule re-verification against the assembled payload (recorded in the
    validation result alongside the unchanged shared validator's outcome)."""
    errors: list[str] = []
    if payload.get("seasons") != list(SEASONS):
        errors.append(f"seasons must be exactly {list(SEASONS)}")
    if payload.get("season_type_scope") != [SEASON_TYPE]:
        errors.append("season_type_scope must be exactly ['REG']")
    if payload.get("status") != CANDIDATE_STATUS:
        errors.append(f"status must be exactly '{CANDIDATE_STATUS}'")
    for idx, record in enumerate(payload.get("records", [])):
        if record.get("season") not in SEASONS:
            errors.append(f"record[{idx}]: season {record.get('season')} outside the bounded 2015-2020 window")
        if record.get("season_type") != SEASON_TYPE:
            errors.append(f"record[{idx}]: season_type must be REG")
        if record.get("position") not in INCLUDED_POSITIONS:
            errors.append(f"record[{idx}]: position {record.get('position')} not in the included set")
        weeks_observed = record.get("weeks_observed") or 0
        if weeks_observed > 17:
            errors.append(f"record[{idx}]: weeks_observed {weeks_observed} exceeds the 17-week era span")
        expected_status = _coverage_status(weeks_observed)
        if record.get("coverage_status") != expected_status:
            errors.append(
                f"record[{idx}]: coverage_status {record.get('coverage_status')} does not match the "
                f"historical rule (expected {expected_status})"
            )
        games_played = record.get("games_played")
        if games_played is not None:
            if games_played > ABSOLUTE_GAMES_CAP_2015_2020:
                errors.append(f"record[{idx}]: games_played {games_played} exceeds the absolute cap 17")
            if games_played > weeks_observed:
                errors.append(f"record[{idx}]: games_played {games_played} exceeds weeks_observed {weeks_observed}")
            if games_played > ORDINARY_GAMES_CAP_2015_2020 and len(record.get("teams") or []) < 2:
                errors.append(
                    f"record[{idx}]: games_played {games_played} above the ordinary cap without "
                    "multi-team week-level evidence"
                )
        if record.get("identity_confidence") != "source_verified":
            errors.append(
                f"record[{idx}]: identity_confidence {record.get('identity_confidence')!r} -- no "
                "publishable provisional identity state exists in this build"
            )
    return errors


def validate_payload_for_publication(payload: dict) -> dict:
    """Run the unchanged shared validator plus the era-rule re-verification.

    Returns the machine-readable validation-result content on success; raises
    CandidateValidationError (artifact withheld, nothing written) on any failure.
    """
    validator = _load_validator_module()
    validator_errors = validator.validate_payload(payload)
    era_errors = verify_era_rules_on_payload(payload)
    if validator_errors or era_errors:
        raise CandidateValidationError(
            f"post-assembly validation failed: {len(validator_errors)} shared-validator error(s), "
            f"{len(era_errors)} era-rule error(s): "
            + "; ".join((validator_errors + era_errors)[:50])
        )
    return {
        "report_id": "player_season_coverage_v0_2015_2020_candidate_validation",
        "status": "pass",
        "artifact_id": payload["artifact_id"],
        "artifact_status": payload["status"],
        "generated_at": payload["generated_at"],
        "validator": VALIDATOR_RELPATH,
        "schema": SCHEMA_RELPATH,
        "validator_errors": [],
        "era_rule_errors": [],
        "era_rules_verified": [
            "seasons exactly 2015-2020, REG only, QB/RB/WR/TE only",
            "weeks_observed <= 17 on every record",
            f"coverage_status per historical rule (full_season >= {FULL_SEASON_MIN_WEEKS_2015_2020} of 17)",
            f"games caps ({ORDINARY_GAMES_CAP_2015_2020} ordinary / {ABSOLUTE_GAMES_CAP_2015_2020} absolute) "
            "with source-backed multi-team evidence for overages",
            "identity_confidence source_verified on every record (no provisional rows)",
        ],
        "record_count": len(payload["records"]),
        "tracking_issue": TRACKING_ISSUE,
    }


# ---------------------------------------------------------------------------
# Output rendering (design SS5, SS13)
# ---------------------------------------------------------------------------


def candidate_output_paths(base_dir: Path | None = None) -> dict[str, Path]:
    """The five final output paths, in the fixed publication (phase-2 commit) order."""
    base = Path(base_dir) if base_dir is not None else OUTPUT_BASE_DIR
    return {
        "artifact": base / ARTIFACT_RELPATH,
        "manifest": base / MANIFEST_RELPATH,
        "validation": base / VALIDATION_RELPATH,
        "report_json": base / REPORT_JSON_RELPATH,
        "report_md": base / REPORT_MD_RELPATH,
    }


def collect_environment_metadata(generated_at: str) -> dict:
    def _dist_version(name: str) -> str | None:
        try:
            return importlib_metadata.version(name)
        except importlib_metadata.PackageNotFoundError:
            return None

    return {
        "python_version": platform.python_version(),
        "nflreadpy_version": _dist_version("nflreadpy"),
        "polars_version": _dist_version("polars"),
        "os_platform": platform.platform(),
        "build_timestamp_utc": generated_at,
        "evidence_lock": {
            "accepted_main_sha": ACCEPTED_MAIN_SHA,
            "accepted_audit_script_blob": ACCEPTED_AUDIT_SCRIPT_BLOB,
            "required_nflreadpy_version": REQUIRED_NFLREADPY_VERSION,
        },
    }


def _coverage_status_distribution(payload: dict) -> dict[str, int]:
    distribution: dict[str, int] = {}
    for record in payload["records"]:
        distribution[record["coverage_status"]] = distribution.get(record["coverage_status"], 0) + 1
    return {status: distribution[status] for status in sorted(distribution)}


def _per_season_position_counts(payload: dict) -> dict[str, dict[str, int]]:
    counts: dict[str, dict[str, int]] = {
        str(season): {p: 0 for p in sorted(INCLUDED_POSITIONS)} for season in SEASONS
    }
    for record in payload["records"]:
        counts[str(record["season"])][record["position"]] += 1
    return counts


def _reconciliation_by_season(build_evidence: dict) -> dict[str, dict]:
    """Reconciliation against the accepted #218 audited per-season aggregates. This is a
    gate, not merely informational: it restates the fingerprint verification that already
    had to pass before staging, so a published set can never disagree with #218."""
    reconciliation: dict[str, dict] = {}
    for season in SEASONS:
        expected = build_evidence["accepted_fingerprint"][season]
        observed = build_evidence["observed_fingerprints"][season]
        reconciliation[str(season)] = {
            "expected_218": expected,
            "observed": observed,
            "match": expected == {key: observed.get(key) for key in expected},
        }
    return reconciliation


def render_candidate_manifest(payload: dict, artifact_sha256: str, environment: dict, build_evidence: dict) -> dict:
    """Candidate-scoped evidence manifest (design SS5). Deliberately not a promotion
    manifest: it must never carry promoted-envelope fields and confers no governed status."""
    return {
        "manifest_id": f"{ARTIFACT_ID}.MANIFEST",
        "status": CANDIDATE_STATUS,
        "artifact_path": ARTIFACT_RELPATH,
        "artifact_id": payload["artifact_id"],
        "artifact_sha256": artifact_sha256,
        "generated_at": payload["generated_at"],
        "seasons": payload["seasons"],
        "season_type_scope": payload["season_type_scope"],
        "included_positions": payload["included_positions"],
        "record_count": len(payload["records"]),
        "row_counts_by_position": payload["row_counts_by_position"],
        "row_counts_by_season": payload["row_counts_by_season"],
        "row_counts_by_season_position": _per_season_position_counts(payload),
        "identity_join_rate": payload["identity_join_rate"],
        "identity_join_rate_by_season": payload["identity_join_rate_by_season"],
        "environment": environment,
        "evidence_lock": payload["evidence_lock"],
        "source_calls_executed": build_evidence["source_calls_executed"],
        "source_content_hashes": build_evidence["source_content_hashes"],
        "tracking_issue": TRACKING_ISSUE,
        "non_promotion_note": (
            "This is candidate-scoped evidence, not a promotion manifest. It confers no "
            "governed status and authorizes no consumer availability."
        ),
    }


def render_build_report_json(payload: dict, artifact_sha256: str, environment: dict, build_evidence: dict) -> dict:
    return {
        "report_id": "player_season_coverage_v0_2015_2020_candidate_build",
        "status": CANDIDATE_STATUS,
        "artifact_id": payload["artifact_id"],
        "artifact_sha256": artifact_sha256,
        "generated_at": payload["generated_at"],
        "seasons": payload["seasons"],
        "record_count": len(payload["records"]),
        "row_counts_by_position": payload["row_counts_by_position"],
        "row_counts_by_season": payload["row_counts_by_season"],
        "row_counts_by_season_position": _per_season_position_counts(payload),
        "coverage_status_distribution": _coverage_status_distribution(payload),
        "identity_join_rate": payload["identity_join_rate"],
        "identity_join_rate_by_season": payload["identity_join_rate_by_season"],
        "environment": environment,
        "source_calls_executed": build_evidence["source_calls_executed"],
        "source_content_hashes": build_evidence["source_content_hashes"],
        "reconciliation_against_218_audit": _reconciliation_by_season(build_evidence),
        "tracking_issue": TRACKING_ISSUE,
    }


def render_build_report_md(payload: dict, artifact_sha256: str, environment: dict, build_evidence: dict) -> str:
    """Human-readable build report. Aggregates only -- never player names or IDs."""
    lines: list[str] = []
    lines.append("# Candidate Build Report: `player_season_coverage_v0` 2015-2020 REG")
    lines.append("")
    lines.append(f"- **status:** `{CANDIDATE_STATUS}`")
    lines.append(f"- **artifact_id:** `{payload['artifact_id']}`")
    lines.append(f"- **artifact sha256:** `{artifact_sha256}`")
    lines.append(f"- **generated_at:** `{payload['generated_at']}`")
    lines.append(f"- **tracking issue:** {TRACKING_ISSUE}")
    lines.append(f"- **record count:** {len(payload['records'])}")
    lines.append(f"- **identity join rate:** {payload['identity_join_rate']}")
    lines.append("")
    lines.append("## Environment")
    lines.append("")
    for key in ("python_version", "nflreadpy_version", "polars_version", "os_platform", "build_timestamp_utc"):
        lines.append(f"- {key}: `{environment.get(key)}`")
    lines.append(
        f"- evidence lock: accepted main `{ACCEPTED_MAIN_SHA}`, audit-script blob "
        f"`{ACCEPTED_AUDIT_SCRIPT_BLOB}`, required nflreadpy `{REQUIRED_NFLREADPY_VERSION}`"
    )
    lines.append("")
    lines.append("## Counts by season and position")
    lines.append("")
    lines.append("| season | QB | RB | WR | TE | total |")
    lines.append("|---|---|---|---|---|---|")
    per_season = _per_season_position_counts(payload)
    for season in SEASONS:
        counts = per_season[str(season)]
        total = payload["row_counts_by_season"][str(season)]
        lines.append(
            f"| {season} | {counts['QB']} | {counts['RB']} | {counts['WR']} | {counts['TE']} | {total} |"
        )
    lines.append("")
    lines.append("## Coverage-status distribution")
    lines.append("")
    for status, count in _coverage_status_distribution(payload).items():
        lines.append(f"- {status}: {count}")
    lines.append("")
    lines.append("## Reconciliation against the accepted #218 audit (gate, not informational)")
    lines.append("")
    lines.append("| season | expected included rows (#218) | observed | max games (#218) | observed | match |")
    lines.append("|---|---|---|---|---|---|")
    reconciliation = _reconciliation_by_season(build_evidence)
    for season in SEASONS:
        entry = reconciliation[str(season)]
        lines.append(
            f"| {season} | {entry['expected_218']['reg_level_rows_reg_qb_rb_wr_te']} | "
            f"{entry['observed']['reg_level_rows_reg_qb_rb_wr_te']} | "
            f"{entry['expected_218']['max_games_reg_level']} | "
            f"{entry['observed']['max_games_reg_level']} | {entry['match']} |"
        )
    lines.append("")
    lines.append("## Source-content hashes (13)")
    lines.append("")
    for season in SEASONS:
        lines.append(
            f"- week-level {season}: `{build_evidence['source_content_hashes']['week_level_by_season'][str(season)]}`"
        )
    for season in SEASONS:
        lines.append(
            f"- REG-summary {season}: `{build_evidence['source_content_hashes']['reg_summary_by_season'][str(season)]}`"
        )
    lines.append(
        f"- joined identity fields: `{build_evidence['source_content_hashes']['joined_identity_fields']}`"
    )
    lines.append("")
    lines.append("## Boundaries")
    lines.append("")
    lines.append(
        "This is a candidate/evidence artifact only. It is not promoted, contains no 2021+ rows, "
        "never merges with the promoted 2021-2025 artifact, does not widen the promoted support "
        "window (2021-2025 REG only), and authorizes no Forecast, ADP, research, or product behavior."
    )
    lines.append("")
    return "\n".join(lines)


def build_output_set(payload: dict, build_evidence: dict, environment: dict, base_dir: Path | None = None) -> dict[Path, str]:
    """Render the complete five-output publication set (validation included).

    Raises CandidateValidationError on any post-assembly validation failure (nothing
    is written) and enforces the support-claim guard on every rendered output.
    """
    validation_result = validate_payload_for_publication(payload)

    artifact_text = _serialize_json_output(payload)
    artifact_sha256 = _sha256_text(artifact_text)
    validation_result["artifact_sha256"] = artifact_sha256

    manifest = render_candidate_manifest(payload, artifact_sha256, environment, build_evidence)
    report_json = render_build_report_json(payload, artifact_sha256, environment, build_evidence)
    report_md = render_build_report_md(payload, artifact_sha256, environment, build_evidence)

    paths = candidate_output_paths(base_dir)
    contents = {
        paths["artifact"]: artifact_text,
        paths["manifest"]: _serialize_json_output(manifest),
        paths["validation"]: _serialize_json_output(validation_result),
        paths["report_json"]: _serialize_json_output(report_json),
        paths["report_md"]: report_md if report_md.endswith("\n") else f"{report_md}\n",
    }

    for path, text in contents.items():
        for variant in PROHIBITED_SUPPORT_CLAIM_VARIANTS:
            if variant in text:
                raise CandidateValidationError(
                    f"support-claim guard: output {path.name} contains the prohibited availability "
                    "claim. The artifact set is withheld."
                )
    for rendered in (manifest, report_json, validation_result):
        status_value = rendered.get("status")
        if status_value not in (CANDIDATE_STATUS, "pass"):
            raise CandidateValidationError(
                f"support-claim guard: unexpected status {status_value!r} in a rendered output."
            )
    return contents


# ---------------------------------------------------------------------------
# Journaled set publication (design SS13)
# ---------------------------------------------------------------------------


def _write_bytes(path: Path, data: bytes) -> None:
    path.write_bytes(data)


def _remove_path(path: Path) -> None:
    path.unlink()


def _restore_backup(backup_path: Path, final_path: Path) -> None:
    os.rename(backup_path, final_path)


def _residue_candidates(final_paths: list[Path]) -> list[Path]:
    residue: list[Path] = []
    for final_path in final_paths:
        directory = final_path.parent
        if not directory.exists():
            continue
        for pattern in (f"{final_path.name}.tmp-*", f"{final_path.name}.prev-*"):
            residue.extend(sorted(directory.glob(pattern)))
    return residue


def publish_output_set(contents: dict[Path, str], *, after_install=None) -> None:
    """Publish the output set as an all-or-nothing journaled transaction.

    Phase 0 (residue preflight): pre-existing .tmp-*/.prev-* files matching any final
    name abort immediately -- no staging, no cleanup, leftovers untouched (crash
    residue may hold the only recoverable prior copy; recovery is an operator step).

    Phase 1 (stage): every output is fully written to `<final>.tmp-<pid>` in its
    destination directory. Any failure deletes all temps and re-raises; the pre-run
    state (including the absence of never-existing outputs) remains intact.

    Phase 2 (commit): in fixed order, an existing final is renamed to
    `<final>.prev-<pid>`, then the staged temp is os.replace'd into place; a journal
    records existed-before/backup/installed per path. Backups are deleted only after
    all installations succeed. On any caught phase-2 failure, rollback runs in
    reverse installation order restoring the exact pre-run state; if rollback itself
    fails, every recoverable backup is retained and a fatal torn-state diagnostic
    names the per-path journal state.

    `after_install` is a test-only fault-injection hook invoked after each phase-2
    installation; production callers leave it None.

    This contract covers every CAUGHT failure. It does not claim process-crash
    atomicity across files: an external hard kill mid-phase-2 can leave a torn but
    detectable state, which verify_published_set() must reject.
    """
    final_paths = list(contents.keys())
    pid = os.getpid()

    residue = _residue_candidates(final_paths)
    if residue:
        raise ResidueError(
            "residue preflight failed: pre-existing staging/backup files found: "
            + ", ".join(str(p) for p in residue)
            + ". Nothing was staged and the residue was left exactly as found; recovery "
            "(inspect, then restore or clear) is a deliberate operator step, never an "
            "automatic action of a rerun."
        )

    temp_paths: dict[Path, Path] = {}
    try:
        for final_path in final_paths:
            final_path.parent.mkdir(parents=True, exist_ok=True)
            temp_path = final_path.parent / f"{final_path.name}.tmp-{pid}"
            # Recorded before writing (not after): if _write_bytes raises after
            # creating a partial file (e.g. disk full mid-write), cleanup below must
            # still find and remove it, or the leftover .tmp-<pid> would fail the
            # next run's phase-0 residue preflight.
            temp_paths[final_path] = temp_path
            _write_bytes(temp_path, contents[final_path].encode("utf-8"))
    except BaseException as exc:
        # Every tracked temp is attempted regardless of an earlier cleanup failure: a
        # single stubborn temp (e.g. a permission error) must not stop cleanup of the
        # rest or mask the original staging error with an unrelated one.
        cleanup_failures: list[str] = []
        for temp_path in temp_paths.values():
            try:
                temp_path.unlink()
            except FileNotFoundError:
                pass
            except OSError as cleanup_exc:
                cleanup_failures.append(f"{temp_path.name}: {cleanup_exc}")
        if cleanup_failures:
            raise PublicationError(
                f"phase-1 staging failed ({exc}); additionally {len(cleanup_failures)} "
                f"temp file(s) could not be removed during cleanup: {'; '.join(cleanup_failures)}. "
                "Pre-run state for already-existing outputs is intact, but the named temp(s) "
                "remain on disk and will require operator clearance before the next run's "
                "residue preflight will pass."
            ) from exc
        raise PublicationError(
            f"phase-1 staging failed ({exc}); all temps removed, pre-run state intact, nothing published."
        ) from exc

    journal: list[dict] = [
        {
            "final": final_path,
            "existed_before": final_path.exists(),
            "backup": final_path.parent / f"{final_path.name}.prev-{pid}",
            "backup_made": False,
            "installed": False,
        }
        for final_path in final_paths
    ]

    try:
        for entry in journal:
            final_path = entry["final"]
            if entry["existed_before"]:
                os.rename(final_path, entry["backup"])
                entry["backup_made"] = True
            os.replace(temp_paths[final_path], final_path)
            entry["installed"] = True
            if after_install is not None:
                after_install(final_path)
    except BaseException as exc:
        try:
            for entry in reversed(journal):
                if entry["installed"] and entry["final"].exists():
                    _remove_path(entry["final"])
                if entry["backup_made"]:
                    _restore_backup(entry["backup"], entry["final"])
            for final_path, temp_path in temp_paths.items():
                if temp_path.exists():
                    temp_path.unlink()
        except BaseException as rollback_exc:
            journal_state = "; ".join(
                f"{entry['final'].name}: existed_before={entry['existed_before']} "
                f"backup_made={entry['backup_made']} installed={entry['installed']}"
                for entry in journal
            )
            raise RollbackFailureError(
                f"FATAL torn state: publication failed ({exc}) and rollback also failed "
                f"({rollback_exc}). Every recoverable backup has been deliberately retained "
                f"on disk (never deleted after a rollback failure). Per-path journal state: "
                f"{journal_state}. Operator recovery required."
            ) from rollback_exc
        raise PublicationError(
            f"phase-2 commit failed ({exc}); rollback restored the exact pre-run state "
            "(prior bytes for pre-existing outputs, absence for never-existing outputs)."
        ) from exc

    cleanup_failures: list[str] = []
    for entry in journal:
        if entry["backup_made"]:
            try:
                entry["backup"].unlink()
            except OSError as exc:
                cleanup_failures.append(f"{entry['backup'].name}: {exc}")
    if cleanup_failures:
        raise BackupCleanupError(
            "publication succeeded (all five outputs were correctly installed), but "
            f"{len(cleanup_failures)} recoverable backup(s) could not be removed: "
            + "; ".join(cleanup_failures)
            + ". This is not data loss and no output was lost or torn -- the retained "
            "backup(s) must be cleared by an operator before the next run, since phase-0 "
            "residue preflight will otherwise reject it."
        )


def verify_published_set(base_dir: Path | None = None, *, check_residue: bool = True) -> None:
    """Mandatory torn-state rejection gate after publication (design SS13).

    All five outputs must exist and the manifest's recorded artifact sha256 must match
    the artifact bytes on disk. By default (check_residue=True, the strict/general
    case used by every caller except one) any leftover .tmp-*/.prev-* file is also
    treated as torn-state evidence -- from the outside, a caller generally cannot tell
    a genuinely torn install apart from benign backup-cleanup residue just by looking
    at the filesystem. check_residue=False exists only for main()'s own recovery path
    immediately after it has caught a BackupCleanupError: at that specific call site
    the exception's origin already proves installation fully succeeded and the only
    residue is the one named, retained backup.
    """
    paths = candidate_output_paths(base_dir)
    missing = [str(path) for path in paths.values() if not path.exists()]
    if missing:
        raise TornStateError(f"torn output state: missing published output(s): {', '.join(missing)}")
    if check_residue:
        residue = _residue_candidates(list(paths.values()))
        if residue:
            raise TornStateError(
                "torn output state: staging/backup residue remains after publication: "
                + ", ".join(str(p) for p in residue)
            )
    manifest = json.loads(paths["manifest"].read_text(encoding="utf-8"))
    artifact_sha256 = _sha256_text(paths["artifact"].read_text(encoding="utf-8"))
    if manifest.get("artifact_sha256") != artifact_sha256:
        raise TornStateError(
            "torn output state: manifest artifact_sha256 does not match the artifact bytes on "
            "disk. The output set must be rejected before any commit or review trusts it."
        )


# ---------------------------------------------------------------------------
# Guards and network-backed entry point
# ---------------------------------------------------------------------------


def assert_paths_not_under_exports(paths: dict[str, Path]) -> None:
    """Promoted-path guard (design SS5, N-17): this builder must never write under
    exports/** generally and exports/promoted/** specifically. Checked before any
    network call."""
    exports_dir = (REPO_ROOT / "exports").resolve()
    for path in paths.values():
        resolved = path.resolve()
        if resolved == exports_dir or exports_dir in resolved.parents:
            raise SourceFeasibilityError(
                f"Refusing to write candidate output under a promoted path: {resolved}. "
                "This build must never write to exports/** (exports/promoted/** included)."
            )


def _load_week_frame(season: int):
    import nflreadpy as nfl

    return nfl.load_player_stats(seasons=[season], summary_level="week")


def _load_reg_frame(season: int):
    import nflreadpy as nfl

    return nfl.load_player_stats(seasons=[season], summary_level="reg")


def _load_players_frame():
    import nflreadpy as nfl

    return nfl.load_players()


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--generated-at",
        default=None,
        help=(
            "Pinned ISO-8601 generation timestamp. Two runs with the same value against "
            "unchanged upstream data are byte-identical. Defaults to now-UTC."
        ),
    )
    parser.add_argument(
        "--accepted-source-hashes",
        default=None,
        help=(
            "Path to a JSON file holding the thirteen accepted source-content hashes of a "
            "previously accepted (G5) candidate, overriding the default auto-discovery "
            "below. Ordinarily this flag is unnecessary: if the candidate manifest at its "
            "standard output path already exists on disk, its recorded source_content_hashes "
            "are loaded and enforced automatically -- a rebuild over an existing manifest "
            "must reproduce them exactly or abort before staging with a value-drift "
            "diagnostic, without depending on this flag being remembered. A genuinely first "
            "build (no manifest yet on disk) has no lock to enforce."
        ),
    )
    return parser.parse_args(argv)


_REQUIRED_SOURCE_CONTENT_HASH_KEYS = ("week_level_by_season", "reg_summary_by_season", "joined_identity_fields")


def _load_accepted_source_content_hashes(
    manifest_path: Path, explicit_path: str | None
) -> dict | None:
    """Resolve the source-content hash lock a rebuild must reproduce.

    An explicit --accepted-source-hashes path always wins. Otherwise, if a candidate
    manifest already exists at its standard output path (i.e. a candidate was
    previously published from this location), its recorded hashes are loaded and
    enforced automatically -- the §6 post-G5 rebuild lock must not depend on an
    operator remembering to pass a flag. A first-ever build (no prior manifest) has
    no lock to enforce.

    An existing manifest that is unreadable, unparsable, or missing a valid
    source_content_hashes object is never treated as equivalent to "no lock exists":
    that would let a rebuild silently overwrite an already-published candidate despite
    unverifiable value-level drift. It fails closed instead.
    """
    if explicit_path:
        return json.loads(Path(explicit_path).read_text(encoding="utf-8"))
    if not manifest_path.exists():
        return None
    try:
        existing_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SourceFeasibilityError(
            f"existing candidate manifest at {manifest_path} could not be read or parsed "
            f"({exc}); a rebuild cannot verify the required post-G5 hash lock (design §6) "
            "against it. Build fails closed rather than treating a damaged manifest as "
            "'no lock exists'."
        ) from exc
    hashes = existing_manifest.get("source_content_hashes")
    if (
        not isinstance(hashes, dict)
        or not all(hashes.get(key) for key in _REQUIRED_SOURCE_CONTENT_HASH_KEYS)
    ):
        raise SourceFeasibilityError(
            f"existing candidate manifest at {manifest_path} is missing a valid "
            "source_content_hashes lock (design §6 requires every rebuild over an "
            "already-published candidate to reproduce its accepted hashes exactly). "
            "An incomplete or damaged manifest must never be treated as 'no lock exists'; "
            "build fails closed rather than silently republishing over it."
        )
    return hashes


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    generated_at = args.generated_at or datetime.now(timezone.utc).isoformat()

    paths = candidate_output_paths()
    assert_paths_not_under_exports(paths)  # before any network call

    verify_nflreadpy_version(_installed_nflreadpy_version())  # before any source call

    accepted_source_content_hashes = _load_accepted_source_content_hashes(
        paths["manifest"], args.accepted_source_hashes
    )

    # Per-season isolated approved source calls (design SS6): six independent
    # week-level and six independent reg-level calls. Any season's failure fails the
    # whole build -- there is no five-season candidate.
    per_season_frames: dict[int, dict] = {}
    for season in SEASONS:
        try:
            per_season_frames[season] = {
                "week": _load_week_frame(season),
                "reg": _load_reg_frame(season),
            }
        except Exception as exc:
            raise SourceFeasibilityError(
                f"Season {season} source call failed ({exc}). The whole build fails closed; "
                "no five-season candidate is ever emitted."
            ) from exc

    try:
        players_df = _load_players_frame()
    except Exception as exc:
        raise SourceFeasibilityError(
            f"nflreadpy.load_players() failed ({exc}). Identity is required, not optional; "
            "build fails closed."
        ) from exc

    payload, build_evidence = build_candidate_payload(
        per_season_frames,
        players_df,
        generated_at,
        accepted_source_content_hashes=accepted_source_content_hashes,
    )

    environment = collect_environment_metadata(generated_at)
    contents = build_output_set(payload, build_evidence, environment)
    try:
        publish_output_set(contents)
    except BackupCleanupError as exc:
        # All five outputs installed and were already sha256-verified as part of that
        # installation; only a stale backup could not be removed afterward. Per design
        # SS13's exit-code contract, exit 0 means "candidate built, validated, all
        # outputs written" -- that remains true here, so this must not be reported as
        # exit 1 ("no candidate exists from this run"). The general strict residue scan
        # is skipped only at this specific call site, since the exception's own origin
        # already proves the retained backup is benign, not evidence of a torn install.
        verify_published_set(check_residue=False)
        print(f"WARNING: {exc}", file=sys.stderr)
    else:
        verify_published_set()

    print(f"Wrote 2015-2020 candidate output set under: {OUTPUT_BASE_DIR}")
    print(f"Record count: {len(payload['records'])}")
    print(f"Identity join rate: {payload['identity_join_rate']}")
    print(f"Row counts by position: {payload['row_counts_by_position']}")
    print(f"Row counts by season: {payload['row_counts_by_season']}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except CandidateValidationError as exc:
        # Post-assembly validation failure: the artifact is withheld, nothing was
        # written, and diagnostics (including the withheld validation-result path)
        # go to stderr only.
        print(f"VALIDATION FAILURE (artifact withheld, nothing written): {exc}", file=sys.stderr)
        print(f"Withheld validation-result path: {candidate_output_paths()['validation']}", file=sys.stderr)
        raise SystemExit(2) from exc
    except SystemExit:
        raise
    except Exception as exc:  # fail closed with clear reason
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

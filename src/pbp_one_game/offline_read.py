"""Offline one-game play-by-play (PBP) receipt verification and bounded event read.

Scope (Research #22 first PR, TIBER-Data owning repository):

- Accept an explicitly supplied local source file with an expected byte count and
  expected SHA-256. The exact bytes are hashed BEFORE parsing. A missing file, size
  mismatch, digest mismatch, or unsupported format stops processing with a precise
  rejection and no side effect. There is no download, no replacement path guessing.
- One supported format: parquet (magic-byte checked), read with polars, which is an
  existing declared repository dependency (`pyproject.toml`). No multi-format framework.
  A parquet file that passes the magic-byte check but fails to parse produces a bounded
  `parse_failure` rejection rather than an uncaught exception.
- Require an explicit requested season, date, away team, and home team. Game identity
  is derived from invariant source identity columns only; event-varying and game-level
  descriptor columns are preserved but never used to reject a game. Raw source identity
  values are preserved verbatim. Zero or multiple matching games is an unresolved
  result. No game ID is synthesized; no substitute date or game is ever selected.
- Inspect the source schema before projecting columns. Absent columns, null values,
  explicit false/zero values, and uninspected columns are reported as distinct states.
- Read lazily: the identity scan projects identity columns only, and the game read
  pushes `game_id == <matched>` into the parquet scan so only the located game's rows
  are materialized. Physical row-group I/O is disclosed separately from logical scope.
- Return a local, non-canonical receipt plus a bounded game inventory. Row count and
  distinct (game_id, play_id) count are reported separately; neither is an official
  snap denominator. Duplicated keys are classified as identical or conflicting and are
  never silently discarded.
- Team possession sequence is derived from ordered `posteam` runs bounded by the
  provider drive number. A team's N-th possession is selected only when the provider
  numbering supports that association for the ENTIRE prefix used to count N; any
  earlier null drive, non-contiguous or non-monotone drive, unattributed row carrying
  an unaccounted drive value, or conflicting duplicate that could alter order, team, or
  drive leaves the selection unresolved.
- Output is capped at MAX_EVENT_ROWS event rows plus at most
  MAX_BOUNDARY_EVENTS_PER_SIDE boundary rows on each side, with explicit truncation.
- The only non-reproducible value across runs of the same input and reader revision is
  `receipt.times.processing_time`, and it is never used as ingestion, retrieval, or
  publication time.

This module deliberately imports no network, database, or application code.
"""

from __future__ import annotations

import hashlib
import io
import json
import math
import re
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
from typing import Any

READER_NAME = "pbp_one_game_offline_read"
READER_VERSION = "0.2.0"
SUPPORTED_FORMAT = "parquet"
PARQUET_MAGIC = b"PAR1"

MAX_EVENT_ROWS = 40
MAX_BOUNDARY_EVENTS_PER_SIDE = 2
MAX_DESCRIPTOR_VALUES_REPORTED = 5

# Mirrors the existing candidate builders (team_week_raw_v0, formation_summary_v0).
TEAM_CODE_CANONICAL_MAP = {"LA": "LAR"}

# Documented nflverse play-by-play column names. Existence is INSPECTED at read time and
# reported; nothing below is assumed to exist in a given source file.
#
# Invariant game identity: the ONLY columns whose distinct-tuple count decides whether a
# game's metadata is consistent. Every one of them is required for certification.
GAME_IDENTITY_COLUMNS: tuple[str, ...] = (
    "game_id", "season", "game_date", "home_team", "away_team",
)
REQUIRED_IDENTITY_COLUMNS: tuple[str, ...] = GAME_IDENTITY_COLUMNS
# Game-level descriptors: preserved for the matched game and reported with their distinct
# values, but never used to reject a game. Variation within a game is disclosed, not fatal.
GAME_DESCRIPTOR_COLUMNS: tuple[str, ...] = (
    "week", "season_type", "old_game_id", "nfl_api_id", "start_time", "stadium", "location",
)
PLAY_KEY_COLUMNS: tuple[str, ...] = ("game_id", "play_id")

# Families inventoried for the bounded event read. `time_of_day` is an event-level
# timestamp and belongs here, not in game identity.
INVENTORY_FIELD_FAMILIES: dict[str, tuple[str, ...]] = {
    "possession_order": (
        "posteam", "defteam", "posteam_type", "drive", "fixed_drive", "fixed_drive_result",
        "drive_play_id_started", "drive_play_id_ended", "drive_start_transition",
        "drive_end_transition",
    ),
    "quarter_clock": (
        "qtr", "game_half", "time", "quarter_seconds_remaining", "half_seconds_remaining",
        "game_seconds_remaining", "quarter_end", "time_of_day",
    ),
    "down_distance": ("down", "ydstogo", "goal_to_go"),
    "field_position": ("yardline_100", "side_of_field", "yrdln"),
    "event_outcome": (
        "play_type", "play_type_nfl", "desc", "yards_gained", "touchdown", "complete_pass",
        "incomplete_pass", "interception", "fumble", "fumble_lost", "sack", "first_down",
        "qb_dropback", "qb_scramble", "qb_kneel", "qb_spike", "aborted_play",
        "two_point_attempt",
    ),
    "penalty_no_play": (
        "penalty", "penalty_team", "penalty_type", "penalty_yards", "penalty_player_id",
        "play_deleted",
    ),
    "actor_ids": (
        "passer_player_id", "rusher_player_id", "receiver_player_id", "sack_player_id",
        "interception_player_id", "fumbled_1_player_id", "penalty_player_id",
    ),
}
# Separately inventoried families. Presence of `shotgun` alone does NOT establish an
# Under / Gun / Pistol alignment vocabulary; routes, coverage, and protection have no
# documented ordinary-PBP field and are expected to be absent.
SEPARATE_FIELD_FAMILIES: dict[str, tuple[str, ...]] = {
    "personnel": (
        "offense_personnel", "defense_personnel", "offense_formation", "defenders_in_box",
        "n_offense", "n_defense", "offense_players", "defense_players",
    ),
    "qb_alignment": ("shotgun", "no_huddle"),
    "routes": ("route",),
    "coverage": ("defense_man_zone_type", "defense_coverage_type"),
    "protection": (),
}
SEPARATE_FAMILY_NOTES: dict[str, str] = {
    "personnel": "Personnel fields are inventoried separately; absence is a source "
    "limitation, not an operator error.",
    "qb_alignment": "A binary shotgun flag does not establish Under, Gun, or Pistol; "
    "non-shotgun is not an under-center claim.",
    "routes": "Ordinary PBP does not document route fields; none are expected here.",
    "coverage": "Ordinary PBP does not document coverage fields; none are expected here.",
    "protection": "No documented PBP field describes protection responsibility.",
}

# Columns whose disagreement between duplicate rows could alter possession order, team,
# or drive association.
ORDER_AFFECTING_COLUMNS: frozenset[str] = frozenset({"posteam", "drive", "fixed_drive"})

NO_PLAY_PLAY_TYPE = "no_play"
NO_PLAY_STATUS_NO_PLAY = "no_play"
NO_PLAY_STATUS_OTHER = "other_play_type"
NO_PLAY_STATUS_UNKNOWN_NULL = "unknown_null_play_type"
NO_PLAY_STATUS_UNKNOWN_ABSENT = "unknown_absent_column"

VALUE_STATUS_ABSENT = "absent_column"
VALUE_STATUS_NULL = "null"
VALUE_STATUS_NAN = "nan"
VALUE_STATUS_FALSE_OR_ZERO = "explicit_false_or_zero"
VALUE_STATUS_VALUE = "value"

PARSE_NOT_ATTEMPTED = "not_attempted"
PARSE_ATTEMPTED_FAILED = "attempted_failed"
PARSE_SUCCEEDED = "succeeded"

# Stages that touch the parquet engine (schema read, scan, collect). Only a failure
# raised inside one of these is a `parse_failure` attributable to the source bytes.
ENGINE_STAGES: tuple[str, ...] = (
    "inspect_schema", "locate_game_identity_scan", "describe_game_descriptors", "load_game_rows",
)
# Pure post-parse processing stages. A failure here is a reader defect
# (`reader_processing_failure`), never a statement about the source file.
PROCESSING_STAGES: tuple[str, ...] = (
    "locate_game_matching", "sort_game_rows", "inventory_duplicates", "inventory_fields",
    "build_possession_sequence", "select_possession", "select_events", "assemble_result",
    "serialize_result",
)

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")


class SourceRejected(Exception):
    """Raised when the supplied input cannot be accepted. Carries the rejection result."""

    def __init__(self, result: dict[str, Any]) -> None:
        super().__init__(result["rejection"]["reason"])
        self.result = result


class _StageFailure(Exception):
    """Internal: an exception captured inside a named stage."""

    def __init__(self, stage: str, exc: BaseException) -> None:
        super().__init__(f"{stage}: {type(exc).__name__}: {exc}")
        self.stage = stage
        self.exc = exc

    @property
    def detail(self) -> str:
        return f"{type(self.exc).__name__}: {self.exc}"


class _EngineFailure(_StageFailure):
    """Parquet engine failure (schema read, scan, collect): attributable to the source bytes."""


class _ProcessingFailure(_StageFailure):
    """Pure post-parse reader failure: a reader defect, not a source-file statement."""


@contextmanager
def _engine_stage(stage: str) -> Iterator[None]:
    assert stage in ENGINE_STAGES, stage
    try:
        yield
    except Exception as exc:
        raise _EngineFailure(stage, exc) from exc


@contextmanager
def _processing_stage(stage: str) -> Iterator[None]:
    assert stage in PROCESSING_STAGES, stage
    try:
        yield
    except (_StageFailure, SourceRejected):
        raise
    except Exception as exc:
        raise _ProcessingFailure(stage, exc) from exc


@dataclass(frozen=True, slots=True)
class GameRequest:
    season: int
    game_date: str  # YYYY-MM-DD, as supplied
    away_team: str
    home_team: str

    def validate(self) -> None:
        if not _DATE_RE.fullmatch(self.game_date):
            raise ValueError("requested game_date must be YYYY-MM-DD")
        try:
            parsed = date.fromisoformat(self.game_date)
        except ValueError as exc:
            raise ValueError(
                f"requested game_date {self.game_date!r} is not a calendar date"
            ) from exc
        if parsed.isoformat() != self.game_date:
            raise ValueError("requested game_date must be a zero-padded ISO calendar date")
        if not self.away_team or not self.home_team:
            raise ValueError("requested away_team and home_team are required")
        if canon_team(self.away_team) == canon_team(self.home_team):
            # Compared after canonicalization so an alias pair such as LA / LAR cannot
            # describe an impossible same-team game.
            raise ValueError(
                "requested away_team and home_team must differ after canonicalization"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "season": self.season,
            "game_date": self.game_date,
            "away_team": self.away_team,
            "home_team": self.home_team,
            "away_team_canonical": canon_team(self.away_team),
            "home_team_canonical": canon_team(self.home_team),
        }


@dataclass(frozen=True, slots=True)
class PossessionRequest:
    team: str
    ordinal: int  # 1-based: the team's N-th possession in play order

    def validate(self) -> None:
        if not self.team:
            raise ValueError("requested possession team is required")
        if isinstance(self.ordinal, bool) or not isinstance(self.ordinal, int) or self.ordinal < 1:
            raise ValueError("requested possession ordinal must be a positive integer (1-based)")


@dataclass(frozen=True, slots=True)
class SourceDeclaration:
    """Operator-supplied statements about the file. Nothing here is verified by hashing."""

    provider_dataset_ref: str | None = None
    retrieved_at: str | None = None
    published_at: str | None = None


# ---------------------------------------------------------------------------
# Small pure helpers
# ---------------------------------------------------------------------------


def canon_team(code: str | None) -> str | None:
    if code is None:
        return None
    return TEAM_CODE_CANONICAL_MAP.get(code, code)


def reader_code_sha256() -> str:
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def _now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def season_matches(value: Any, requested: int) -> bool:
    """Exact season equality with no lossy coercion.

    An int matches on equality; a float matches only if it is integral and equal; a
    string matches only if it is exactly the decimal digits of the requested season.
    Booleans, fractional values, and anything else never match.
    """
    if value is None or isinstance(value, bool):
        return False
    if isinstance(value, int):
        return value == requested
    if isinstance(value, float):
        return not math.isnan(value) and value.is_integer() and int(value) == requested
    if isinstance(value, str):
        return value == str(requested)
    return False


def _is_nan(value: Any) -> bool:
    return isinstance(value, float) and math.isnan(value)


def _is_non_finite(value: Any) -> bool:
    """True for ±infinity: a legal Float64 that carries no ordering evidence."""
    return isinstance(value, float) and math.isinf(value)


def _values_equal(left: Any, right: Any) -> bool:
    """NaN-aware equality, applied recursively through lists and structs.

    Two NaNs are equivalent (at any nesting depth); NaN is never equal to null or a
    number. Sequences compare element-wise only when they are the same container type,
    mirroring Python's own list/tuple inequality; structs compare by key set and value.
    """
    if _is_nan(left) or _is_nan(right):
        return _is_nan(left) and _is_nan(right)
    if isinstance(left, (list, tuple)) and isinstance(right, (list, tuple)):
        if type(left) is not type(right) or len(left) != len(right):
            return False
        return all(_values_equal(a, b) for a, b in zip(left, right, strict=True))
    if isinstance(left, dict) and isinstance(right, dict):
        if left.keys() != right.keys():
            return False
        return all(_values_equal(left[k], right[k]) for k in left)
    return left == right


# Strict decimal grammar for a numeric play-ID string: optional sign, digits with an
# optional fraction (or a bare fraction), optional exponent. No whitespace, underscores,
# hex, or inf/nan spellings. Parsed exactly, never through float.
_NUMERIC_STRING_RE = re.compile(
    r"(?P<sign>[+-]?)(?:(?P<int>\d+)(?:\.(?P<frac>\d*))?|\.(?P<bare_frac>\d+))"
    r"(?:[eE](?P<exp_sign>[+-]?)(?P<exp>\d+))?"
)

# Bounded numeric domain for numeric strings. The grammar alone is unbounded: a tiny
# string such as "1e999999999" would expand into an integer with a billion digits and
# hang the reader, and "1e9999999999999999999" overflows the decimal module's own
# exponent range before anything is expanded. Every bound is therefore derived from the
# COMPACT SPELLING (digit counts and the spelled exponent) before any Decimal or int is
# constructed; the exact inclusive magnitude check runs only once the spelling proves
# the value is representable. Outside the domain a string is an unknown order position,
# never order evidence. Ints and floats from parquet are bounded by their own types.
_MAX_NUMERIC_STRING_DIGITS = 4000  # significant (coefficient) digits, leading zeros dropped
_MAX_NUMERIC_STRING_MAGNITUDE = Decimal("1e4000")  # inclusive ceiling on |value|
_MIN_NUMERIC_STRING_MAGNITUDE = Decimal("1e-4000")  # inclusive floor on nonzero |value|
_MAX_NUMERIC_STRING_ADJUSTED_EXPONENT = 4000  # any in-domain value has |adjusted| <= this
_MAX_NUMERIC_STRING_EXPONENT_DIGITS = 12  # spelled exponent digits admitted to int()


def _bounded_decimal(text: str) -> Decimal | None:
    """Exact Decimal for a numeric string inside the bounded domain, else None.

    Domain: at most 4000 significant digits, and either zero or an absolute value in the
    inclusive range 10**-4000 ..= 10**4000. The digit count and the adjusted exponent are
    computed from the spelling alone, so an absurd exponent never reaches `Decimal`;
    the final magnitude comparison is exact (`1.1e4000` and `9e4000` are outside,
    `1e4000`, `0.1e4001`, and `10e3999` are inside).
    """
    match = _NUMERIC_STRING_RE.fullmatch(text)
    if match is None:
        return None
    int_part = match.group("int") or ""
    frac_part = match.group("frac")
    if frac_part is None:
        frac_part = match.group("bare_frac") or ""
    coefficient = (int_part + frac_part).lstrip("0")
    if not coefficient:
        return Decimal(0)  # zero at any spelled exponent has no magnitude
    if len(coefficient) > _MAX_NUMERIC_STRING_DIGITS:
        return None
    exp_digits = (match.group("exp") or "0").lstrip("0") or "0"
    if len(exp_digits) > _MAX_NUMERIC_STRING_EXPONENT_DIGITS:
        return None
    exponent = int(exp_digits) * (-1 if match.group("exp_sign") == "-" else 1)
    # Exponent of the most significant digit, exactly as Decimal.adjusted() defines it.
    adjusted = exponent - len(frac_part) + len(coefficient) - 1
    if abs(adjusted) > _MAX_NUMERIC_STRING_ADJUSTED_EXPONENT:
        return None
    dec = Decimal(text)  # provably within the decimal module's exponent range
    magnitude = abs(dec)
    if magnitude > _MAX_NUMERIC_STRING_MAGNITUDE or magnitude < _MIN_NUMERIC_STRING_MAGNITUDE:
        return None
    return dec


def _play_id_numeric(play_id: Any) -> int | Fraction | None:
    """The single lossless numeric representation used by every ordering stage.

    Returns an exact value or None. Ints stay ints; finite floats become exact Fractions
    of their binary value; numeric strings are parsed exactly from their decimal spelling
    (`9007199254740993.0` and `9007199254740993e0` are the integer 9007199254740993, not
    a rounded float) and become an int when integral, else an exact Fraction. Python
    compares int and Fraction exactly, so every stage that orders or compares play IDs
    through this function agrees. bool, bytes, NaN, ±infinity, unparseable values, and
    numeric strings outside the bounded domain (see `_bounded_decimal`) return None and
    are never order evidence.
    """
    if play_id is None or isinstance(play_id, bool):
        return None
    if isinstance(play_id, int):
        return play_id
    if isinstance(play_id, float):
        return Fraction(play_id) if math.isfinite(play_id) else None
    if isinstance(play_id, str):
        dec = _bounded_decimal(play_id)
        if dec is None:
            return None
        exact = Fraction(dec)
        return exact.numerator if exact.denominator == 1 else exact
    return None


def validate_receipt_expectations(expected_bytes: int, expected_sha256: str) -> None:
    """Malformed receipt declarations are usage errors, never evidence about the source."""
    if isinstance(expected_bytes, bool) or not isinstance(expected_bytes, int):
        raise ValueError("expected_bytes must be an integer byte count")
    if expected_bytes < 0:
        raise ValueError("expected_bytes must be a non-negative byte count")
    # fullmatch: a trailing newline must not slip past an end anchor.
    if not isinstance(expected_sha256, str) or not _SHA256_RE.fullmatch(expected_sha256):
        raise ValueError("expected_sha256 must be exactly 64 hexadecimal characters")


def _jsonable(value: Any) -> Any:
    """Normalize every scalar polars can hand back into a JSON-serializable value.

    Raw values are preserved where JSON can carry them; bytes become an explicit hex
    envelope rather than being dropped or stringified silently.
    """
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        if math.isnan(value):
            # A source NaN is not a source null; keep the distinction in the output.
            return {"float_nan": True}
        if math.isinf(value):
            # Legal Float64 values JSON cannot carry; kept distinct from finite, NaN, null.
            return {"float_infinity": "+" if value > 0 else "-"}
        return value
    if isinstance(value, (bytes, bytearray, memoryview)):
        raw = bytes(value)
        return {"bytes_hex": raw.hex(), "byte_length": len(raw)}
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if isinstance(value, timedelta):
        return {"timedelta_seconds": value.total_seconds()}
    if isinstance(value, Decimal):
        return {"decimal": str(value)}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    return {"unsupported_type": type(value).__name__, "repr": repr(value)}


def classify_value(row: dict[str, Any], column: str, columns: set[str]) -> str:
    """Distinguish absent column / null / explicit false-or-zero / value."""
    if column not in columns:
        return VALUE_STATUS_ABSENT
    value = row.get(column)
    if value is None:
        return VALUE_STATUS_NULL
    if _is_nan(value):
        return VALUE_STATUS_NAN
    if isinstance(value, bool):
        return VALUE_STATUS_FALSE_OR_ZERO if value is False else VALUE_STATUS_VALUE
    if isinstance(value, (int, float)) and value == 0:
        return VALUE_STATUS_FALSE_OR_ZERO
    return VALUE_STATUS_VALUE


def classify_no_play(row: dict[str, Any], columns: set[str]) -> str:
    """Derived no-play status that never asserts a known type from a missing discriminator."""
    if "play_type" not in columns:
        return NO_PLAY_STATUS_UNKNOWN_ABSENT
    value = row.get("play_type")
    if value is None:
        return NO_PLAY_STATUS_UNKNOWN_NULL
    if value == NO_PLAY_PLAY_TYPE:
        return NO_PLAY_STATUS_NO_PLAY
    return NO_PLAY_STATUS_OTHER


PLAY_ID_ORDER_FINITE = "finite"
PLAY_ID_ORDER_NULL = "null"  # None or NaN: a missing key
PLAY_ID_ORDER_NON_FINITE = "non_finite"  # ±infinity: serializable, not an order position
PLAY_ID_ORDER_NON_NUMERIC = "non_numeric"  # unparseable: an unknown order position


def play_id_order_class(play_id: Any) -> str:
    """Classify a play ID by whether it evidences a position in the game order."""
    if play_id is None or _is_nan(play_id):
        return PLAY_ID_ORDER_NULL
    if _is_non_finite(play_id):
        return PLAY_ID_ORDER_NON_FINITE
    if isinstance(play_id, bool) or not isinstance(play_id, (int, float, str)):
        # bytes and other types are never order evidence, even if float() would parse them.
        return PLAY_ID_ORDER_NON_NUMERIC
    if _play_id_numeric(play_id) is not None:
        return PLAY_ID_ORDER_FINITE
    if isinstance(play_id, str):
        if _NUMERIC_STRING_RE.fullmatch(play_id):
            # Numeric spelling outside the bounded domain (too many digits or too large a
            # magnitude): an unknown order position, never expanded.
            return PLAY_ID_ORDER_NON_NUMERIC
        # Outside the strict numeric grammar: an infinity spelling is non-finite; "nan",
        # whitespace, underscores, hex, or garbage is an unknown order position.
        try:
            parsed = float(play_id)
        except ValueError:
            return PLAY_ID_ORDER_NON_NUMERIC
        return PLAY_ID_ORDER_NON_FINITE if math.isinf(parsed) else PLAY_ID_ORDER_NON_NUMERIC
    return PLAY_ID_ORDER_NON_NUMERIC


def _play_sort_key(row: dict[str, Any]) -> tuple[int, int | Fraction]:
    """Finite play IDs order the game exactly; every other class sorts last."""
    numeric = _play_id_numeric(row.get("play_id"))
    if numeric is None:
        return (1, 0)
    return (0, numeric)


class _NanKey:
    """Canonical frozen key for a NaN source value (play ID, drive, or nested): every NaN
    freezes to this one sentinel, which is distinct from the null key `None`."""

    __slots__ = ()

    def __repr__(self) -> str:
        return "<nan>"


_NAN_KEY = _NanKey()


def _freeze(value: Any) -> Any:
    """Equality-consistent, hashable key form of a source value. Row values are never altered.

    Two values receive the same frozen key exactly when `_values_equal` holds: NaN maps to
    one sentinel at any depth, lists/tuples become typed tuples of frozen elements (so
    [0.0] and [-0.0] share a key because 0.0 == -0.0, while a list and a tuple do not),
    structs become sorted tuples of frozen items, and any residual unhashable value is
    keyed by type and repr as a last resort.
    """
    if _is_nan(value):
        return _NAN_KEY
    if isinstance(value, (list, tuple)):
        return ("<seq>", type(value).__name__, tuple(_freeze(v) for v in value))
    if isinstance(value, dict):
        return ("<map>", tuple(sorted((str(k), _freeze(v)) for k, v in value.items())))
    try:
        hash(value)
    except TypeError:
        return ("<unhashable>", type(value).__name__, repr(value))
    return value


_hashable_key_part = _freeze


def _grouping_key(row: dict[str, Any]) -> tuple[Any, Any]:
    """(game_id, play_id) with NaN canonicalized so separately loaded NaNs share a group.

    Only the KEY is canonicalized; the row's raw play_id is untouched, so the NaN-aware
    comparator can still tell NaN from null when members of a group are compared, and a
    non-scalar play ID still reaches the unresolved-possession path instead of crashing
    grouping.
    """
    return (_hashable_key_part(row.get("game_id")), _hashable_key_part(row.get("play_id")))


def _normalize_date_value(value: Any) -> tuple[str | None, str]:
    """Return (YYYY-MM-DD or None, basis). Timezone is never guessed."""
    if value is None:
        return None, "null"
    if isinstance(value, datetime):
        basis = "datetime_date_component_tz_aware" if value.tzinfo else (
            "datetime_date_component_naive"
        )
        return value.date().isoformat(), basis
    if isinstance(value, date):
        return value.isoformat(), "date"
    text = str(value)
    if _DATE_RE.fullmatch(text):
        return text, "string_exact"
    return text, "string_non_iso_date"


# ---------------------------------------------------------------------------
# Step 1: receipt verification (hash before parse)
# ---------------------------------------------------------------------------


def _base_receipt(
    *,
    supplied_path: str,
    expected_bytes: int,
    expected_sha256: str,
    declaration: SourceDeclaration,
) -> dict[str, Any]:
    return {
        "reader": {
            "name": READER_NAME,
            "version": READER_VERSION,
            "code_sha256": reader_code_sha256(),
            "supported_format": SUPPORTED_FORMAT,
            "max_event_rows": MAX_EVENT_ROWS,
            "max_boundary_events_per_side": MAX_BOUNDARY_EVENTS_PER_SIDE,
        },
        "source": {
            "supplied_path": supplied_path,
            "expected_bytes": expected_bytes,
            "expected_sha256": expected_sha256.lower(),
            "actual_bytes": None,
            "actual_sha256": None,
            "format_detected": None,
            "receipt_status": None,
            "provider_dataset_ref": declaration.provider_dataset_ref,
            "provider_dataset_ref_basis": (
                "operator_supplied" if declaration.provider_dataset_ref else "unknown"
            ),
            "retrieved_at": declaration.retrieved_at,
            "retrieved_at_basis": "operator_supplied" if declaration.retrieved_at else "unknown",
            "published_at": declaration.published_at,
            "published_at_basis": (
                "operator_supplied" if declaration.published_at else "not_evidenced"
            ),
            "mutability_note": (
                "A mutable release URL is never an identity; only the exact byte digest "
                "identifies this input."
            ),
        },
        "times": {
            "processing_time": None,
            "ingestion_time": None,
            "note": (
                "processing_time is when this reader ran. It is not retrieval, ingestion, "
                "publication, or admission time and must never be substituted for them."
            ),
        },
        "lineage": {"status": "unknown", "note": "No TIBER lineage is asserted by this reader."},
        "admission": {
            "status": "not_admitted",
            "note": "Local read only. Existence of this output is not admission, promotion, "
            "or consumer availability.",
        },
        "governance_status": "ungoverned",
        "canonical": False,
        "side_effects": {
            "network": False,
            "database": False,
            "schema_change": False,
            "app_startup": False,
        },
    }


def verify_source_bytes(
    path: Path,
    *,
    expected_bytes: int,
    expected_sha256: str,
    receipt: dict[str, Any],
) -> bytes:
    """Read and hash the exact bytes. Rejects on missing file, size, digest, or format."""
    source = receipt["source"]
    if not path.is_file():
        source["receipt_status"] = "rejected"
        raise SourceRejected(
            _rejection(receipt, "missing_input", f"No file at supplied path: {path}")
        )
    content = path.read_bytes()
    actual_bytes = len(content)
    actual_sha256 = hashlib.sha256(content).hexdigest()
    source["actual_bytes"] = actual_bytes
    source["actual_sha256"] = actual_sha256
    if actual_bytes != expected_bytes:
        source["receipt_status"] = "rejected"
        raise SourceRejected(
            _rejection(
                receipt,
                "byte_count_mismatch",
                f"Expected {expected_bytes} bytes, found {actual_bytes} bytes.",
            )
        )
    if actual_sha256 != expected_sha256.lower():
        source["receipt_status"] = "rejected"
        raise SourceRejected(
            _rejection(
                receipt,
                "sha256_mismatch",
                "Supplied SHA-256 does not match the exact bytes at the supplied path.",
            )
        )
    is_parquet = (
        actual_bytes >= 12
        and content[:4] == PARQUET_MAGIC
        and content[-4:] == PARQUET_MAGIC
    )
    if not is_parquet:
        source["receipt_status"] = "rejected"
        source["format_detected"] = "unsupported"
        raise SourceRejected(
            _rejection(
                receipt,
                "unsupported_format",
                "Only parquet (PAR1 magic at head and tail) is supported by this reader.",
            )
        )
    source["format_detected"] = SUPPORTED_FORMAT
    source["receipt_status"] = "verified"
    return content


def _rejection(
    receipt: dict[str, Any],
    reason: str,
    detail: str,
    *,
    parsed: str = PARSE_NOT_ATTEMPTED,
    read_stage: str | None = None,
) -> dict[str, Any]:
    receipt["times"]["processing_time"] = _now_iso()
    return {
        "status": "rejected",
        "rejection": {
            "reason": reason, "detail": detail, "parsed": parsed, "read_stage": read_stage,
        },
        "failure": None,
        "receipt": receipt,
        "game": None,
        "inventory": None,
        "possession": None,
        "events": None,
    }


def _processing_failed(
    receipt: dict[str, Any], stage: str, detail: str, game: dict[str, Any] | None
) -> dict[str, Any]:
    """Bounded result for a reader defect after parsing succeeded. Not a source statement."""
    receipt["times"]["processing_time"] = _now_iso()
    return {
        "status": "processing_failed",
        "rejection": None,
        "failure": {
            "kind": "reader_processing_failure",
            "stage": stage,
            "detail": detail,
            "parsed": PARSE_SUCCEEDED,
            "note": "The source bytes were verified and parsed. This failure is in the reader's "
            "own processing and says nothing about the source file.",
        },
        "receipt": receipt,
        "game": game,
        "inventory": None,
        "possession": None,
        "events": None,
    }


# ---------------------------------------------------------------------------
# Step 2: schema inspection and game location (lazy, identity columns only)
# ---------------------------------------------------------------------------


def inspect_schema(content: bytes) -> dict[str, str]:
    import polars as pl

    with _engine_stage("inspect_schema"):
        schema = pl.read_parquet_schema(io.BytesIO(content))
        return {name: str(dtype) for name, dtype in schema.items()}


def _lazy_scan(content: bytes) -> Any:
    """Lazy scan over the exact verified bytes; callers push projections/filters into it."""
    import polars as pl

    return pl.scan_parquet(io.BytesIO(content))


def game_scan(content: bytes, game_id: Any) -> Any:
    """LazyFrame for exactly one game; the equality predicate is pushed into the scan.

    `game_id` is the RAW typed value observed in the source (Int64, Utf8, ...), never a
    string rendering of it, so the predicate compares like with like. The ID is
    normalized only for output.
    """
    import polars as pl

    return _lazy_scan(content).filter(pl.col("game_id") == pl.lit(game_id))


def locate_game(
    content: bytes, schema: dict[str, str], request: GameRequest
) -> dict[str, Any]:
    """Scan ONLY identity columns across the file to find exactly one matching game."""
    columns = set(schema)
    missing = [c for c in REQUIRED_IDENTITY_COLUMNS if c not in columns]
    present_identity = [c for c in GAME_IDENTITY_COLUMNS if c in columns]
    present_descriptors = [c for c in GAME_DESCRIPTOR_COLUMNS if c in columns]
    location: dict[str, Any] = {
        "status": None,
        "reason": None,
        "requested": request.to_dict(),
        "identity_columns_present": present_identity,
        "identity_columns_absent": [c for c in GAME_IDENTITY_COLUMNS if c not in columns],
        "descriptor_columns_present": present_descriptors,
        "descriptor_columns_absent": [c for c in GAME_DESCRIPTOR_COLUMNS if c not in columns],
        "selection_scan": {
            "columns_scanned": present_identity,
            "note": "Only invariant game-identity columns were projected across the supplied "
            "file to locate the requested game. Descriptor columns were read for the "
            "matched game only. No other game's event rows were materialized.",
        },
        "observed": None,
        "descriptors": None,
        "date_match_basis": None,
        "timezone": "not_stated_by_source_identity_columns",
        "diagnostics": {},
    }
    if missing:
        location["status"] = "unresolved"
        location["reason"] = "missing_game_identity_columns"
        location["diagnostics"]["missing_columns"] = missing
        return location

    with _engine_stage("locate_game_identity_scan"):
        distinct = (
            _lazy_scan(content)
            .select(present_identity)
            .unique(maintain_order=True)
            .collect()
            .to_dicts()
        )

    req_home = canon_team(request.home_team)
    req_away = canon_team(request.away_team)
    matches: list[dict[str, Any]] = []
    matches_without_game_id = 0
    matches_with_non_finite_game_id = 0
    same_teams_any_orientation = 0
    swapped_orientation = 0
    date_bases: set[str] = set()
    for rec in distinct:
        rec_date, basis = _normalize_date_value(rec.get("game_date"))
        date_bases.add(basis)
        season_ok = season_matches(rec.get("season"), request.season)
        home = canon_team(rec.get("home_team"))
        away = canon_team(rec.get("away_team"))
        if season_ok and {home, away} == {req_home, req_away}:
            same_teams_any_orientation += 1
            if home == req_away and away == req_home and rec_date == request.game_date:
                swapped_orientation += 1
        if season_ok and home == req_home and away == req_away and rec_date == request.game_date:
            game_id_value = rec.get("game_id")
            if game_id_value is None or str(game_id_value).strip() == "":
                # Identity fields agree but the provider game ID is missing: this can
                # never be certified, and it must not be silently dropped either.
                matches_without_game_id += 1
            elif _is_nan(game_id_value) or _is_non_finite(game_id_value):
                # A NaN or ±infinity Float64 ID serializes, but it is no usable source
                # identity: nothing may be scanned or certified under it.
                matches_with_non_finite_game_id += 1
            else:
                matches.append(rec)

    location["diagnostics"] = {
        "distinct_identity_tuples_scanned": len(distinct),
        "same_season_same_teams_any_orientation_or_date": same_teams_any_orientation,
        "swapped_home_away_on_requested_date": swapped_orientation,
        "matching_tuples_without_game_id": matches_without_game_id,
        "matching_tuples_with_non_finite_game_id": matches_with_non_finite_game_id,
        "game_date_value_bases": sorted(date_bases),
    }
    if matches_without_game_id or matches_with_non_finite_game_id:
        # Null, blank, NaN, or infinite provider IDs are all unusable identity; the
        # diagnostics say which kind occurred, and no real match beside them is certified.
        location["status"] = "unresolved"
        location["reason"] = "matching_identity_without_game_id"
        return location
    if not matches:
        location["status"] = "unresolved"
        location["reason"] = "no_matching_game"
        return location
    # Distinct matched IDs by the shared equality-consistent key; the RAW typed value is
    # kept (an Int64 game_id stays an int) so scan predicates compare like with like.
    distinct_ids: dict[Any, Any] = {}
    for m in matches:
        distinct_ids.setdefault(_freeze(m["game_id"]), m["game_id"])
    if len(distinct_ids) > 1:
        location["status"] = "unresolved"
        location["reason"] = "multiple_matching_games"
        location["diagnostics"]["matching_game_ids"] = sorted(
            (_jsonable(v) for v in distinct_ids.values()), key=str
        )
        return location
    game_id = next(iter(distinct_ids.values()))
    tuples_for_game = [rec for rec in distinct if _values_equal(rec.get("game_id"), game_id)]
    if len(tuples_for_game) > 1:
        location["status"] = "unresolved"
        location["reason"] = "conflicting_game_metadata"
        location["diagnostics"]["conflicting_identity_tuples"] = [
            _jsonable(rec) for rec in tuples_for_game
        ]
        location["observed"] = {"game_id": _jsonable(game_id)}
        return location
    observed = _jsonable(tuples_for_game[0])
    _, basis = _normalize_date_value(tuples_for_game[0].get("game_date"))
    location["status"] = "matched"
    location["observed"] = observed
    location["date_match_basis"] = basis
    location["game_id_predicate"] = {
        "source_dtype": schema.get("game_id"),
        "python_type": type(game_id).__name__,
        "note": "The raw typed source value is pushed into every game scan; it is "
        "normalized for JSON only in `observed`.",
    }
    # Private handoff of the raw value to the read path; stripped before output.
    location["_game_id_raw"] = game_id
    location["descriptors"] = _describe_game_descriptors(content, game_id, present_descriptors)
    if basis.startswith("datetime"):
        location["timezone"] = (
            "source game_date carries a time component; timezone "
            + ("declared by source dtype" if basis.endswith("aware") else "not declared")
        )
    return location


def _describe_game_descriptors(
    content: bytes, game_id: Any, descriptor_columns: list[str]
) -> dict[str, Any]:
    """Distinct values of game-level descriptor columns for the matched game only."""
    if not descriptor_columns:
        return {}
    report: dict[str, Any] = {}
    with _engine_stage("describe_game_descriptors"):
        frame = game_scan(content, game_id).select(descriptor_columns).collect()
    for column in descriptor_columns:
        values = frame.get_column(column).unique(maintain_order=True).to_list()
        jsonable = [_jsonable(v) for v in values]
        report[column] = {
            "distinct_count": len(jsonable),
            "distinct_values": jsonable[:MAX_DESCRIPTOR_VALUES_REPORTED],
            "varies_within_game": len(jsonable) > 1,
            "truncated": len(jsonable) > MAX_DESCRIPTOR_VALUES_REPORTED,
        }
    return report


def load_game_rows(content: bytes, game_id: Any) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Materialize only the located game's rows (all columns) via a pushed-down filter.

    `game_id` is the raw typed value from `locate_game`, not a string rendering of it.
    """
    with _engine_stage("load_game_rows"):
        lazy = game_scan(content, game_id)
        plan = lazy.explain()
        frame = lazy.collect()
        raw_rows = frame.to_dicts()
    # Keep raw source scalars (including NaN, which stays distinct from null) for duplicate
    # classification and possession sequencing; comparisons are NaN-aware. All JSON
    # shaping (bytes, NaN, infinities, dates) happens once at the output boundary.
    rows = [dict(row) for row in raw_rows]
    with _processing_stage("sort_game_rows"):
        # Pure post-parse work: a defect here is a reader failure, never a source failure.
        rows.sort(key=_play_sort_key)
    strategy = {
        "logical_scope": f"rows where game_id == {game_id!r}",
        "columns": "all source columns for the located game only; full-row content is "
        "required to classify duplicate keys as identical or conflicting",
        "physical_io": "The verified in-memory bytes are the only source. Parquet row "
        "groups whose statistics cannot exclude the game may be decoded and discarded "
        "by the engine; no other game's rows are materialized into the result.",
        "selection_pushed_into_scan": "SELECTION:" in plan and "game_id" in plan,
    }
    return rows, strategy


# ---------------------------------------------------------------------------
# Step 3: game-level inventory (duplicates, field families, counts)
# ---------------------------------------------------------------------------


def inventory_duplicates(rows: list[dict[str, Any]]) -> dict[str, Any]:
    groups: dict[tuple[Any, Any], list[dict[str, Any]]] = {}
    null_key_rows = 0
    for row in rows:
        key = _grouping_key(row)
        if key[0] is None or key[1] is None or key[1] is _NAN_KEY:
            # A null or NaN play ID is a missing key; both are counted, kept distinct.
            null_key_rows += 1
        groups.setdefault(key, []).append(row)
    identical: list[dict[str, Any]] = []
    conflicting: list[dict[str, Any]] = []
    for key, members in groups.items():
        if len(members) < 2:
            continue
        first = members[0]
        differing: set[str] = set()
        for other in members[1:]:
            for column in set(first) | set(other):
                if not _values_equal(first.get(column), other.get(column)):
                    differing.add(column)
        # Report the raw play_id of the group (NaN stays NaN; the envelope is applied at
        # the output boundary), never the internal canonical key.
        entry = {
            "game_id": key[0], "play_id": first.get("play_id"), "occurrences": len(members),
        }
        if differing:
            entry["differing_columns"] = sorted(differing)
            entry["affects_possession_order"] = bool(differing & ORDER_AFFECTING_COLUMNS)
            conflicting.append(entry)
        else:
            identical.append(entry)
    conflicting_keys = {
        key for key, members in groups.items()
        if len(members) > 1 and any(
            not _values_equal(members[0].get(c), other.get(c))
            for other in members[1:] for c in set(members[0]) | set(other)
        )
    }
    for row in rows:
        key = _grouping_key(row)
        if len(groups[key]) == 1:
            row["_duplicate_status"] = "unique"
        elif key in conflicting_keys:
            row["_duplicate_status"] = "conflicting_duplicate"
        else:
            row["_duplicate_status"] = "identical_duplicate"
    return {
        "row_count": len(rows),
        "distinct_game_play_key_count": len(groups),
        "null_key_rows": null_key_rows,
        "identical_duplicate_keys": identical,
        "conflicting_duplicate_keys": conflicting,
        "disposition": "All rows retained; duplicates classified, never discarded.",
        "snap_denominator_note": (
            "Neither row_count nor distinct_game_play_key_count is an official snap "
            "denominator."
        ),
    }


def inventory_fields(rows: list[dict[str, Any]], schema: dict[str, str]) -> dict[str, Any]:
    columns = set(schema)

    def family_report(family_columns: tuple[str, ...]) -> dict[str, Any]:
        report: dict[str, Any] = {}
        for column in family_columns:
            if column not in columns:
                report[column] = {"status": "absent", "dtype": None}
                continue
            counts = {
                VALUE_STATUS_NULL: 0,
                VALUE_STATUS_NAN: 0,
                VALUE_STATUS_FALSE_OR_ZERO: 0,
                VALUE_STATUS_VALUE: 0,
            }
            for row in rows:
                counts[classify_value(row, column, columns)] += 1
            report[column] = {
                "status": "present",
                "dtype": schema[column],
                "null_rows": counts[VALUE_STATUS_NULL],
                "nan_rows": counts[VALUE_STATUS_NAN],
                "explicit_false_or_zero_rows": counts[VALUE_STATUS_FALSE_OR_ZERO],
                "value_rows": counts[VALUE_STATUS_VALUE],
            }
        return report

    inspected: set[str] = set()
    families: dict[str, Any] = {}
    for name, family_columns in INVENTORY_FIELD_FAMILIES.items():
        families[name] = family_report(family_columns)
        inspected.update(family_columns)
    separate: dict[str, Any] = {}
    for name, family_columns in SEPARATE_FIELD_FAMILIES.items():
        separate[name] = {
            "fields": family_report(family_columns),
            "note": SEPARATE_FAMILY_NOTES[name],
        }
        inspected.update(family_columns)
    inspected.update(GAME_IDENTITY_COLUMNS)
    inspected.update(GAME_DESCRIPTOR_COLUMNS)
    inspected.update(PLAY_KEY_COLUMNS)
    uninspected = sorted(columns - inspected)
    no_play_counts = {
        NO_PLAY_STATUS_NO_PLAY: 0,
        NO_PLAY_STATUS_OTHER: 0,
        NO_PLAY_STATUS_UNKNOWN_NULL: 0,
        NO_PLAY_STATUS_UNKNOWN_ABSENT: 0,
    }
    for row in rows:
        no_play_counts[classify_no_play(row, columns)] += 1
    return {
        "source_column_count": len(columns),
        "inventoried_families": families,
        "separately_inventoried_families": separate,
        "uninspected_columns": uninspected,
        "uninspected_column_count": len(uninspected),
        "clock_meaning": (
            "Clock fields are reported raw. Their semantics (e.g. time remaining at play "
            "start) are documented upstream but not certified by this reader."
        ),
        "no_play_status_rows": no_play_counts,
        "no_play_basis": (
            f"play_type == '{NO_PLAY_PLAY_TYPE}'; a null play_type is unknown, never a "
            "negative assertion"
        ),
    }


# ---------------------------------------------------------------------------
# Step 4: possession sequence and selection
# ---------------------------------------------------------------------------


def build_possession_sequence(
    rows: list[dict[str, Any]], schema: dict[str, str]
) -> dict[str, Any]:
    """Possession runs: maximal ordered runs of identical non-null posteam AND drive value.

    A run is the unit of "possession". The provider `drive` column (fallback
    `fixed_drive`, disclosed) bounds runs so that two consecutive possessions by the
    same team (e.g. either side of halftime) are not merged. If no drive column exists,
    runs are bounded by posteam change only and no provider drive association is
    possible. Rows with null posteam are recorded as unattributed together with any
    drive value they carry, so a later selection can tell a neutral administrative row
    from evidence of a possession the run count did not see.
    """
    columns = set(schema)
    drive_column: str | None = None
    for candidate in ("drive", "fixed_drive"):
        if candidate in columns:
            drive_column = candidate
            break
    runs: list[dict[str, Any]] = []
    unattributed: list[dict[str, Any]] = []
    play_id_null_rows = 0
    play_id_non_finite_rows = 0
    play_id_non_numeric_rows = 0
    for index, row in enumerate(rows):
        order_class = play_id_order_class(row.get("play_id"))
        if order_class == PLAY_ID_ORDER_NULL:
            play_id_null_rows += 1
        elif order_class == PLAY_ID_ORDER_NON_FINITE:
            play_id_non_finite_rows += 1
        elif order_class == PLAY_ID_ORDER_NON_NUMERIC:
            play_id_non_numeric_rows += 1
        posteam = canon_team(row.get("posteam")) if "posteam" in columns else None
        # The raw drive value is kept: a NaN drive stays NaN (distinct from null) through
        # run extension, occurrence counting, and inventory, and is enveloped only at the
        # output boundary. Selection treats NaN as a missing drive number (_drive_missing).
        drive = row.get(drive_column) if drive_column else None
        if posteam is None:
            unattributed.append({"index": index, "play_id": row.get("play_id"), "drive": drive})
            continue
        current = runs[-1] if runs else None
        # Run extension uses the same recursive equality as duplicate classification and
        # key freezing, so all three stages obey one equivalence relation.
        if (
            current
            and current["posteam"] == posteam
            and _values_equal(current["provider_drive"], drive)
        ):
            current["last_index"] = index
            current["last_play_id"] = row.get("play_id")
            current["attributed_row_count"] += 1
        else:
            runs.append(
                {
                    "sequence_index": len(runs) + 1,
                    "posteam": posteam,
                    "posteam_raw": row.get("posteam"),
                    "provider_drive": drive,
                    "first_index": index,
                    "last_index": index,
                    "first_play_id": row.get("play_id"),
                    "last_play_id": row.get("play_id"),
                    "attributed_row_count": 1,
                }
            )
    per_team: dict[str, int] = {}
    for run in runs:
        per_team[run["posteam"]] = per_team.get(run["posteam"], 0) + 1
        run["team_possession_ordinal"] = per_team[run["posteam"]]
    drive_occurrences: dict[Any, int] = {}
    for run in runs:
        # Frozen key so a non-scalar drive counts instead of crashing; the run keeps its raw value.
        drive_value = _freeze(run["provider_drive"])
        drive_occurrences[drive_value] = drive_occurrences.get(drive_value, 0) + 1
    return {
        "basis": {
            "order": "rows sorted by finite play_id ascending; null, NaN, non-finite, and "
            "non-numeric play_id carry no order and sort last",
            "run_rule": "maximal consecutive run of identical non-null posteam and identical "
            "provider drive value",
            "drive_column_used": drive_column,
            "posteam_column_present": "posteam" in columns,
            "team_ordinal_rule": "N-th run whose posteam is the team, counted in play order; "
            "never equated with provider drive number N; resolved only when every run in "
            "the prefix up to the selection is itself evidenced",
        },
        "unattributed_rows": len(unattributed),
        "unattributed": unattributed,
        "play_id_null_rows": play_id_null_rows,
        "play_id_non_finite_rows": play_id_non_finite_rows,
        "play_id_non_numeric_rows": play_id_non_numeric_rows,
        "runs": runs,
        "drive_occurrence_counts": {str(k): v for k, v in drive_occurrences.items()},
    }


def _drive_missing(value: Any) -> bool:
    """A null or NaN provider drive is a missing drive number, never a drive.

    The two states stay distinct through sequencing and output; only selection treats
    them alike, because neither is evidence of a possession's drive.
    """
    return value is None or _is_nan(value)


def select_possession(
    sequence: dict[str, Any],
    request: PossessionRequest,
    *,
    order_affecting_conflict_play_ids: tuple[Any, ...] = (),
) -> dict[str, Any]:
    """Select the team's N-th possession only if the whole counting prefix is evidenced."""
    team = canon_team(request.team)
    result: dict[str, Any] = {
        "requested": {"team": request.team, "team_canonical": team, "ordinal": request.ordinal},
        "status": None,
        "reason": None,
        "selected_run": None,
    }

    def unresolved(reason: str, run: dict[str, Any] | None = None, **extra: Any) -> dict[str, Any]:
        result.update(status="unresolved", reason=reason, selected_run=run)
        result.update(extra)
        return result

    if not sequence["basis"]["posteam_column_present"]:
        return unresolved("posteam_column_absent")
    if sequence["basis"]["drive_column_used"] is None:
        return unresolved("no_provider_drive_column")
    if sequence["play_id_null_rows"]:
        return unresolved("null_play_id_breaks_play_order")
    if sequence["play_id_non_finite_rows"]:
        # ±infinity serializes, but it is no evidence of a position in the game order.
        return unresolved("non_finite_play_id_breaks_play_order")
    if sequence["play_id_non_numeric_rows"]:
        # An unparseable ID has an unknown position; it could change which run is N-th.
        return unresolved("non_numeric_play_id_breaks_play_order")
    candidates = [r for r in sequence["runs"] if r["posteam"] == team]
    if request.ordinal < 1 or request.ordinal > len(candidates):
        return unresolved(
            "team_possession_ordinal_not_present",
            team_possession_runs_observed=len(candidates),
        )
    run = candidates[request.ordinal - 1]
    if _drive_missing(run["provider_drive"]):
        return unresolved("null_provider_drive_in_possession", run)

    # The ordinal is a count over every earlier run (any team). Each of those runs must
    # itself be evidenced, or the count cannot be trusted. Conflicting duplicates that
    # disagree on team or drive are checked first because they can distort the count.
    last_numeric = _play_id_numeric(run["last_play_id"])
    conflicts = []
    for pid in order_affecting_conflict_play_ids:
        pid_numeric = _play_id_numeric(pid)
        # Exact comparison; anything not exactly orderable is treated as inside the prefix.
        if pid_numeric is None or last_numeric is None or pid_numeric <= last_numeric:
            conflicts.append(pid)
    if conflicts:
        return unresolved("conflicting_duplicate_in_prefix", run, affected_play_ids=conflicts)
    prefix = [r for r in sequence["runs"] if r["sequence_index"] <= run["sequence_index"]]
    null_prefix = [r["sequence_index"] for r in prefix if _drive_missing(r["provider_drive"])]
    if null_prefix:
        return unresolved("null_provider_drive_in_prefix", run, affected_runs=null_prefix)
    counts = sequence["drive_occurrence_counts"]
    non_contiguous = [
        r["sequence_index"] for r in prefix
        if counts.get(str(_freeze(r["provider_drive"])), 0) != 1
    ]
    if non_contiguous:
        return unresolved("provider_drive_not_contiguous", run, affected_runs=non_contiguous)
    # Drive numbers obey the same classifier and the same lossless numeric representation
    # as play IDs: bool, bytes, lists, structs, and unparseable strings are not orderable;
    # ±infinity is serializable but no drive ordinal; finite values compare exactly, so
    # Int64 drives above 2**53 never collapse through float.
    classes = [play_id_order_class(r["provider_drive"]) for r in prefix]
    if any(c == PLAY_ID_ORDER_NON_NUMERIC for c in classes):
        return unresolved("provider_drive_not_orderable", run)
    non_finite = [
        r["sequence_index"] for r, c in zip(prefix, classes, strict=True)
        if c == PLAY_ID_ORDER_NON_FINITE
    ]
    if non_finite:
        # A serializable infinity is not a football drive ordinal.
        return unresolved("non_finite_provider_drive_in_prefix", run, affected_runs=non_finite)
    drive_values = [_play_id_numeric(r["provider_drive"]) for r in prefix]
    if any(v is None for v in drive_values):
        # Unreachable once nulls/NaN are excluded above; kept so a gap never certifies.
        return unresolved("provider_drive_not_orderable", run)
    if any(earlier > later for earlier, later in zip(drive_values, drive_values[1:], strict=False)):
        return unresolved("provider_drive_order_non_monotone", run)
    prefix_drives = {_freeze(r["provider_drive"]) for r in prefix}
    foreign = [
        u for u in sequence["unattributed"]
        if u["index"] <= run["last_index"]
        and not _drive_missing(u["drive"])
        and _freeze(u["drive"]) not in prefix_drives
    ]
    if foreign:
        return unresolved(
            "unattributed_drive_value_in_prefix",
            run,
            affected_play_ids=[u["play_id"] for u in foreign],
        )
    result.update(status="resolved", reason="possession_semantics_supported", selected_run=run)
    result["note"] = (
        f"{team} possession #{request.ordinal} is provider drive "
        f"{run['provider_drive']!r}; the ordinal was derived from posteam run order over a "
        "fully evidenced prefix, not from drive-number equality."
    )
    return result


# ---------------------------------------------------------------------------
# Step 5: bounded event output
# ---------------------------------------------------------------------------


def _event_row(row: dict[str, Any], columns: set[str]) -> dict[str, Any]:
    fields: dict[str, Any] = {}
    for family_columns in INVENTORY_FIELD_FAMILIES.values():
        for column in family_columns:
            if column in columns:
                fields[column] = row.get(column)
    for family_columns in SEPARATE_FIELD_FAMILIES.values():
        for column in family_columns:
            if column in columns:
                fields[column] = row.get(column)
    return {
        "game_id": row.get("game_id"),
        "play_id": row.get("play_id"),
        "duplicate_status": row.get("_duplicate_status", "unique"),
        "event_status": {
            "no_play": classify_no_play(row, columns),
            "penalty_raw": row.get("penalty") if "penalty" in columns else VALUE_STATUS_ABSENT,
            "play_deleted_raw": (
                row.get("play_deleted") if "play_deleted" in columns else VALUE_STATUS_ABSENT
            ),
        },
        "fields": fields,
    }


def _empty_events(status: str, reason: str) -> dict[str, Any]:
    return {
        "status": status,
        "reason": reason,
        "rows": [],
        "boundary_before": [],
        "boundary_after": [],
        "row_count": 0,
        "distinct_game_play_key_count": 0,
        "truncated": False,
        "omitted_row_count": 0,
    }


def select_events(
    rows: list[dict[str, Any]], selection: dict[str, Any], schema: dict[str, str]
) -> dict[str, Any]:
    columns = set(schema)
    if selection["status"] != "resolved":
        return _empty_events("withheld", "possession_unresolved_no_arbitrary_sample")
    run = selection["selected_run"]
    first, last = run["first_index"], run["last_index"]
    window = rows[first : last + 1]
    truncated = len(window) > MAX_EVENT_ROWS
    emitted = window[:MAX_EVENT_ROWS]
    before = rows[max(0, first - MAX_BOUNDARY_EVENTS_PER_SIDE) : first]
    after = rows[last + 1 : last + 1 + MAX_BOUNDARY_EVENTS_PER_SIDE]
    # The same frozen (game_id, play_id) key as duplicate inventory: a List/Struct game
    # ID or play ID counts instead of failing, and the count agrees with the inventory.
    keys = {_grouping_key(r) for r in window}
    return {
        "status": "emitted",
        "reason": None,
        "rows": [_event_row(r, columns) for r in emitted],
        "boundary_before": [_event_row(r, columns) for r in before],
        "boundary_after": [_event_row(r, columns) for r in after],
        "row_count": len(window),
        "distinct_game_play_key_count": len(keys),
        "unattributed_rows_in_window": sum(
            1 for r in window if ("posteam" not in columns or r.get("posteam") is None)
        ),
        "emitted_row_count": len(emitted),
        "truncated": truncated,
        "omitted_row_count": len(window) - len(emitted),
        "max_event_rows": MAX_EVENT_ROWS,
        "max_boundary_events_per_side": MAX_BOUNDARY_EVENTS_PER_SIDE,
        "snap_denominator_note": (
            "row_count and distinct_game_play_key_count are reported separately; neither is "
            "an official snap denominator and no snap count is inferred."
        ),
    }


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def read_one_game(
    *,
    path: str | Path,
    expected_bytes: int,
    expected_sha256: str,
    request: GameRequest,
    possession: PossessionRequest | None = None,
    declaration: SourceDeclaration | None = None,
) -> dict[str, Any]:
    """Run the full offline path. Returns a result dict; never raises on rejection."""
    declaration = declaration or SourceDeclaration()
    validate_receipt_expectations(expected_bytes, expected_sha256)
    request.validate()
    if possession is not None:
        possession.validate()
    source_path = Path(path)
    receipt = _base_receipt(
        supplied_path=str(path),
        expected_bytes=expected_bytes,
        expected_sha256=expected_sha256,
        declaration=declaration,
    )
    try:
        content = verify_source_bytes(
            source_path,
            expected_bytes=expected_bytes,
            expected_sha256=expected_sha256,
            receipt=receipt,
        )
    except SourceRejected as rejected:
        return rejected.result

    partial: dict[str, Any] = {"game": None}
    try:
        return _read_verified_content(content, receipt, request, possession, partial)
    except _EngineFailure as failure:
        # Only parquet engine stages land here: attributable to the source bytes.
        return _rejection(
            receipt,
            "parse_failure",
            failure.detail,
            parsed=PARSE_ATTEMPTED_FAILED,
            read_stage=failure.stage,
        )
    except _ProcessingFailure as failure:
        # Pure post-parse reader defect: never labeled as a parser or source failure.
        return _processing_failed(receipt, failure.stage, failure.detail, partial["game"])


def _read_verified_content(
    content: bytes,
    receipt: dict[str, Any],
    request: GameRequest,
    possession: PossessionRequest | None,
    partial: dict[str, Any],
) -> dict[str, Any]:
    schema = inspect_schema(content)
    with _processing_stage("locate_game_matching"):
        location = locate_game(content, schema, request)
        # The raw typed game ID drives the scans below; only its JSON form is emitted.
        game_id_raw = location.pop("_game_id_raw", None)
    partial["game"] = location
    result: dict[str, Any] = {
        "status": None,
        "rejection": None,
        "failure": None,
        "receipt": receipt,
        "game": location,
        "inventory": None,
        "possession": None,
        "events": None,
    }
    if location["status"] != "matched":
        result["status"] = "unresolved"
        receipt["times"]["processing_time"] = _now_iso()
        return result

    rows, read_strategy = load_game_rows(content, game_id_raw)
    with _processing_stage("inventory_duplicates"):
        duplicates = inventory_duplicates(rows)
    with _processing_stage("inventory_fields"):
        fields = inventory_fields(rows, schema)
    with _processing_stage("build_possession_sequence"):
        sequence = build_possession_sequence(rows, schema)
    with _processing_stage("assemble_result"):
        compact_runs = [
            {
                k: v
                for k, v in run.items()
                if k in (
                    "sequence_index", "posteam", "posteam_raw", "provider_drive",
                    "team_possession_ordinal", "first_play_id", "last_play_id",
                    "attributed_row_count",
                )
            }
            for run in sequence["runs"]
        ]
        possession_block: dict[str, Any] = {
            "basis": sequence["basis"],
            "unattributed_rows": sequence["unattributed_rows"],
            "play_id_null_rows": sequence["play_id_null_rows"],
            "play_id_non_finite_rows": sequence["play_id_non_finite_rows"],
            "play_id_non_numeric_rows": sequence["play_id_non_numeric_rows"],
            "runs": compact_runs,
            "selection": None,
        }
    if possession is not None:
        with _processing_stage("select_possession"):
            order_conflicts = tuple(
                d["play_id"] for d in duplicates["conflicting_duplicate_keys"]
                if d.get("affects_possession_order")
            )
            selection = select_possession(
                sequence, possession, order_affecting_conflict_play_ids=order_conflicts
            )
            possession_block["selection"] = {
                k: v for k, v in selection.items() if k != "selected_run"
            } | {
                "selected_run": (
                    {
                        k: v for k, v in selection["selected_run"].items()
                        if not k.endswith("_index")
                    }
                    if selection["selected_run"]
                    else None
                )
            }
        with _processing_stage("select_events"):
            events = select_events(rows, selection, schema)
    else:
        events = _empty_events("not_requested", "no possession selection requested")
    with _processing_stage("assemble_result"):
        result["inventory"] = {
            "keys": duplicates, "fields": fields, "read_strategy": read_strategy,
        }
        result["possession"] = possession_block
        result["events"] = events
        result["status"] = "read"
    receipt["times"]["processing_time"] = _now_iso()
    return result


def dumps(result: dict[str, Any]) -> str:
    return json.dumps(_jsonable(result), indent=2, sort_keys=True, allow_nan=False) + "\n"


def dumps_bounded(result: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """Serialize a result; if serialization itself fails, return a bounded
    `reader_processing_failure` at stage `serialize_result` instead of raising."""
    try:
        return dumps(result), result
    except (TypeError, ValueError) as exc:
        failed = _processing_failed(
            result["receipt"], "serialize_result", f"{type(exc).__name__}: {exc}", None
        )
        return dumps(failed), failed

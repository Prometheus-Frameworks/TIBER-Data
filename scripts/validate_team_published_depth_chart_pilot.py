"""Fail-closed validation helpers for the TIBER-Data #231 D0 pilot.

This module validates contracts, hash-pinned observation metadata, source
allowlisting, freshness advancement, and deterministic diffs. It deliberately
does not fetch, mirror, parse, transcribe, promote, or publish team content.
"""

from __future__ import annotations

import json
from copy import deepcopy
from datetime import date, datetime, time, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from jsonschema import Draft202012Validator, FormatChecker, ValidationError

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_SCHEMA = ROOT / "schemas/team_published_depth_chart_snapshot_v0.schema.json"
REGISTRY_SCHEMA = ROOT / "schemas/team_published_depth_chart_source_registry_v0.schema.json"
REGISTRY = ROOT / "data/candidate/depth_charts/official_source_registry_v0.json"
RECEIPTS = ROOT / "data/candidate/depth_charts/source_observation_receipts_2026-08-10.json"
AUDIT = ROOT / "docs/audits/official-depth-chart-pilot-readiness-2026-08-10.json"
CANDIDATE_MANIFEST = (
    ROOT / "data/candidate/depth_charts/normalized_candidate_manifest_2026-08-10.json"
)

CANONICAL_TEAM_ORDER = (
    "ARI",
    "ATL",
    "BAL",
    "BUF",
    "CAR",
    "CHI",
    "CIN",
    "CLE",
    "DAL",
    "DEN",
    "DET",
    "GB",
    "HOU",
    "IND",
    "JAX",
    "KC",
    "LAC",
    "LAR",
    "LV",
    "MIA",
    "MIN",
    "NE",
    "NO",
    "NYG",
    "NYJ",
    "PHI",
    "PIT",
    "SF",
    "SEA",
    "TB",
    "TEN",
    "WAS",
)
TEAM_OFFICIAL_HOST = {
    "ARI": "azcardinals.com",
    "ATL": "atlantafalcons.com",
    "BAL": "baltimoreravens.com",
    "BUF": "buffalobills.com",
    "CAR": "panthers.com",
    "CHI": "chicagobears.com",
    "CIN": "bengals.com",
    "CLE": "clevelandbrowns.com",
    "DAL": "dallascowboys.com",
    "DEN": "denverbroncos.com",
    "DET": "detroitlions.com",
    "GB": "packers.com",
    "HOU": "houstontexans.com",
    "IND": "colts.com",
    "JAX": "jaguars.com",
    "KC": "chiefs.com",
    "LAC": "chargers.com",
    "LAR": "therams.com",
    "LV": "raiders.com",
    "MIA": "miamidolphins.com",
    "MIN": "vikings.com",
    "NE": "patriots.com",
    "NO": "neworleanssaints.com",
    "NYG": "giants.com",
    "NYJ": "newyorkjets.com",
    "PHI": "philadelphiaeagles.com",
    "PIT": "steelers.com",
    "SF": "49ers.com",
    "SEA": "seahawks.com",
    "TB": "buccaneers.com",
    "TEN": "tennesseetitans.com",
    "WAS": "commanders.com",
}
TEAM_OFFICIAL_ASSET_PREFIXES = {
    "ARI": {"static.clubs.nfl.com": ("/image/upload/cardinals/",)},
}
OFFICIAL_HOSTS = frozenset({*TEAM_OFFICIAL_HOST.values(), "static.clubs.nfl.com"})
IMMUTABLE_RECEIPT_ROOT = Path("data/raw/depth_charts")
NORMALIZED_CANDIDATE_ROOT = Path("data/candidate/depth_charts/normalized")
BOUNDED_PILOT_TEAMS = ("ARI", "WAS", "PIT", "CAR")
# Formats the pilot contracts declare and therefore must actually enforce.
REQUIRED_SCHEMA_FORMATS = ("date", "date-time")
# Coverage states that assert snapshot evidence exists, so it must be recorded.
EVIDENCE_REQUIRING_COVERAGE_STATES = frozenset(
    {"captured_candidate", "verified_current", "superseded"}
)
# Monitor statuses that assert no probe was performed, so no clock is expected.
# Any other status claims an observation and must carry its observation clock.
CLOCK_EXEMPT_MONITOR_STATUSES = frozenset(
    {"not_checked_in_bounded_pilot", "scheduler_not_authorized"}
)


class PilotValidationError(RuntimeError):
    """Raised when a pilot invariant fails closed."""


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_json_bytes(payload: Any) -> bytes:
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return (text + "\n").encode("utf-8")


def canonical_sha256(payload: Any) -> str:
    return sha256(canonical_json_bytes(payload)).hexdigest()


def pilot_format_checker() -> FormatChecker:
    """Fail closed when a declared format would be silently unenforced.

    ``jsonschema`` only registers ``date-time`` when its format extras are
    installed, so a missing dependency would otherwise downgrade timestamp
    validation to an unchecked string.
    """
    checker = FormatChecker()
    missing = [name for name in REQUIRED_SCHEMA_FORMATS if name not in checker.checkers]
    if missing:
        raise PilotValidationError(
            f"Schema format enforcement unavailable for {', '.join(missing)}; "
            "install jsonschema[format]"
        )
    return checker


def schema_validator(path: Path) -> Draft202012Validator:
    return Draft202012Validator(load_json(path), format_checker=pilot_format_checker())


def normalized_hostname(url: str) -> str:
    parsed = urlparse(url)
    try:
        port = parsed.port
    except ValueError as exc:
        raise PilotValidationError(f"Official source URL has an invalid port: {url}") from exc
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or port not in (None, 443)
    ):
        raise PilotValidationError(f"Official source URL must use https: {url}")
    host = parsed.hostname.lower()
    return host.removeprefix("www.")


def official_source_allowed(url: str) -> bool:
    try:
        return normalized_hostname(url) in OFFICIAL_HOSTS
    except PilotValidationError:
        return False


def official_source_allowed_for_team(team_abbr: str, url: str) -> bool:
    """Require an HTTPS official host that is explicitly coupled to the team."""
    try:
        host = normalized_hostname(url)
    except PilotValidationError:
        return False
    if host == TEAM_OFFICIAL_HOST.get(team_abbr):
        return True
    prefixes = TEAM_OFFICIAL_ASSET_PREFIXES.get(team_abbr, {}).get(host, ())
    path = urlparse(url).path
    if ".." in Path(path).parts or "%" in path:
        return False
    return any(path.startswith(prefix) for prefix in prefixes)


def validate_registry(payload: dict[str, Any]) -> None:
    schema_validator(REGISTRY_SCHEMA).validate(payload)
    teams = payload["teams"]
    ids = [team["team_id"] for team in teams]
    if len(ids) != 32 or len(set(ids)) != 32:
        raise PilotValidationError("Registry must contain exactly 32 unique team IDs")
    if tuple(ids) != CANONICAL_TEAM_ORDER:
        raise PilotValidationError(
            "Registry team rows drifted from the canonical deterministic order"
        )

    for team in teams:
        if team["team_id"] != team["team_abbr"]:
            raise PilotValidationError(f"Team ID/abbreviation drift: {team['team_id']}")
        for key in ("official_team_home_url", "official_depth_chart_page_candidate"):
            url = team[key]
            if url is not None and not official_source_allowed_for_team(team["team_abbr"], url):
                raise PilotValidationError(
                    f"Source host is not official for {team['team_abbr']}: {url}"
                )
        if team["coverage_state"] == "not_yet_published" and team["last_checked_at"] is None:
            raise PilotValidationError("not_yet_published requires an observation clock")
        if (
            team["monitor_status"] not in CLOCK_EXEMPT_MONITOR_STATUSES
            and team["last_checked_at"] is None
        ):
            raise PilotValidationError(
                f"Monitor status {team['monitor_status']} requires an observation clock"
            )
        if (
            team["coverage_state"] in EVIDENCE_REQUIRING_COVERAGE_STATES
            and team["latest_verified_snapshot_id"] is None
        ):
            raise PilotValidationError(
                f"Coverage state {team['coverage_state']} requires snapshot evidence"
            )
        if team["latest_verified_snapshot_id"] is not None:
            required = (
                team["last_qualifying_effective_date"],
                team["latest_verified_snapshot_sha256"],
            )
            if any(value is None for value in required):
                raise PilotValidationError(
                    "Verified latest requires an effective date and content hash"
                )


def validate_receipts(payload: dict[str, Any]) -> None:
    comparison_scope = payload.get("comparison_scope")
    if not isinstance(comparison_scope, dict):
        raise PilotValidationError("Observation ledger must declare comparison scope")
    if comparison_scope.get("kind") != "same_bounded_probe_hash_comparison":
        raise PilotValidationError("Observation ledger overstates its hash comparison scope")
    if comparison_scope.get("independent_monitor_run") is not False:
        raise PilotValidationError("Bounded probe must not claim an independent monitor run")
    if comparison_scope.get("comparison_run_id_recorded") is not False:
        raise PilotValidationError("Unrecorded comparison run ID must remain explicit")
    if comparison_scope.get("comparison_clock_recorded") is not False:
        raise PilotValidationError("Unrecorded comparison clock must remain explicit")

    receipts = payload.get("receipts")
    if not isinstance(receipts, list) or not receipts:
        raise PilotValidationError("Observation ledger must contain receipts")
    seen: set[str] = set()
    for receipt in receipts:
        receipt_id = receipt["receipt_id"]
        if receipt_id in seen:
            raise PilotValidationError(f"Duplicate receipt ID: {receipt_id}")
        seen.add(receipt_id)
        if not official_source_allowed_for_team(receipt["team_abbr"], receipt["source_url"]):
            raise PilotValidationError(
                f"Receipt source is not official for {receipt['team_abbr']}: "
                f"{receipt['source_url']}"
            )
        if receipt["external_source_classification"] != "external_candidate":
            raise PilotValidationError(f"Unexpected source classification: {receipt_id}")
        if not valid_sha256(receipt["sha256"]):
            raise PilotValidationError(f"Malformed source SHA-256: {receipt_id}")
        comparison_sha = receipt["same_probe_comparison_sha256"]
        if not valid_sha256(comparison_sha):
            raise PilotValidationError(f"Malformed comparison SHA-256: {receipt_id}")
        hash_equal = receipt["sha256"] == comparison_sha
        if receipt["same_probe_hash_equal"] is not hash_equal:
            raise PilotValidationError(f"Hash comparison boolean drifted: {receipt_id}")
        expected_disposition = (
            "same_probe_hash_stable_no_snapshot"
            if hash_equal
            else "same_probe_hash_changed_quarantine_no_advance"
        )
        if receipt["same_probe_disposition"] != expected_disposition:
            raise PilotValidationError(f"Hash disposition drifted: {receipt_id}")
        if receipt["byte_length"] <= 0:
            raise PilotValidationError(f"Empty source receipt: {receipt_id}")
        if receipt["archive_status"] == "blocked_rights_unresolved":
            if receipt["repository_receipt_path"] is not None:
                raise PilotValidationError(f"Rights-blocked receipt was mirrored: {receipt_id}")
            if receipt["license_observed"] is not None:
                raise PilotValidationError(
                    f"Rights blocker conflicts with a declared license: {receipt_id}"
                )


def valid_sha256(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(
        character in "0123456789abcdef" for character in value
    )


def classify_source_hash_run(
    previous_sha256: str | None,
    current_sha256: str | None,
    *,
    changed_candidate_parse_succeeded: bool | None = None,
) -> str:
    """Classify hash evidence without inferring monitor health or advancement."""
    if previous_sha256 is not None and not valid_sha256(previous_sha256):
        raise PilotValidationError("Malformed prior run SHA-256")
    if current_sha256 is not None and not valid_sha256(current_sha256):
        raise PilotValidationError("Malformed current run SHA-256")
    if current_sha256 is None:
        return "monitor_degraded_no_advance"
    if previous_sha256 is None:
        return "initial_hash_candidate_pending_validation_no_advance"
    if current_sha256 == previous_sha256:
        return "stable_observation_only_no_snapshot_no_health_claim"
    if changed_candidate_parse_succeeded is False:
        return "changed_hash_parse_quarantined_no_advance"
    if changed_candidate_parse_succeeded is True:
        return "changed_hash_requires_full_validation_no_advance"
    return "changed_hash_pending_parse_no_advance"


def _resolve_repository_path(
    relative_path: str,
    *,
    repository_root: Path,
    required_root: Path,
) -> Path:
    candidate_relative = Path(relative_path)
    if candidate_relative.is_absolute() or ".." in candidate_relative.parts:
        raise PilotValidationError(f"Unsafe repository-relative path: {relative_path}")
    try:
        candidate_relative.relative_to(required_root)
    except ValueError as exc:
        raise PilotValidationError(
            f"Path must remain under {required_root.as_posix()}: {relative_path}"
        ) from exc

    root = repository_root.resolve()
    unresolved = root / candidate_relative
    cursor = root
    for part in candidate_relative.parts:
        cursor /= part
        if cursor.is_symlink():
            raise PilotValidationError(
                f"Repository evidence path cannot traverse a symlink: {relative_path}"
            )
    resolved = unresolved.resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise PilotValidationError(f"Repository path escaped its root: {relative_path}") from exc
    return resolved


def _validate_immutable_receipt_bytes(receipt: dict[str, Any], *, receipt_root: Path) -> None:
    if receipt["archive_status"] != "stored_immutable":
        return
    relative_path = receipt.get("immutable_receipt_path")
    if not isinstance(relative_path, str):
        raise PilotValidationError("stored_immutable receipt requires an immutable path")
    source_path = _resolve_repository_path(
        relative_path,
        repository_root=receipt_root,
        required_root=IMMUTABLE_RECEIPT_ROOT,
    )
    if not source_path.is_file():
        raise PilotValidationError(f"Immutable receipt bytes are missing: {relative_path}")
    source_bytes = source_path.read_bytes()
    if len(source_bytes) != receipt["byte_length"]:
        raise PilotValidationError(f"Immutable receipt byte length drifted: {relative_path}")
    if sha256(source_bytes).hexdigest() != receipt["sha256"]:
        raise PilotValidationError(f"Immutable receipt SHA-256 drifted: {relative_path}")


def validate_snapshot(payload: dict[str, Any], *, receipt_root: Path = ROOT) -> None:
    schema_validator(SNAPSHOT_SCHEMA).validate(payload)
    team_abbr = payload["team_abbr"]
    if payload["team_id"] is not None and payload["team_id"] != team_abbr:
        raise PilotValidationError("Snapshot team_id and team_abbr must agree")
    if not official_source_allowed_for_team(team_abbr, payload["canonical_source_url"]):
        raise PilotValidationError(
            f"Canonical source is not official for {team_abbr}: "
            f"{payload['canonical_source_url']}"
        )

    receipt_ids = [receipt["receipt_id"] for receipt in payload["source_receipts"]]
    if len(receipt_ids) != len(set(receipt_ids)):
        raise PilotValidationError("Snapshot receipt IDs must be unique")
    receipt_urls: set[str] = set()
    for receipt in payload["source_receipts"]:
        source_url = receipt["source_url"]
        if not official_source_allowed_for_team(team_abbr, source_url):
            raise PilotValidationError(
                f"Snapshot receipt is not official for {team_abbr}: {source_url}"
            )
        receipt_urls.add(source_url)
        _validate_immutable_receipt_bytes(receipt, receipt_root=receipt_root)
    if payload["canonical_source_url"] not in receipt_urls:
        raise PilotValidationError("Canonical source URL must be represented by an exact receipt")

    row_ids = [row["row_instance_id"] for row in payload["rows"]]
    if len(row_ids) != len(set(row_ids)):
        raise PilotValidationError("Snapshot row IDs must be unique")
    if payload["transcription"]["normalized_row_count"] != len(payload["rows"]):
        raise PilotValidationError("Normalized row count does not match rows")
    entry_count = sum(len(row["entries"]) for row in payload["rows"])
    if payload["transcription"]["normalized_entry_count"] != entry_count:
        raise PilotValidationError("Normalized entry count does not match entries")
    if payload["normalization_status"] == "complete":
        source_row_count = payload["transcription"]["source_row_count"]
        source_entry_count = payload["transcription"]["source_entry_count"]
        normalized_row_count = payload["transcription"]["normalized_row_count"]
        normalized_entry_count = payload["transcription"]["normalized_entry_count"]
        if any(
            receipt["archive_status"] != "stored_immutable"
            for receipt in payload["source_receipts"]
        ):
            raise PilotValidationError(
                "Complete candidate requires retained immutable bytes for every receipt"
            )
        if not payload["rows"] or entry_count == 0:
            raise PilotValidationError("Complete candidate requires nonempty normalized evidence")
        if source_row_count is None or source_row_count <= 0:
            raise PilotValidationError("Complete candidate requires nonempty source-row evidence")
        if source_entry_count is None or source_entry_count <= 0:
            raise PilotValidationError("Complete candidate requires nonempty source-entry evidence")
        if source_row_count != normalized_row_count:
            raise PilotValidationError(
                "Complete v0 candidate requires exact source/normalized row reconciliation"
            )
        if source_entry_count != normalized_entry_count:
            raise PilotValidationError(
                "Complete v0 candidate requires exact source/normalized entry reconciliation"
            )

    for row in payload["rows"]:
        for entry in row["entries"]:
            if entry["identity_status"] != "resolved_exact" and entry["player_id"] is not None:
                raise PilotValidationError(
                    "Unresolved or ambiguous identity must retain player_id=null"
                )
            if entry["identity_status"] == "resolved_exact":
                if not entry["player_id"]:
                    raise PilotValidationError("Resolved identity requires a canonical player ID")
                if not entry["identity_resolution_method"]:
                    raise PilotValidationError(
                        "Resolved identity requires an explicit resolution method"
                    )
            if entry["decoded_marker_meanings"]:
                raise PilotValidationError("Marker decoding is prohibited in contract v0")
            if entry["decoded_marker_legend_reference"] is not None:
                raise PilotValidationError("Marker legend binding is prohibited in contract v0")


def _parse_timezone_aware_datetime(value: str) -> datetime:
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise PilotValidationError("Publication clock must be timezone-aware")
    return parsed.astimezone(timezone.utc)


def snapshot_evidence_key(snapshot: dict[str, Any]) -> tuple[date, datetime] | None:
    published_at = snapshot.get("published_at")
    publication_clock = (
        _parse_timezone_aware_datetime(published_at) if published_at is not None else None
    )
    chart_as_of = snapshot.get("chart_as_of")
    if chart_as_of is None:
        return None
    effective_date = date.fromisoformat(chart_as_of)
    publication_tiebreaker = publication_clock or datetime.combine(
        effective_date, time.min, tzinfo=timezone.utc
    )
    return effective_date, publication_tiebreaker


def candidate_can_advance(snapshot: dict[str, Any], *, receipt_root: Path = ROOT) -> bool:
    try:
        validate_snapshot(snapshot, receipt_root=receipt_root)
    except (KeyError, OSError, TypeError, ValueError, ValidationError, PilotValidationError):
        return False
    if snapshot.get("normalization_status") != "complete":
        return False
    if snapshot.get("verification_status") != "candidate_structurally_validated":
        return False
    try:
        if snapshot_evidence_key(snapshot) is None:
            return False
    except (TypeError, ValueError, PilotValidationError):
        # An unparseable chronology is an invalid candidate, not a crash: the
        # caller must still fall back to prior-snapshot retention.
        return False
    receipts = snapshot.get("source_receipts", [])
    return bool(receipts) and all(
        receipt.get("archive_status") == "stored_immutable" for receipt in receipts
    )


def advance_latest(
    prior_verified: dict[str, Any] | None,
    changed_candidate: dict[str, Any],
    *,
    receipt_root: Path = ROOT,
) -> dict[str, Any] | None:
    """Advance only on a newer, complete, rights-cleared, structurally validated candidate."""
    if not candidate_can_advance(changed_candidate, receipt_root=receipt_root):
        return deepcopy(prior_verified)
    if prior_verified is None:
        return deepcopy(changed_candidate)
    if not candidate_can_advance(prior_verified, receipt_root=receipt_root):
        return deepcopy(prior_verified)
    stream_fields = ("contract_version", "assertion_scope", "team_abbr", "season")
    if any(prior_verified[field] != changed_candidate[field] for field in stream_fields):
        return deepcopy(prior_verified)
    prior_hashes = tuple(
        sorted({receipt["sha256"] for receipt in prior_verified["source_receipts"]})
    )
    candidate_hashes = tuple(
        sorted({receipt["sha256"] for receipt in changed_candidate["source_receipts"]})
    )
    if candidate_hashes == prior_hashes:
        return deepcopy(prior_verified)
    try:
        prior_key = snapshot_evidence_key(prior_verified)
        candidate_key = snapshot_evidence_key(changed_candidate)
    except (TypeError, ValueError, PilotValidationError):
        return deepcopy(prior_verified)
    if prior_key is None or candidate_key is None or candidate_key <= prior_key:
        return deepcopy(prior_verified)
    return deepcopy(changed_candidate)


def _entry_index(snapshot: dict[str, Any]) -> dict[tuple[Any, ...], dict[str, Any]]:
    index: dict[tuple[Any, ...], dict[str, Any]] = {}
    for row in snapshot.get("rows", []):
        for entry in row.get("entries", []):
            key = (
                row["unit"],
                row["row_instance_id"],
                entry["display_column"],
                entry["display_order_within_column"],
                entry["raw_source_text"],
            )
            if key in index:
                raise PilotValidationError(f"Duplicate semantic entry key: {key}")
            index[key] = {"row": row["source_position_label_raw"], "entry": deepcopy(entry)}
    return index


def deterministic_snapshot_diff(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    left = _entry_index(before)
    right = _entry_index(after)
    left_keys = set(left)
    right_keys = set(right)
    added = [{"key": list(key), "after": right[key]} for key in sorted(right_keys - left_keys)]
    removed = [{"key": list(key), "before": left[key]} for key in sorted(left_keys - right_keys)]
    changed = [
        {"key": list(key), "before": left[key], "after": right[key]}
        for key in sorted(left_keys & right_keys)
        if canonical_sha256(left[key]) != canonical_sha256(right[key])
    ]
    return {"added": added, "removed": removed, "changed": changed}


def validate_candidate_manifest(
    payload: dict[str, Any],
    audit: dict[str, Any],
    *,
    repository_root: Path = ROOT,
) -> list[dict[str, Any]]:
    required_keys = {
        "artifact_type",
        "artifact_version",
        "issue",
        "snapshot_contract_version",
        "bounded_teams",
        "candidate_root",
        "candidate_snapshot_paths",
        "empty_reason",
    }
    if set(payload) != required_keys:
        raise PilotValidationError("Candidate manifest envelope drifted")
    if payload["artifact_type"] != "official_depth_chart_normalized_candidate_manifest":
        raise PilotValidationError("Unexpected candidate manifest artifact type")
    if payload["artifact_version"] != "official_depth_chart_normalized_candidate_manifest_v0":
        raise PilotValidationError("Unexpected candidate manifest version")
    if payload["issue"] != audit["issue"]:
        raise PilotValidationError("Candidate manifest issue drift")
    if payload["snapshot_contract_version"] != "team_published_depth_chart_snapshot_v0":
        raise PilotValidationError("Candidate manifest contract drift")
    if tuple(audit["bounded_scope"]["pilot_teams"]) != BOUNDED_PILOT_TEAMS:
        raise PilotValidationError("Audit pilot-team scope drifted from activation")
    if tuple(payload["bounded_teams"]) != BOUNDED_PILOT_TEAMS:
        raise PilotValidationError("Candidate manifest escaped the bounded pilot teams")
    if not isinstance(payload["empty_reason"], str) or not payload["empty_reason"].strip():
        raise PilotValidationError("Candidate manifest requires an explicit disposition")
    if payload["candidate_root"] != NORMALIZED_CANDIDATE_ROOT.as_posix():
        raise PilotValidationError("Candidate manifest root drifted")

    listed_paths = payload["candidate_snapshot_paths"]
    if not isinstance(listed_paths, list) or any(
        not isinstance(path, str) for path in listed_paths
    ):
        raise PilotValidationError("Candidate manifest paths must be a list of strings")
    if listed_paths != sorted(set(listed_paths)):
        raise PilotValidationError("Candidate manifest paths must be unique and sorted")

    root = repository_root.resolve()
    candidate_directory = _resolve_repository_path(
        payload["candidate_root"],
        repository_root=repository_root,
        required_root=NORMALIZED_CANDIDATE_ROOT,
    )
    actual_paths = (
        sorted(
            path.resolve().relative_to(root).as_posix()
            for path in candidate_directory.rglob("*.json")
            if path.is_file()
        )
        if candidate_directory.exists()
        else []
    )
    if listed_paths != actual_paths:
        raise PilotValidationError("Candidate manifest does not match its bounded directory")

    candidates: list[dict[str, Any]] = []
    allowed_teams = set(payload["bounded_teams"])
    for relative_path in listed_paths:
        snapshot_path = _resolve_repository_path(
            relative_path,
            repository_root=repository_root,
            required_root=NORMALIZED_CANDIDATE_ROOT,
        )
        snapshot = load_json(snapshot_path)
        if snapshot.get("team_abbr") not in allowed_teams:
            raise PilotValidationError("Manifested candidate escaped the bounded team set")
        validate_snapshot(snapshot, receipt_root=repository_root)
        candidates.append(snapshot)
    return candidates


def validate_pilot_files() -> dict[str, Any]:
    registry = load_json(REGISTRY)
    receipts = load_json(RECEIPTS)
    audit = load_json(AUDIT)
    candidate_manifest = load_json(CANDIDATE_MANIFEST)
    validate_registry(registry)
    validate_receipts(receipts)

    if audit["source_registry_path"] != str(REGISTRY.relative_to(ROOT)):
        raise PilotValidationError("Audit/registry path drift")
    if audit["source_observation_receipts_path"] != str(RECEIPTS.relative_to(ROOT)):
        raise PilotValidationError("Audit/receipt path drift")
    if audit["normalized_candidate_manifest_path"] != str(
        CANDIDATE_MANIFEST.relative_to(ROOT)
    ):
        raise PilotValidationError("Audit/candidate-manifest path drift")
    candidates = validate_candidate_manifest(candidate_manifest, audit)
    if any(result["normalization_output_committed"] for result in audit["format_probe_results"]):
        raise PilotValidationError(
            "Audit claims a normalized candidate despite the receipt blocker"
        )
    decision = audit.get("terminal_decision")
    if not isinstance(decision, str) or not decision.startswith("official_depth_chart_pilot_"):
        raise PilotValidationError("Missing or malformed terminal decision")

    return {
        "registry_team_count": len(registry["teams"]),
        "observation_receipt_count": len(receipts["receipts"]),
        "format_probe_count": len(audit["format_probe_results"]),
        "normalized_candidate_count": len(candidates),
        "terminal_decision": decision,
    }


def main() -> int:
    print(json.dumps(validate_pilot_files(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Fail-closed manifest/digest gate for rb_contact_evasion_observations_v0 bundles.

TIBER-Data #234, Slice B. Slice A shipped the contract, the JSON Schema, the
documentation and the fixture corpus. This module is the boundary a *future*
candidate bundle has to cross before anything downstream may read it.

Single semantic authority
-------------------------
This gate deliberately contains **no football semantics**. It knows nothing
about mechanisms, metrics, denominators, clocks, cohorts, rights or
missingness. Every semantic judgment is delegated, unchanged, to Slice A's
canonical public evaluator ``evaluateRbContactEvasionObservationsV0`` via
``scripts/rb_contact_evasion_contract_bridge.mjs``, and that evaluator's exact
machine-readable reason codes are reproduced verbatim. Shape judgment is
delegated to the committed JSON Schema. Porting either into Python would create
a second, competing authority, so neither is ported.

What this gate does own
-----------------------
Everything that has to be true *before* a payload claim can be trusted:

1. the manifest is readable, parses, and matches the committed manifest schema;
2. the declared contract identity equals the identity pinned **in this file**,
   which is itself cross-checked against the canonical contract;
3. every declared path is relative, contained, and a real regular file;
4. the manifest and the bundle are in exact bijection;
5. byte size and SHA-256 are verified **before** any parse or evaluation;
6. the payload parses strictly (a matching digest never excuses malformed JSON);
7. the committed JSON Schema shape gate is applied;
8. the manifest agrees with the payload it describes, and can never weaken it;
9. the canonical evaluator judges the exact verified bytes.

Stages run in that order and the result is fail-closed at every one: a stage
that cannot run is a failure, never a skip. The gate performs no network access
and opens every path read-only, so it never mutates what it validates.

Usage::

    python3 scripts/validate_rb_contact_evasion_bundle.py <bundle-root>
    python3 scripts/validate_rb_contact_evasion_bundle.py <bundle-root> --json
    python3 scripts/validate_rb_contact_evasion_bundle.py <bundle-root> --json-out result.json

Exit codes: ``0`` the bundle passed, ``1`` the bundle failed the gate, ``2`` the
invocation itself was invalid.

The semantic stage requires the compiled contract under ``dist/`` (run
``npm run build``). If it is absent the gate fails closed rather than reporting
a pass it could not establish.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any

import jsonschema

REPO_ROOT = Path(__file__).resolve().parents[1]

GATE_ID = "rb_contact_evasion_observations_bundle_gate_v0"

# ---------------------------------------------------------------------------
# Pinned contract identity
# ---------------------------------------------------------------------------
# These are pinned HERE, in code, and not taken from the manifest. A manifest is
# editable data: if it were allowed to name its own artifact id, schema version
# or digest algorithm, a candidate could declare itself into admissibility. The
# pins are additionally cross-checked against the canonical contract at run time
# (see ``check_contract_identity``) so that they cannot silently drift away from
# Slice A either.
PINNED_MANIFEST_VERSION = "rb_contact_evasion_observations_bundle_manifest_v0.1.0"
PINNED_ARTIFACT_ID = "rb_contact_evasion_observations_v0"
PINNED_SCHEMA_VERSION = "rb_contact_evasion_observations_v0.4.0"
ADMITTED_DIGEST_ALGORITHMS = frozenset({"sha256"})
DIGEST_HEX_LENGTHS = {"sha256": 64}

# The manifest name is pinned rather than configurable: a caller able to point
# the gate at a different manifest could point it at a friendlier one.
MANIFEST_FILENAME = "manifest.json"

MANIFEST_SCHEMA_PATH = (
    REPO_ROOT / "schemas/rb_contact_evasion_observations_bundle_manifest_v0.schema.json"
)
ARTIFACT_SCHEMA_PATH = REPO_ROOT / "schemas/rb_contact_evasion_observations_v0.schema.json"
BRIDGE_PATH = REPO_ROOT / "scripts/rb_contact_evasion_contract_bridge.mjs"
COMPILED_CONTRACT_PATH = REPO_ROOT / "dist/src/index.js"

# Bounded reads. A declared size above the cap is rejected before anything is
# read, so a hostile manifest cannot ask the gate to load an arbitrary file.
MANIFEST_MAX_BYTES = 1_048_576
ARTIFACT_MAX_BYTES = 67_108_864
BRIDGE_TIMEOUT_SECONDS = 120

# Ordered stages. The order is part of the contract: integrity is established
# before any parse, and parsing before any semantic claim.
STAGES = (
    "manifest_read",
    "manifest_parse",
    "manifest_shape",
    "contract_identity",
    "path_safety",
    "bundle_bijection",
    "integrity",
    "payload_parse",
    "payload_shape",
    "manifest_payload_agreement",
    "semantic",
)
_STAGE_ORDER = {stage: index for index, stage in enumerate(STAGES)}

# Manifest keys that would, if present, let integrity metadata speak for the
# contract. The committed manifest schema is closed, so none of these can
# validate; this set exists so the ban is asserted directly and a future schema
# widening cannot quietly reopen the hole.
FORBIDDEN_MANIFEST_KEYS = frozenset(
    {
        "acquisition_method",
        "access_class",
        "advice",
        "attribution",
        "caveat_ids",
        "cohort",
        "cohort_scope",
        "contract_valid",
        "elite",
        "evidence_class",
        "exempt",
        "exemptions",
        "grade",
        "measurement",
        "mechanism_id",
        "metric",
        "metric_dictionary",
        "metric_id",
        "minimum_sample_rule_id",
        "missingness_reason",
        "observations",
        "override",
        "overrides",
        "percentile",
        "permissions",
        "promotable",
        "provenance_mode",
        "rank",
        "ranking",
        "rating",
        "reason_codes",
        "rights_review_ref",
        "score",
        "skip_checks",
        "skip_semantic_validation",
        "suppress",
        "suppressed_reason_codes",
        "tier",
        "trusted",
        "valid",
        "validated",
        "waiver",
        "waivers",
    }
)


class GateUsageError(Exception):
    """The invocation itself was invalid. Distinct from a bundle failure."""


class _Unparsed:
    """Sentinel for "no payload has been parsed yet".

    ``None`` cannot serve here: a file containing the four bytes ``null`` parses
    to ``None`` perfectly legitimately, and using ``None`` as the sentinel would
    let such a payload slip past the shape gate and the evaluator untouched.
    """

    def __repr__(self) -> str:  # pragma: no cover - diagnostics only
        return "<unparsed>"


UNPARSED = _Unparsed()


@dataclass(frozen=True)
class Failure:
    """One fail-closed finding. ``path`` is bundle-relative, never absolute."""

    stage: str
    reason_code: str
    path: str
    detail: str

    def as_dict(self) -> dict[str, str]:
        return {
            "stage": self.stage,
            "reason_code": self.reason_code,
            "path": self.path,
            "detail": self.detail,
        }

    def sort_key(self) -> tuple[int, str, str, str]:
        return (_STAGE_ORDER.get(self.stage, len(STAGES)), self.path, self.reason_code, self.detail)


@dataclass
class ArtifactState:
    """Per-entry state, carried between stages."""

    path: str
    declared_size: int
    declared_digest: str
    absolute: Path | None = None
    stages_passed: list[str] = field(default_factory=list)
    observed_size: int | None = None
    observed_digest: str | None = None
    raw_bytes: bytes | None = None
    payload: Any = UNPARSED
    contract: dict[str, Any] | None = None
    blocked: bool = False

    def block(self) -> None:
        self.blocked = True

    def passed(self, stage: str) -> None:
        self.stages_passed.append(stage)


@dataclass
class GateResult:
    """Deterministic, machine-readable outcome. Contains no clock and no
    absolute path, so two runs over the same bytes produce identical JSON."""

    ok: bool
    failures: list[Failure]
    artifacts: list[ArtifactState]

    @property
    def reason_codes(self) -> list[str]:
        return sorted({failure.reason_code for failure in self.failures})

    def as_dict(self) -> dict[str, Any]:
        return {
            "gate": GATE_ID,
            "ok": self.ok,
            "manifest": MANIFEST_FILENAME,
            "pinned": {
                "manifest_version": PINNED_MANIFEST_VERSION,
                "artifact_id": PINNED_ARTIFACT_ID,
                "schema_version": PINNED_SCHEMA_VERSION,
                "digest_algorithms": sorted(ADMITTED_DIGEST_ALGORITHMS),
            },
            "reason_codes": self.reason_codes,
            "failures": [failure.as_dict() for failure in self.failures],
            "artifacts": [
                {
                    "path": artifact.path,
                    "declared_size_bytes": artifact.declared_size,
                    "declared_digest": artifact.declared_digest,
                    "observed_size_bytes": artifact.observed_size,
                    "observed_digest": artifact.observed_digest,
                    "stages_passed": list(artifact.stages_passed),
                    "contract": artifact.contract,
                }
                for artifact in self.artifacts
            ],
        }


# ---------------------------------------------------------------------------
# Strict JSON parsing
# ---------------------------------------------------------------------------


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    seen: dict[str, Any] = {}
    for key, value in pairs:
        if key in seen:
            raise ValueError(f"duplicate object key {key!r}")
        seen[key] = value
    return seen


def _reject_constant(name: str) -> Any:
    raise ValueError(f"non-JSON constant {name!r} is not admitted")


def parse_json_strictly(raw: bytes) -> Any:
    """Parse JSON with the latitude removed.

    Python's default parser accepts ``NaN``/``Infinity`` and silently keeps the
    last of duplicate object keys; JavaScript's does neither for the former.
    Both are rejected here so the bytes the JSON Schema sees and the bytes the
    canonical evaluator sees cannot be read two different ways, and so a payload
    cannot smuggle a second value for a field past whichever reader looks first.
    """

    return json.loads(
        raw.decode("utf-8"),
        object_pairs_hook=_reject_duplicate_keys,
        parse_constant=_reject_constant,
    )


def sha256_hex(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _repo_relative(path: Path) -> str:
    """Render a path relative to the repo when it is inside it, else verbatim."""

    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path)


def _load_schema(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _schema_errors(payload: Any, schema: dict[str, Any]) -> list[str]:
    validator = jsonschema.Draft202012Validator(
        schema, format_checker=jsonschema.Draft202012Validator.FORMAT_CHECKER
    )
    errors = sorted(validator.iter_errors(payload), key=lambda error: list(error.absolute_path))
    return [
        f"{'.'.join(str(part) for part in error.absolute_path) or '<root>'}: {error.message}"
        for error in errors
    ]


# ---------------------------------------------------------------------------
# Stage 1-3: the manifest itself
# ---------------------------------------------------------------------------


def read_manifest(bundle_root: Path, failures: list[Failure]) -> bytes | None:
    manifest_path = bundle_root / MANIFEST_FILENAME
    if manifest_path.is_symlink():
        failures.append(
            Failure(
                "manifest_read",
                "BUNDLE_MANIFEST_UNREADABLE",
                MANIFEST_FILENAME,
                "the manifest is a symlink; the gate reads regular files only",
            )
        )
        return None
    if not manifest_path.exists():
        failures.append(
            Failure(
                "manifest_read",
                "BUNDLE_MANIFEST_UNREADABLE",
                MANIFEST_FILENAME,
                f"no {MANIFEST_FILENAME} at the bundle root; the manifest name is pinned in code",
            )
        )
        return None
    if not manifest_path.is_file():
        failures.append(
            Failure(
                "manifest_read",
                "BUNDLE_MANIFEST_UNREADABLE",
                MANIFEST_FILENAME,
                "the manifest is not a regular file",
            )
        )
        return None
    size = manifest_path.stat().st_size
    if size > MANIFEST_MAX_BYTES:
        failures.append(
            Failure(
                "manifest_read",
                "BUNDLE_MANIFEST_UNREADABLE",
                MANIFEST_FILENAME,
                f"manifest is {size} bytes, above the {MANIFEST_MAX_BYTES}-byte cap",
            )
        )
        return None
    try:
        return manifest_path.read_bytes()
    except OSError as error:  # pragma: no cover - environment dependent
        failures.append(
            Failure(
                "manifest_read",
                "BUNDLE_MANIFEST_UNREADABLE",
                MANIFEST_FILENAME,
                f"could not read the manifest: {error}",
            )
        )
        return None


def parse_manifest(raw: bytes, failures: list[Failure]) -> Any:
    try:
        return parse_json_strictly(raw)
    except ValueError as error:
        reason = (
            "BUNDLE_MANIFEST_DUPLICATE_KEY"
            if "duplicate object key" in str(error)
            else "BUNDLE_MANIFEST_JSON_MALFORMED"
        )
        failures.append(
            Failure(
                "manifest_parse",
                reason,
                MANIFEST_FILENAME,
                f"manifest is not strict JSON: {error}",
            )
        )
        return None
    except UnicodeDecodeError as error:
        failures.append(
            Failure(
                "manifest_parse",
                "BUNDLE_MANIFEST_JSON_MALFORMED",
                MANIFEST_FILENAME,
                f"manifest is not valid UTF-8: {error}",
            )
        )
        return None


def check_manifest_shape(manifest: Any, failures: list[Failure]) -> bool:
    """Apply the committed manifest schema, then re-assert the no-authority ban."""

    schema = _load_schema(MANIFEST_SCHEMA_PATH)
    errors = _schema_errors(manifest, schema)
    for message in errors:
        failures.append(
            Failure(
                "manifest_shape",
                "BUNDLE_MANIFEST_SHAPE_INVALID",
                MANIFEST_FILENAME,
                f"manifest does not match the committed manifest schema: {message}",
            )
        )
    if errors:
        return False

    # Defence in depth. The committed schema is closed, so this cannot fire
    # today; it exists so that widening the schema to admit a contract-semantic
    # field is caught here rather than becoming a way for a manifest to speak
    # for a payload.
    intruding = sorted(set(manifest) & FORBIDDEN_MANIFEST_KEYS)
    for key in intruding:
        failures.append(
            Failure(
                "manifest_shape",
                "BUNDLE_MANIFEST_SHAPE_INVALID",
                MANIFEST_FILENAME,
                (
                    f"manifest declares {key!r}; a manifest is integrity metadata and may carry no "
                    "field able to state, relax or waive a contract rule"
                ),
            )
        )
    return not intruding


# ---------------------------------------------------------------------------
# Stage 4: pinned contract identity
# ---------------------------------------------------------------------------


def canonical_contract_constants() -> dict[str, Any]:
    """Ask the canonical contract what it is. Never trusted from the manifest."""

    if not COMPILED_CONTRACT_PATH.exists():
        return {
            "ok": False,
            "error": "compiled_contract_unavailable",
            "detail": (
                f"{_repo_relative(COMPILED_CONTRACT_PATH)} is absent; run 'npm run build' so the "
                "canonical evaluator can be reached"
            ),
        }
    return _run_bridge(["constants"], stdin_bytes=b"")


def check_contract_identity(manifest: dict[str, Any], failures: list[Failure]) -> bool:
    """The manifest may restate the contract identity; it may never define it.

    Two independent things are checked. First the manifest's restatement must
    equal the pins in this file. Second the pins in this file must equal what
    the canonical contract actually reports, so Slice B cannot drift into
    admitting a version Slice A no longer defines.
    """

    ok = True

    canonical = canonical_contract_constants()
    if not canonical.get("ok"):
        failures.append(
            Failure(
                "contract_identity",
                "BUNDLE_SEMANTIC_EVALUATOR_UNAVAILABLE",
                MANIFEST_FILENAME,
                (
                    "the canonical contract could not be reached, so neither the pinned "
                    "identity nor any semantic judgment can be established: "
                    f"{canonical.get('detail')}"
                ),
            )
        )
        ok = False
    else:
        drifted = [
            ("artifact_id", PINNED_ARTIFACT_ID, canonical.get("artifact_id")),
            ("schema_version", PINNED_SCHEMA_VERSION, canonical.get("schema_version")),
        ]
        for name, pinned, actual in drifted:
            if pinned != actual:
                failures.append(
                    Failure(
                        "contract_identity",
                        "BUNDLE_CONTRACT_IDENTITY_DRIFT",
                        MANIFEST_FILENAME,
                        (
                            f"this gate pins {name}={pinned!r} but the canonical contract reports "
                            f"{actual!r}; Slice B must be re-pinned against Slice A rather than "
                            "validating against a version the contract no longer defines"
                        ),
                    )
                )
                ok = False

    expectations = [
        ("manifest_version", PINNED_MANIFEST_VERSION),
        ("artifact_id", PINNED_ARTIFACT_ID),
        ("schema_version", PINNED_SCHEMA_VERSION),
    ]
    for name, pinned in expectations:
        declared = manifest.get(name)
        if declared != pinned:
            failures.append(
                Failure(
                    "contract_identity",
                    "BUNDLE_CONTRACT_IDENTITY_MISMATCH",
                    MANIFEST_FILENAME,
                    (
                        f"manifest declares {name}={declared!r}; the only admitted value is "
                        f"{pinned!r}, which is pinned in code and cannot be redefined by "
                        "manifest data"
                    ),
                )
            )
            ok = False

    algorithm = manifest.get("digest_algorithm")
    if algorithm not in ADMITTED_DIGEST_ALGORITHMS:
        failures.append(
            Failure(
                "contract_identity",
                "BUNDLE_DIGEST_ALGORITHM_UNSUPPORTED",
                MANIFEST_FILENAME,
                (
                    f"manifest declares digest_algorithm={algorithm!r}; the admitted "
                    f"algorithms are {sorted(ADMITTED_DIGEST_ALGORITHMS)} and are pinned in code"
                ),
            )
        )
        ok = False

    return ok


# ---------------------------------------------------------------------------
# Stage 5: path safety and bundle containment
# ---------------------------------------------------------------------------


def _path_shape_failure(raw_path: str) -> tuple[str, str] | None:
    """Return ``(reason_code, detail)`` when a declared path is inadmissible."""

    if "\x00" in raw_path:
        return ("BUNDLE_PATH_NOT_NORMALIZED", "path contains a NUL byte")
    if "\\" in raw_path:
        return (
            "BUNDLE_PATH_NOT_NORMALIZED",
            "path contains a backslash; bundle paths are POSIX relative paths",
        )
    if raw_path.startswith("/"):
        return ("BUNDLE_PATH_NOT_RELATIVE", "path is absolute")
    if len(raw_path) >= 2 and raw_path[1] == ":" and raw_path[0].isalpha():
        return ("BUNDLE_PATH_NOT_RELATIVE", "path is drive-qualified")
    if raw_path.endswith("/"):
        return ("BUNDLE_PATH_NOT_NORMALIZED", "path names a directory, not a file")

    segments = raw_path.split("/")
    for segment in segments:
        if segment == "":
            return ("BUNDLE_PATH_NOT_NORMALIZED", "path contains an empty segment")
        if segment == ".":
            return ("BUNDLE_PATH_NOT_NORMALIZED", "path contains a '.' segment")
        if segment == "..":
            return ("BUNDLE_PATH_TRAVERSAL", "path contains a '..' segment")
    if raw_path == MANIFEST_FILENAME:
        return (
            "BUNDLE_MANIFEST_DECLARES_ITSELF",
            "the manifest declares itself as a bundle artifact; it describes the bundle "
            "and is not part of it",
        )
    return None


def check_path_safety(
    bundle_root: Path, artifacts: list[ArtifactState], failures: list[Failure]
) -> None:
    """Reject anything that is not a plain, contained, regular file.

    Symlinks are rejected at every component, not only at the leaf: a symlinked
    parent directory is just as good an escape as a symlinked file, and a digest
    computed through one describes bytes that live outside the bundle.
    """

    real_root = Path(os.path.realpath(bundle_root))
    for artifact in artifacts:
        shape_failure = _path_shape_failure(artifact.path)
        if shape_failure is not None:
            reason, detail = shape_failure
            failures.append(Failure("path_safety", reason, artifact.path, detail))
            artifact.block()
            continue

        absolute = bundle_root / PurePosixPath(artifact.path)

        escaped = False
        walked = bundle_root
        for segment in PurePosixPath(artifact.path).parts:
            walked = walked / segment
            if walked.is_symlink():
                failures.append(
                    Failure(
                        "path_safety",
                        "BUNDLE_PATH_NOT_REGULAR_FILE",
                        artifact.path,
                        (
                            f"path component {segment!r} is a symlink; the gate follows no "
                            "link, because a link's target is not bundle content"
                        ),
                    )
                )
                artifact.block()
                escaped = True
                break
        if escaped:
            continue

        if not absolute.exists():
            failures.append(
                Failure(
                    "path_safety",
                    "BUNDLE_ARTIFACT_MISSING",
                    artifact.path,
                    "the manifest declares this artifact but the bundle does not contain it",
                )
            )
            artifact.block()
            continue

        if not absolute.is_file():
            failures.append(
                Failure(
                    "path_safety",
                    "BUNDLE_PATH_NOT_REGULAR_FILE",
                    artifact.path,
                    "the declared path is not a regular file",
                )
            )
            artifact.block()
            continue

        real_target = Path(os.path.realpath(absolute))
        if real_root != real_target and real_root not in real_target.parents:
            failures.append(
                Failure(
                    "path_safety",
                    "BUNDLE_PATH_ESCAPES_ROOT",
                    artifact.path,
                    "the declared path resolves outside the bundle root",
                )
            )
            artifact.block()
            continue

        artifact.absolute = absolute
        artifact.passed("path_safety")


# ---------------------------------------------------------------------------
# Stage 6: exact manifest <-> bundle bijection
# ---------------------------------------------------------------------------


def _walk_bundle(bundle_root: Path) -> tuple[list[str], list[str]]:
    """Return ``(regular_files, irregular_entries)`` as bundle-relative paths."""

    regular: list[str] = []
    irregular: list[str] = []
    for current_root, directory_names, file_names in os.walk(bundle_root, followlinks=False):
        current = Path(current_root)
        for name in sorted(directory_names):
            entry = current / name
            if entry.is_symlink():
                irregular.append(entry.relative_to(bundle_root).as_posix())
        for name in sorted(file_names):
            entry = current / name
            relative = entry.relative_to(bundle_root).as_posix()
            if relative == MANIFEST_FILENAME:
                continue
            if entry.is_symlink() or not entry.is_file():
                irregular.append(relative)
            else:
                regular.append(relative)
    return sorted(regular), sorted(irregular)


def check_bundle_bijection(
    bundle_root: Path, artifacts: list[ArtifactState], failures: list[Failure]
) -> None:
    """The manifest must describe the bundle exactly: no more, no less, no twice.

    Without this, an attacker adds a file the manifest never mentions and the
    per-entry digest checks all still pass.
    """

    seen: dict[str, int] = {}
    for artifact in artifacts:
        seen[artifact.path] = seen.get(artifact.path, 0) + 1
    for path, count in sorted(seen.items()):
        if count > 1:
            failures.append(
                Failure(
                    "bundle_bijection",
                    "BUNDLE_DUPLICATE_MANIFEST_ENTRY",
                    path,
                    f"the manifest declares this path {count} times; each artifact is "
                    "declared exactly once",
                )
            )
            for artifact in artifacts:
                if artifact.path == path:
                    artifact.block()

    regular, irregular = _walk_bundle(bundle_root)

    for path in irregular:
        failures.append(
            Failure(
                "bundle_bijection",
                "BUNDLE_PATH_NOT_REGULAR_FILE",
                path,
                "the bundle contains a symlink or non-regular entry; a bundle holds "
                "regular files only",
            )
        )

    declared = set(seen)
    for path in sorted(set(regular) - declared):
        failures.append(
            Failure(
                "bundle_bijection",
                "BUNDLE_UNDECLARED_FILE",
                path,
                "the bundle contains a file the manifest does not declare",
            )
        )

    # A path declared but absent is reported once, by path_safety.
    for artifact in artifacts:
        if artifact.blocked or artifact.absolute is None:
            continue
        artifact.passed("bundle_bijection")


# ---------------------------------------------------------------------------
# Stage 7: size and digest, before anything is parsed
# ---------------------------------------------------------------------------


def check_integrity(
    manifest: dict[str, Any], artifacts: list[ArtifactState], failures: list[Failure]
) -> None:
    """Verify byte length and digest of the exact bytes on disk.

    Size is checked first and from ``stat``, so an oversized or wrong-length
    file is rejected without reading it. The digest is then computed over the
    bytes actually read, and those same bytes -- not a re-read of the path --
    are what later stages parse and evaluate.
    """

    algorithm = manifest.get("digest_algorithm")
    expected_hex_length = DIGEST_HEX_LENGTHS.get(algorithm if isinstance(algorithm, str) else "")

    for artifact in artifacts:
        if artifact.blocked or artifact.absolute is None:
            continue

        digest = artifact.declared_digest
        if expected_hex_length is not None and len(digest) != expected_hex_length:
            failures.append(
                Failure(
                    "integrity",
                    "BUNDLE_DIGEST_VALUE_MALFORMED",
                    artifact.path,
                    (
                        f"declared digest is {len(digest)} hex characters; {algorithm} digests are "
                        f"{expected_hex_length}"
                    ),
                )
            )
            artifact.block()
            continue

        if artifact.declared_size > ARTIFACT_MAX_BYTES:
            failures.append(
                Failure(
                    "integrity",
                    "BUNDLE_ARTIFACT_TOO_LARGE",
                    artifact.path,
                    (
                        f"declared size {artifact.declared_size} exceeds the "
                        f"{ARTIFACT_MAX_BYTES}-byte cap; the gate will not read it"
                    ),
                )
            )
            artifact.block()
            continue

        try:
            observed_size = artifact.absolute.stat().st_size
        except OSError as error:
            failures.append(
                Failure(
                    "integrity",
                    "BUNDLE_ARTIFACT_MISSING",
                    artifact.path,
                    f"the declared artifact became unreadable during validation: {error}",
                )
            )
            artifact.block()
            continue
        artifact.observed_size = observed_size
        if observed_size != artifact.declared_size:
            failures.append(
                Failure(
                    "integrity",
                    "BUNDLE_SIZE_MISMATCH",
                    artifact.path,
                    f"manifest declares {artifact.declared_size} bytes; the file is "
                    f"{observed_size} bytes",
                )
            )
            artifact.block()
            continue

        if observed_size > ARTIFACT_MAX_BYTES:  # pragma: no cover - unreachable via declared size
            failures.append(
                Failure(
                    "integrity",
                    "BUNDLE_ARTIFACT_TOO_LARGE",
                    artifact.path,
                    f"file is {observed_size} bytes, above the {ARTIFACT_MAX_BYTES}-byte cap",
                )
            )
            artifact.block()
            continue

        try:
            raw = artifact.absolute.read_bytes()
        except OSError as error:
            failures.append(
                Failure(
                    "integrity",
                    "BUNDLE_ARTIFACT_MISSING",
                    artifact.path,
                    f"the declared artifact became unreadable during validation: {error}",
                )
            )
            artifact.block()
            continue
        observed_digest = sha256_hex(raw)
        artifact.observed_digest = observed_digest
        if observed_digest != digest:
            failures.append(
                Failure(
                    "integrity",
                    "BUNDLE_DIGEST_MISMATCH",
                    artifact.path,
                    (
                        f"manifest declares {algorithm}={digest}; the file's bytes hash to "
                        f"{observed_digest}"
                    ),
                )
            )
            artifact.block()
            continue

        artifact.raw_bytes = raw  # verified bytes; parsed in the next stage
        artifact.passed("integrity")


# ---------------------------------------------------------------------------
# Stage 8-9: strict parse, then the committed JSON Schema shape gate
# ---------------------------------------------------------------------------


def parse_payloads(artifacts: list[ArtifactState], failures: list[Failure]) -> None:
    for artifact in artifacts:
        if artifact.blocked or artifact.raw_bytes is None:
            continue
        try:
            artifact.payload = parse_json_strictly(artifact.raw_bytes)
        except ValueError as error:
            reason = (
                "BUNDLE_ARTIFACT_DUPLICATE_KEY"
                if "duplicate object key" in str(error)
                else "BUNDLE_ARTIFACT_JSON_MALFORMED"
            )
            failures.append(
                Failure(
                    "payload_parse",
                    reason,
                    artifact.path,
                    (
                        "the declared bytes are not strict JSON, and a matching size and "
                        f"digest do not make them parseable: {error}"
                    ),
                )
            )
            artifact.block()
            continue
        except UnicodeDecodeError as error:
            failures.append(
                Failure(
                    "payload_parse",
                    "BUNDLE_ARTIFACT_JSON_MALFORMED",
                    artifact.path,
                    f"the declared bytes are not valid UTF-8: {error}",
                )
            )
            artifact.block()
            continue
        artifact.passed("payload_parse")


def check_payload_schema(artifacts: list[ArtifactState], failures: list[Failure]) -> None:
    """Apply the committed rb_contact_evasion_observations_v0 JSON Schema.

    The schema file is Slice A's committed shape authority. It is applied here,
    not re-expressed: this gate holds no copy of the shape rules.
    """

    schema = _load_schema(ARTIFACT_SCHEMA_PATH)
    for artifact in artifacts:
        if artifact.blocked or artifact.payload is UNPARSED:
            continue
        errors = _schema_errors(artifact.payload, schema)
        for message in errors:
            failures.append(
                Failure(
                    "payload_shape",
                    "BUNDLE_ARTIFACT_SCHEMA_INVALID",
                    artifact.path,
                    f"payload does not match the committed contract schema: {message}",
                )
            )
        if errors:
            artifact.block()
            continue
        artifact.passed("payload_shape")


# ---------------------------------------------------------------------------
# Stage 10: the manifest must agree with the payload, never override it
# ---------------------------------------------------------------------------


def check_manifest_payload_agreement(
    manifest: dict[str, Any], artifacts: list[ArtifactState], failures: list[Failure]
) -> None:
    """Exact agreement, in the direction that cannot launder a payload.

    The payload's own declarations are what the contract layer judges. The
    manifest restates three of them, and any disagreement is a failure -- so a
    manifest cannot describe a candidate as a fixture to duck the rules a
    candidate faces, nor describe a fixture as a candidate to look governed.
    """

    for artifact in artifacts:
        if artifact.blocked or not isinstance(artifact.payload, dict):
            continue
        for key in ("artifact_id", "schema_version", "artifact_position"):
            declared = manifest.get(key)
            actual = artifact.payload.get(key)
            if declared != actual:
                failures.append(
                    Failure(
                        "manifest_payload_agreement",
                        "BUNDLE_MANIFEST_PAYLOAD_DISAGREEMENT",
                        artifact.path,
                        (
                            f"manifest declares {key}={declared!r} but the payload declares "
                            f"{actual!r}; the manifest describes the payload and never "
                            "redefines it"
                        ),
                    )
                )
                artifact.block()
        if not artifact.blocked:
            artifact.passed("manifest_payload_agreement")


# ---------------------------------------------------------------------------
# Stage 11: delegate every semantic judgment to the canonical evaluator
# ---------------------------------------------------------------------------


def _run_bridge(args: list[str], stdin_bytes: bytes) -> dict[str, Any]:
    """Invoke the Node bridge with a minimal environment and no network use."""

    if not BRIDGE_PATH.exists():
        return {
            "ok": False,
            "error": "bridge_missing",
            "detail": f"{_repo_relative(BRIDGE_PATH)} is absent",
        }
    try:
        completed = subprocess.run(  # noqa: S603 - fixed argv, no shell
            ["node", str(BRIDGE_PATH), *args],
            input=stdin_bytes,
            capture_output=True,
            timeout=BRIDGE_TIMEOUT_SECONDS,
            cwd=str(REPO_ROOT),
            env={"PATH": os.environ.get("PATH", "")},
            check=False,
        )
    except FileNotFoundError:
        return {
            "ok": False,
            "error": "node_unavailable",
            "detail": "the 'node' executable is not on PATH",
        }
    except subprocess.TimeoutExpired:
        return {
            "ok": False,
            "error": "bridge_timeout",
            "detail": f"the bridge did not answer within {BRIDGE_TIMEOUT_SECONDS}s",
        }

    stdout = completed.stdout.decode("utf-8", errors="replace").strip()
    if not stdout:
        return {
            "ok": False,
            "error": "bridge_silent",
            "detail": (
                f"the bridge exited {completed.returncode} with no output: "
                f"{completed.stderr.decode('utf-8', errors='replace').strip()[:400]}"
            ),
        }
    try:
        payload = json.loads(stdout.splitlines()[-1])
    except ValueError as error:
        return {"ok": False, "error": "bridge_unreadable", "detail": f"{error}"}
    if not isinstance(payload, dict):
        return {
            "ok": False,
            "error": "bridge_unreadable",
            "detail": "bridge did not answer with an object",
        }
    return payload


def evaluate_semantics(artifacts: list[ArtifactState], failures: list[Failure]) -> None:
    """Hand the verified bytes to Slice A and reproduce its verdict verbatim.

    No reason code is invented, renamed, filtered or ranked here. The evaluator's
    own ``reason_codes`` are what a consumer reads, so a downstream CI check sees
    exactly the codes Slice A's tests pin.
    """

    for artifact in artifacts:
        if artifact.blocked or artifact.payload is UNPARSED:
            continue

        # Re-serialising the parsed payload would let this gate's serializer
        # decide what the evaluator sees. The verified bytes are sent instead.
        if artifact.absolute is None:
            failures.append(
                Failure(
                    "semantic",
                    "BUNDLE_SEMANTIC_EVALUATOR_FAILED",
                    artifact.path,
                    "no verified path reached the semantic stage; refusing to evaluate",
                )
            )
            artifact.block()
            continue

        try:
            raw = artifact.absolute.read_bytes()
        except OSError as error:
            failures.append(
                Failure(
                    "semantic",
                    "BUNDLE_DIGEST_MISMATCH",
                    artifact.path,
                    f"the artifact became unreadable between verification and evaluation: {error}",
                )
            )
            artifact.block()
            continue

        if sha256_hex(raw) != artifact.declared_digest:
            failures.append(
                Failure(
                    "semantic",
                    "BUNDLE_DIGEST_MISMATCH",
                    artifact.path,
                    "the file changed between integrity verification and semantic evaluation",
                )
            )
            artifact.block()
            continue

        answer = _run_bridge(["evaluate"], stdin_bytes=raw)
        if not answer.get("ok"):
            error = answer.get("error")
            reason = (
                "BUNDLE_SEMANTIC_EVALUATOR_UNAVAILABLE"
                if error in {"compiled_contract_unavailable", "node_unavailable", "bridge_missing"}
                else "BUNDLE_SEMANTIC_EVALUATOR_FAILED"
            )
            failures.append(
                Failure(
                    "semantic",
                    reason,
                    artifact.path,
                    (
                        "the canonical evaluator did not return a verdict, so this bundle is not "
                        f"validated: {error}: {answer.get('detail')}"
                    ),
                )
            )
            artifact.block()
            continue

        report = answer.get("report")
        if not isinstance(report, dict) or "valid" not in report:
            failures.append(
                Failure(
                    "semantic",
                    "BUNDLE_SEMANTIC_EVALUATOR_FAILED",
                    artifact.path,
                    "the canonical evaluator returned an unreadable report",
                )
            )
            artifact.block()
            continue

        artifact.contract = {
            "valid": bool(report.get("valid")),
            "shape_valid": bool(report.get("shape_valid")),
            "reason_codes": list(report.get("reason_codes") or []),
        }

        if not report.get("valid"):
            for violation in report.get("violations") or []:
                failures.append(
                    Failure(
                        "semantic",
                        str(violation.get("reason_code")),
                        artifact.path,
                        f"{violation.get('path')}: {violation.get('detail')}",
                    )
                )
            artifact.block()
            continue

        artifact.passed("semantic")


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def validate_bundle(bundle_root: Path) -> GateResult:
    """Run every stage in order, fail-closed, over one bundle directory."""

    failures: list[Failure] = []
    artifacts: list[ArtifactState] = []

    if not bundle_root.exists() or not bundle_root.is_dir() or bundle_root.is_symlink():
        failures.append(
            Failure(
                "manifest_read",
                "BUNDLE_ROOT_INVALID",
                ".",
                f"{bundle_root} is not a real directory; a bundle root is a plain directory",
            )
        )
        return GateResult(ok=False, failures=failures, artifacts=artifacts)

    raw_manifest = read_manifest(bundle_root, failures)
    if raw_manifest is None:
        return GateResult(
            ok=False, failures=sorted(failures, key=Failure.sort_key), artifacts=artifacts
        )

    manifest = parse_manifest(raw_manifest, failures)
    if manifest is None:
        return GateResult(
            ok=False, failures=sorted(failures, key=Failure.sort_key), artifacts=artifacts
        )

    if not check_manifest_shape(manifest, failures):
        return GateResult(
            ok=False, failures=sorted(failures, key=Failure.sort_key), artifacts=artifacts
        )

    identity_ok = check_contract_identity(manifest, failures)

    for entry in manifest["artifacts"]:
        artifacts.append(
            ArtifactState(
                path=entry["path"],
                declared_size=entry["size_bytes"],
                declared_digest=entry["digest"],
            )
        )
    artifacts.sort(key=lambda artifact: artifact.path)

    check_path_safety(bundle_root, artifacts, failures)
    check_bundle_bijection(bundle_root, artifacts, failures)
    check_integrity(manifest, artifacts, failures)
    parse_payloads(artifacts, failures)
    check_payload_schema(artifacts, failures)
    check_manifest_payload_agreement(manifest, artifacts, failures)

    # A failed identity check means the pinned contract could not be
    # established. Evaluating anyway would produce a verdict from an
    # unestablished authority, so the semantic stage does not run.
    if identity_ok:
        evaluate_semantics(artifacts, failures)
    else:
        for artifact in artifacts:
            artifact.block()

    return GateResult(
        ok=not failures,
        failures=sorted(failures, key=Failure.sort_key),
        artifacts=artifacts,
    )


def render_human_report(bundle_root: Path, result: GateResult) -> str:
    """Deterministic human-readable diagnostics."""

    lines = [
        f"{GATE_ID}",
        f"bundle root: {bundle_root}",
        f"manifest:    {MANIFEST_FILENAME}",
        f"pinned:      {PINNED_ARTIFACT_ID} / {PINNED_SCHEMA_VERSION} / "
        f"{'|'.join(sorted(ADMITTED_DIGEST_ALGORITHMS))}",
        "",
    ]
    if result.artifacts:
        lines.append("artifacts:")
        for artifact in result.artifacts:
            stages = ", ".join(artifact.stages_passed) if artifact.stages_passed else "none"
            lines.append(f"  {artifact.path}")
            lines.append(f"    stages passed: {stages}")
            if artifact.contract is not None:
                codes = ", ".join(artifact.contract["reason_codes"]) or "none"
                lines.append(
                    f"    contract: valid={artifact.contract['valid']} "
                    f"shape_valid={artifact.contract['shape_valid']} reason_codes: {codes}"
                )
        lines.append("")

    if result.ok:
        lines.append("RESULT: PASS - every declared artifact cleared every stage.")
    else:
        lines.append(f"RESULT: FAIL - {len(result.failures)} finding(s).")
        lines.append("")
        for failure in result.failures:
            lines.append(f"  [{failure.stage}] {failure.reason_code}  ({failure.path})")
            lines.append(f"      {failure.detail}")
        lines.append("")
        lines.append(f"reason codes: {', '.join(result.reason_codes)}")
    return "\n".join(lines)


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Fail-closed manifest/digest gate for rb_contact_evasion_observations_v0 candidate "
            "bundles. Semantic judgment is delegated to the canonical Slice A evaluator."
        )
    )
    parser.add_argument(
        "bundle_root", type=Path, help="directory holding manifest.json and its artifacts"
    )
    parser.add_argument(
        "--json", action="store_true", help="print only the machine-readable result to stdout"
    )
    parser.add_argument(
        "--json-out", type=Path, default=None, help="also write the machine-readable result here"
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    bundle_root = args.bundle_root

    if args.json_out is not None:
        try:
            root_real = Path(os.path.realpath(bundle_root))
            out_real = Path(os.path.realpath(args.json_out))
        except OSError as error:  # pragma: no cover - environment dependent
            raise GateUsageError(f"could not resolve --json-out: {error}") from error
        if root_real == out_real or root_real in out_real.parents:
            raise GateUsageError(
                "--json-out points inside the bundle; the gate never writes into what it validates"
            )

    result = validate_bundle(bundle_root)
    machine = json.dumps(result.as_dict(), indent=2, sort_keys=True) + "\n"

    if args.json_out is not None:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(machine, encoding="utf-8")

    if args.json:
        sys.stdout.write(machine)
    else:
        sys.stdout.write(render_human_report(bundle_root, result) + "\n")

    return 0 if result.ok else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except GateUsageError as usage_error:
        sys.stderr.write(f"usage error: {usage_error}\n")
        raise SystemExit(2) from usage_error

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

Evaluator identity
------------------
The gate never trusts a pre-existing compiled build. ``dist/`` is gitignored, so
a stale, substituted or permissive module could sit there exporting the correct
artifact id and schema version while returning ``valid: true`` for everything --
self-reported constants prove nothing about what the code does.

So identity is established by **construction**: on first use the gate compiles
the reviewed TypeScript contract itself, with the repository's own ``tsc`` and a
committed tsconfig naming exactly one entry point, into a private temporary
directory this process owns. It then hands the bridge the path of what it just
built together with the sha256 of those exact bytes, and the bridge refuses to
import anything that does not hash to it. Nothing under ``dist/`` is read at any
point.

The receipt of that build -- the fingerprint of every repo-local source file the
compiler actually read, the digest of the emitted module, and the dependency
pins -- is reported in the machine-readable result, so a reviewer can confirm
which source produced a verdict. See ``build_evaluator`` for exactly what is
hashed.

What this gate does own
-----------------------
Everything that has to be true *before* a payload claim can be trusted:

1. the manifest is readable, parses, and matches the committed manifest schema;
2. the declared contract identity equals the identity pinned **in this file**,
   which is itself cross-checked against a contract compiled from reviewed
   source;
3. every declared path is relative, contained, and a real regular file;
4. the manifest and the bundle are in exact bijection;
5. byte size and SHA-256 are verified **before** any parse or evaluation;
6. the payload parses strictly (a matching digest never excuses malformed JSON);
7. the committed JSON Schema shape gate is applied;
8. the manifest agrees with the payload it describes, and can never weaken it;
9. the canonical evaluator judges the exact verified bytes, and returns a
   structurally well-formed, internally consistent verdict.

Stages run in that order and the result is fail-closed at every one: a stage
that cannot run is a failure, never a skip. The gate performs no network access
and opens every path read-only, so it never mutates what it validates.

Usage::

    python3 scripts/validate_rb_contact_evasion_bundle.py <bundle-root>
    python3 scripts/validate_rb_contact_evasion_bundle.py <bundle-root> --json

``--json-out`` is intentionally disabled. Machine-readable output is emitted
only to stdout so this validation gate never owns a write capability.

Exit codes: ``0`` the bundle passed, ``1`` the bundle failed the gate, ``2`` the
invocation itself was invalid.

The semantic stage compiles the contract on demand and therefore needs ``node``
and the repository's dev dependencies installed. If the build cannot be produced
the gate fails closed rather than reporting a pass it could not establish.
"""

from __future__ import annotations

import argparse
import errno
import hashlib
import json
import os
import stat
import subprocess
import sys
import tempfile
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

# The build surface. The tsconfig names exactly one entry point -- the module
# that defines the canonical evaluator -- so the compiler resolves the true
# transitive source surface rather than this file guessing at it.
EVALUATOR_TSCONFIG_PATH = REPO_ROOT / "scripts/rb_contact_evasion_evaluator.tsconfig.json"
EVALUATOR_ENTRY_SOURCE = "src/contracts/v1/rbContactEvasionObservationsV0.ts"
EVALUATOR_ENTRY_OUTPUT = "src/contracts/v1/rbContactEvasionObservationsV0.js"

# Hashed alongside the compiled sources: the two tsconfigs decide how the source
# is compiled, and the package manifests pin the one runtime dependency the
# evaluator imports.
EVALUATOR_FINGERPRINT_EXTRA_PATHS = (
    "tsconfig.json",
    "scripts/rb_contact_evasion_evaluator.tsconfig.json",
    "package.json",
    "package-lock.json",
)
EVALUATOR_RUNTIME_DEPENDENCY = "zod"

# The compiler is the repository-local, lock-governed TypeScript, invoked as
# `node <this file>` so PATH is never consulted -- a poisoned `npx`/`tsc` earlier
# on PATH can never be executed, and no package acquisition is ever attempted.
EVALUATOR_TS_COMPILER = REPO_ROOT / "node_modules/typescript/bin/tsc"
EVALUATOR_TS_PACKAGE_JSON = REPO_ROOT / "node_modules/typescript/package.json"
EVALUATOR_LOCKFILE = REPO_ROOT / "package-lock.json"
# The entry source, relative form, as tsc reports it.
EVALUATOR_ENTRY_SOURCE_ABS = (REPO_ROOT / EVALUATOR_ENTRY_SOURCE).as_posix()

# Bounded reads. A declared size above the cap is rejected before anything is
# read, so a hostile manifest cannot ask the gate to load an arbitrary file.
MANIFEST_MAX_BYTES = 1_048_576
ARTIFACT_MAX_BYTES = 67_108_864
BRIDGE_TIMEOUT_SECONDS = 120
EVALUATOR_BUILD_TIMEOUT_SECONDS = 600

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
    # Both hold the SAME immutable ``bytes`` object once integrity freezes it, so
    # the digest-authorized subject cannot be mutated in place before evaluation.
    raw_bytes: bytes | None = None
    verified_bytes: bytes | None = None
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
    # Receipt of the build that produced the verdict, so a reviewer can confirm
    # which source the semantic stage actually ran. None when no build was made.
    evaluator: dict[str, Any] | None = None

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
            "evaluator": self.evaluator,
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


# ---------------------------------------------------------------------------
# Descriptor-bound file reads
# ---------------------------------------------------------------------------
# Every file the gate reads out of a bundle -- the manifest and each declared
# artifact -- is read through ONE descriptor whose type and size are validated
# with fstat() on that same descriptor, then read with a bounded read from it.
# The gate never does a pathname stat() followed by a separate pathname read:
# that is a time-of-check/time-of-use race in which the entry can be swapped for
# an oversized file, a FIFO, a device, or a symlink between the two operations.
# Instead, each path component is opened descriptor-relatively with O_NOFOLLOW,
# so a symlink at any component (final or intermediate) is refused atomically;
# the leaf is opened O_NONBLOCK so a FIFO cannot make the open hang; fstat on the
# descriptor requires a regular file; the cap is enforced against that
# descriptor; and the bounded read reads at most cap + 1 bytes in total (peak
# reader ownership is one growing buffer plus one bounded read chunk and
# allocation headroom), so an oversized replacement or post-fstat growth is
# detected without unbounded memory. The bytes returned are the exact bytes
# those checks bound.


class _ReadOutcome:
    OK = "ok"
    MISSING = "missing"
    SYMLINK = "symlink"
    NOT_REGULAR = "not_regular"
    TOO_LARGE = "too_large"
    UNREADABLE = "unreadable"
    UNSUPPORTED = "unsupported"


_O_CLOEXEC = getattr(os, "O_CLOEXEC", 0)
_O_NOFOLLOW = getattr(os, "O_NOFOLLOW", 0)
_O_DIRECTORY = getattr(os, "O_DIRECTORY", 0)
_O_NONBLOCK = getattr(os, "O_NONBLOCK", 0)
_O_PATH = getattr(os, "O_PATH", 0)
_READ_CHUNK = 1 << 20


def descriptor_primitives_available() -> bool:
    """Whether the platform can prove no-follow, component-relative access.

    The descriptor-bound read requires ``O_NOFOLLOW`` and ``O_PATH`` (to open an
    inode without following a link and without I/O), ``O_NONBLOCK`` (so a FIFO
    leaf cannot hang the open), and ``dir_fd`` support on ``os.open`` (to walk
    components relative to an already-opened directory). If any is missing the
    gate cannot prove safe access and MUST fail closed rather than fall back to a
    full-path open, which would follow a symlink to bytes outside the bundle.
    """

    return bool(
        _O_NOFOLLOW
        and _O_PATH
        and _O_NONBLOCK
        and os.open in getattr(os, "supports_dir_fd", set())
    )


def _read_fd_capped(fd: int, cap: int) -> tuple[bytearray, bool]:
    """Read at most ``cap + 1`` bytes from ``fd`` into ONE growing buffer.

    Within this reader, peak payload ownership is a single ``bytearray`` of at
    most ``cap + 1`` bytes, plus one small reusable read chunk -- there is never
    a second payload-sized representation here (the old chunk-list-then-``join``
    held both the list and the joined result, peaking at roughly twice the
    payload). This "no whole-payload copy" property is scoped to the read: the
    reader returns the ``bytearray`` without copying it. It is NOT a
    whole-lifecycle claim -- once the digest matches, ``check_integrity``
    deliberately freezes these bytes into an immutable ``bytes`` object (one
    per-artifact copy, made once) so no later stage can mutate the
    digest-authorized subject. See ``check_integrity`` and the contract doc for
    that honest per-stage accounting.

    Reads at most ``cap + 1`` bytes total, so an arbitrarily large file cannot
    exhaust memory. The second value is "grew past cap": if the descriptor
    yields more than ``cap`` bytes the buffer is dropped and
    ``(bytearray(), True)`` is returned. Post-``fstat`` growth and short reads
    are both detected -- growth trips the ``cap + 1`` limit, a short read simply
    yields fewer bytes for the caller's size/digest checks to reject.
    """

    limit = cap + 1
    buf = bytearray()
    while len(buf) < limit:
        try:
            chunk = os.read(fd, min(_READ_CHUNK, limit - len(buf)))
        except BlockingIOError:  # pragma: no cover - regular files do not block
            break
        if not chunk:
            break
        buf += chunk  # `chunk` is at most _READ_CHUNK bytes and freed next iteration
    if len(buf) > cap:
        buf.clear()
        return bytearray(), True
    return buf, False


def read_bundle_file(
    bundle_root: Path, relative_posix: str, cap: int
) -> tuple[bytearray | None, tuple[str, str]]:
    """Open a bundle-relative path safely and return its bytes, or an outcome.

    Walks each path component descriptor-relatively with ``O_NOFOLLOW`` (refusing
    a symlink at any level), opens the leaf ``O_NONBLOCK`` (so a FIFO cannot
    hang), requires a regular file by ``fstat`` on the opened descriptor, caps by
    that descriptor's size, and reads at most ``cap + 1`` bytes from it. Returns
    ``(bytes-like, ("ok", ""))`` on success or ``(None, (outcome, detail))``.

    If the platform cannot provide the primitives required to prove no-follow,
    component-relative access, the read **fails closed** with ``UNSUPPORTED``
    before opening anything -- it never degrades to a full-path open, which would
    follow a symlink to bytes outside the bundle.
    """

    segments = [segment for segment in relative_posix.split("/") if segment]
    if not segments:
        return None, (_ReadOutcome.UNREADABLE, "empty relative path")

    if not descriptor_primitives_available():
        return None, (
            _ReadOutcome.UNSUPPORTED,
            "the platform lacks the descriptor primitives (O_NOFOLLOW, O_PATH, "
            "O_NONBLOCK, dir_fd) required to prove no-follow component-relative "
            "access; the gate fails closed rather than reading bundle bytes",
        )

    open_flags = os.O_RDONLY | _O_CLOEXEC
    fds: list[int] = []

    def _classify(error: OSError, what: str) -> tuple[None, tuple[str, str]]:
        if error.errno == errno.ELOOP:
            return None, (_ReadOutcome.SYMLINK, f"{what} is a symlink; the gate follows no link")
        if error.errno == errno.ENOENT:
            return None, (_ReadOutcome.MISSING, f"{what} is absent")
        if error.errno == errno.ENOTDIR:
            return None, (_ReadOutcome.NOT_REGULAR, f"{what} is not a directory")
        return None, (_ReadOutcome.UNREADABLE, f"could not open {what}: {error}")

    try:
        # Intermediate components are opened O_PATH|O_NOFOLLOW: this resolves the
        # inode without I/O (so a FIFO or device can never block) and without
        # following a link (a symlink opens AS a symlink, detected by fstat),
        # then each must be a real directory. Deterministic across kernels,
        # unlike relying on ELOOP vs ENOTDIR from O_DIRECTORY. There is no
        # full-path fallback: without these primitives the read already returned
        # UNSUPPORTED above.
        try:
            current = os.open(bundle_root, open_flags | _O_PATH | _O_NOFOLLOW)
        except OSError as error:
            return _classify(error, "the bundle root")
        fds.append(current)
        for segment in segments[:-1]:
            try:
                nxt = os.open(segment, open_flags | _O_PATH | _O_NOFOLLOW, dir_fd=current)
            except OSError as error:
                return _classify(error, f"path component {segment!r}")
            fds.append(nxt)
            mode = os.fstat(nxt).st_mode
            if stat.S_ISLNK(mode):
                return None, (
                    _ReadOutcome.SYMLINK,
                    f"path component {segment!r} is a symlink; the gate follows no link",
                )
            if not stat.S_ISDIR(mode):
                return None, (
                    _ReadOutcome.NOT_REGULAR,
                    f"path component {segment!r} is not a directory",
                )
            current = nxt
        try:
            leaf_fd = os.open(
                segments[-1], open_flags | _O_NOFOLLOW | _O_NONBLOCK, dir_fd=current
            )
        except OSError as error:
            return _classify(error, "the artifact")
        fds.append(leaf_fd)

        st = os.fstat(leaf_fd)
        if not stat.S_ISREG(st.st_mode):
            return None, (
                _ReadOutcome.NOT_REGULAR,
                "the opened descriptor is not a regular file (a FIFO, device, "
                "socket, or directory is refused without reading it)",
            )
        if st.st_size > cap:
            return None, (
                _ReadOutcome.TOO_LARGE,
                f"the file is {st.st_size} bytes, above the {cap}-byte cap; it is not read",
            )
        data, grew = _read_fd_capped(leaf_fd, cap)
        if grew:
            return None, (
                _ReadOutcome.TOO_LARGE,
                f"the file grew past the {cap}-byte cap while being read",
            )
        return data, (_ReadOutcome.OK, "")
    finally:
        for fd in reversed(fds):
            try:
                os.close(fd)
            except OSError:  # pragma: no cover - best-effort close
                pass


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
    """Read the manifest through one O_NOFOLLOW descriptor, bounded and typed.

    A symlink, FIFO, device, directory, oversized replacement, or growth during
    reading all fail closed as ``BUNDLE_MANIFEST_UNREADABLE`` without a pathname
    stat-then-reopen and without an unbounded read.
    """

    data, (outcome, detail) = read_bundle_file(bundle_root, MANIFEST_FILENAME, MANIFEST_MAX_BYTES)
    if outcome != _ReadOutcome.OK:
        failures.append(
            Failure("manifest_read", "BUNDLE_MANIFEST_UNREADABLE", MANIFEST_FILENAME, detail)
        )
        return None
    return data


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
# Evaluator identity: compiled from reviewed source, never trusted from disk
# ---------------------------------------------------------------------------


@dataclass
class EvaluatorBuild:
    """A compiled evaluator plus the receipt of what produced it."""

    module_path: Path
    module_digest: str
    source_fingerprint: str
    source_files: tuple[tuple[str, str], ...]
    dependency_pins: tuple[tuple[str, str], ...]
    # Keeps a caller-supplied build's temporary directory alive for as long as
    # the build object itself is referenced.
    retained_dir: Any = None

    def receipt(self) -> dict[str, Any]:
        """Repo-relative, clock-free, so two runs over one source agree exactly."""

        return {
            "entry_source": EVALUATOR_ENTRY_SOURCE,
            "source_fingerprint": self.source_fingerprint,
            "module_digest": self.module_digest,
            "source_files": [
                {"path": path, "sha256": digest} for path, digest in self.source_files
            ],
            "dependency_pins": [
                {"name": name, "version": version} for name, version in self.dependency_pins
            ],
        }


# One build per process, revalidated against the source on every use.
_EVALUATOR_BUILD: EvaluatorBuild | None = None
_EVALUATOR_BUILD_DIR: Any = None


def _fingerprint(entries: list[tuple[str, str]]) -> str:
    """Fold a sorted (path, digest) list into one hash."""

    joined = "\n".join(f"{path} {digest}" for path, digest in sorted(entries))
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


def _dependency_pins(repo_root: Path) -> tuple[tuple[str, str], ...]:
    """Record the installed version of the evaluator's one runtime dependency.

    The compiled module imports ``zod`` at run time from ``node_modules``, whose
    contents this gate does not hash (see the residual note in the contract
    doc). Recording the installed version against the lockfile at least makes a
    substituted major version visible rather than silent.
    """

    pins: list[tuple[str, str]] = []
    installed = repo_root / "node_modules" / EVALUATOR_RUNTIME_DEPENDENCY / "package.json"
    try:
        pins.append(
            (
                EVALUATOR_RUNTIME_DEPENDENCY,
                str(json.loads(installed.read_text(encoding="utf-8")).get("version", "unknown")),
            )
        )
    except (OSError, ValueError):
        pins.append((EVALUATOR_RUNTIME_DEPENDENCY, "unresolved"))
    return tuple(pins)


def _resolve_toolchain() -> tuple[Path | None, dict[str, Any] | None]:
    """Return the repository-local TypeScript compiler, or a fail-closed error.

    The compiler must exist locally and its installed version must equal the
    version pinned in ``package-lock.json``. If it is absent or inconsistent,
    the gate fails **before** attempting compilation -- it never falls back to
    ``npx`` or any path that could acquire a package from a registry.
    """

    if not EVALUATOR_TS_COMPILER.is_file():
        return None, {
            "error": "evaluator_toolchain_unavailable",
            "detail": (
                "the repository-local TypeScript compiler "
                f"{_repo_relative(EVALUATOR_TS_COMPILER)} is absent; the gate refuses to acquire "
                "one and fails closed"
            ),
        }
    try:
        installed = json.loads(EVALUATOR_TS_PACKAGE_JSON.read_text(encoding="utf-8")).get("version")
    except (OSError, ValueError) as error:
        return None, {
            "error": "evaluator_toolchain_unavailable",
            "detail": f"could not read the installed TypeScript version: {error}",
        }
    try:
        locked = (
            json.loads(EVALUATOR_LOCKFILE.read_text(encoding="utf-8"))
            .get("packages", {})
            .get("node_modules/typescript", {})
            .get("version")
        )
    except (OSError, ValueError) as error:
        return None, {
            "error": "evaluator_toolchain_unavailable",
            "detail": f"could not read the pinned TypeScript version from the lockfile: {error}",
        }
    if not locked:
        return None, {
            "error": "evaluator_toolchain_unavailable",
            "detail": "the lockfile does not pin a TypeScript version",
        }
    if installed != locked:
        return None, {
            "error": "evaluator_toolchain_mismatch",
            "detail": (
                f"installed TypeScript {installed!r} does not match the lockfile pin {locked!r}; "
                "the gate fails closed rather than compiling with an unpinned compiler"
            ),
        }
    return EVALUATOR_TS_COMPILER, None


def _run_local_tsc(
    compiler: Path, argv: list[str], cwd: Path
) -> tuple[subprocess.CompletedProcess[bytes] | None, dict[str, Any] | None]:
    """Invoke the repository-local compiler as ``node <tsc>``.

    PATH is deliberately not consulted for the compiler: the absolute compiler
    path is passed to ``node``. The child environment carries no ``npm_*`` or
    proxy configuration, so no registry access can be initiated.
    """

    env = {
        "PATH": os.environ.get("PATH", ""),
        "HOME": os.environ.get("HOME", ""),
        # Belt and braces: even though tsc is invoked directly, deny npm any
        # registry, offline-forbid, and silence update checks, in case a
        # transitive tool ever shells out.
        "npm_config_offline": "true",
        "npm_config_registry": "http://127.0.0.1:0/",
        "NO_UPDATE_NOTIFIER": "1",
        "CI": "1",
    }
    try:
        completed = subprocess.run(  # noqa: S603 - fixed argv, no shell, absolute compiler
            ["node", str(compiler), *argv],
            capture_output=True,
            timeout=EVALUATOR_BUILD_TIMEOUT_SECONDS,
            cwd=str(cwd),
            env=env,
            check=False,
        )
    except FileNotFoundError:
        return None, {
            "error": "evaluator_build_unavailable",
            "detail": "'node' is not on PATH; the evaluator cannot be built from source",
        }
    except subprocess.TimeoutExpired:
        return None, {
            "error": "evaluator_build_timeout",
            "detail": f"the build did not finish within {EVALUATOR_BUILD_TIMEOUT_SECONDS}s",
        }
    return completed, None


def _tsc_repo_local_sources(
    stdout: str, root: Path
) -> tuple[list[str], list[str]]:
    """Split a ``--listFiles`` stdout into (repo-local sources, escapes).

    Repo-local means: under ``root`` and not under ``node_modules`` (which holds
    only ``.d.ts`` declarations, erased at emit). An "escape" is a listed file
    that is neither -- a repo-local read from outside the intended tree.
    """

    repo_local: list[str] = []
    escapes: list[str] = []
    for line in stdout.splitlines():
        listed = line.strip()
        if not listed.startswith("/"):
            continue
        listed_path = Path(listed)
        try:
            relative = listed_path.relative_to(root).as_posix()
        except ValueError:
            if f"{os.sep}node_modules{os.sep}" not in listed and "/node_modules/" not in listed:
                escapes.append(listed)
            continue
        if relative.startswith("node_modules/"):
            continue
        repo_local.append(relative)
    return repo_local, escapes


def build_evaluator(
    tsconfig_path: Path | None = None, repo_root: Path | None = None
) -> tuple[EvaluatorBuild | None, dict[str, Any] | None]:
    """Compile the reviewed contract from an immutable snapshot of its source.

    This is what establishes evaluator identity, and it is race-free by
    construction. The working tree is never the thing compiled or hashed:

    1. A discovery pass (``--noEmit --listFiles``) asks the local compiler which
       repo-local source files the contract transitively needs. Discovery is not
       an authority -- it only decides what to copy.
    2. Those files, plus the tsconfigs and the package manifests, are copied
       into a private snapshot directory this process owns. The snapshot is
       written once and never touched again.
    3. The snapshot bytes are compiled -- with the snapshot as the working
       directory, so repo-local module resolution is confined to the snapshot
       and cannot reach the working tree -- and the emitted module is hashed.
    4. The receipt hashes the **snapshot** source bytes, i.e. exactly the bytes
       that were compiled. Working-tree drift during compilation cannot change
       the snapshot, so the receipt can never describe bytes the compiler did
       not see.

    Nothing under ``dist/`` is read. The compiler is the repository-local,
    lock-pinned TypeScript, never ``npx``.

    Returns ``(build, None)`` or ``(None, error)``. It never raises for an
    ordinary build failure: a build that cannot be produced is a gate failure.
    """

    root = repo_root or REPO_ROOT
    tsconfig = tsconfig_path or EVALUATOR_TSCONFIG_PATH

    if not tsconfig.exists():
        return None, {
            "error": "evaluator_tsconfig_missing",
            "detail": f"{_repo_relative(tsconfig)} is absent; the build surface is not defined",
        }

    compiler, toolchain_error = _resolve_toolchain_for(root)
    if toolchain_error is not None:
        return None, toolchain_error

    # 1. Discovery pass over the working tree. Not authoritative.
    discovery, run_error = _run_local_tsc(
        compiler, ["-p", str(tsconfig), "--noEmit", "--listFiles"], root
    )
    if run_error is not None:
        return None, run_error
    disc_stdout = discovery.stdout.decode("utf-8", errors="replace")
    if discovery.returncode != 0:
        diagnostics = "\n".join(
            line for line in disc_stdout.splitlines() if not line.startswith("/")
        ).strip()
        return None, {
            "error": "evaluator_build_failed",
            "detail": (
                f"discovery compile of {EVALUATOR_ENTRY_SOURCE} failed "
                f"(exit {discovery.returncode}): "
                f"{diagnostics[:600] or discovery.stderr.decode('utf-8', errors='replace')[:600]}"
            ),
        }
    discovered, disc_escapes = _tsc_repo_local_sources(disc_stdout, root)
    if disc_escapes:
        return None, {
            "error": "evaluator_source_escape",
            "detail": f"discovery read repo-local files outside the tree: {disc_escapes[:4]}",
        }
    if EVALUATOR_ENTRY_SOURCE not in discovered:
        return None, {
            "error": "evaluator_entry_not_compiled",
            "detail": (
                f"discovery did not report reading {EVALUATOR_ENTRY_SOURCE}; the build surface "
                "does not contain the canonical contract"
            ),
        }

    snapshot_dir = tempfile.TemporaryDirectory(prefix="rb-contact-evasion-src-")
    build_dir = tempfile.TemporaryDirectory(prefix="rb-contact-evasion-out-")
    snap = Path(snapshot_dir.name)
    out_root = Path(build_dir.name)

    # 2. Snapshot every discovered source plus the config/lock surface. Copy the
    #    bytes once; the snapshot is immutable from here on.
    to_snapshot = sorted(set(discovered) | set(EVALUATOR_FINGERPRINT_EXTRA_PATHS))
    for relative in to_snapshot:
        source_path = root / relative
        target = snap / relative
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source_path.read_bytes())
        except OSError as error:
            snapshot_dir.cleanup()
            build_dir.cleanup()
            return None, {
                "error": "evaluator_source_unreadable",
                "detail": f"could not snapshot build input {relative}: {error}",
            }
    try:
        (snap / "node_modules").symlink_to(root / "node_modules", target_is_directory=True)
        (out_root / "node_modules").symlink_to(root / "node_modules", target_is_directory=True)
        (out_root / "package.json").write_text('{"type": "module"}\n', encoding="utf-8")
    except OSError as error:
        snapshot_dir.cleanup()
        build_dir.cleanup()
        return None, {
            "error": "evaluator_build_setup_failed",
            "detail": f"could not prepare the private build directories: {error}",
        }

    # 3. Hash the snapshot bytes: this is the authority.
    source_entries: list[tuple[str, str]] = []
    for relative in to_snapshot:
        try:
            source_entries.append((relative, sha256_hex((snap / relative).read_bytes())))
        except OSError as error:  # pragma: no cover - just written above
            snapshot_dir.cleanup()
            build_dir.cleanup()
            return None, {
                "error": "evaluator_source_unreadable",
                "detail": f"could not hash snapshot input {relative}: {error}",
            }

    # 4. Compile from the snapshot, confined to it.
    snap_tsconfig = snap / "scripts/rb_contact_evasion_evaluator.tsconfig.json"
    if not snap_tsconfig.is_file():
        snapshot_dir.cleanup()
        build_dir.cleanup()
        return None, {
            "error": "evaluator_tsconfig_missing",
            "detail": "the snapshot does not contain the evaluator tsconfig",
        }
    compile_run, run_error = _run_local_tsc(
        compiler,
        ["-p", str(snap_tsconfig), "--outDir", str(out_root), "--listFiles"],
        snap,
    )
    if run_error is not None:
        snapshot_dir.cleanup()
        build_dir.cleanup()
        return None, run_error
    comp_stdout = compile_run.stdout.decode("utf-8", errors="replace")
    if compile_run.returncode != 0:
        diagnostics = "\n".join(
            line for line in comp_stdout.splitlines() if not line.startswith("/")
        ).strip()
        snapshot_dir.cleanup()
        build_dir.cleanup()
        return None, {
            "error": "evaluator_build_failed",
            "detail": (
                f"compiling {EVALUATOR_ENTRY_SOURCE} from snapshot failed (exit "
                f"{compile_run.returncode}): "
                f"{diagnostics[:600] or compile_run.stderr.decode('utf-8', errors='replace')[:600]}"
            ),
        }

    # The snapshot compile must have read only snapshot files for repo-local
    # sources, and every repo-local file it read must have been snapshotted.
    compiled_local, comp_escapes = _tsc_repo_local_sources(comp_stdout, snap)
    if comp_escapes:
        snapshot_dir.cleanup()
        build_dir.cleanup()
        return None, {
            "error": "evaluator_source_escape",
            "detail": f"the snapshot compile read files outside the snapshot: {comp_escapes[:4]}",
        }
    snapshotted = {relative for relative, _ in source_entries}
    unsnapshotted = sorted(set(compiled_local) - snapshotted)
    if unsnapshotted:
        snapshot_dir.cleanup()
        build_dir.cleanup()
        return None, {
            "error": "evaluator_source_escape",
            "detail": (
                "the snapshot compile read un-snapshotted repo-local files: "
                f"{unsnapshotted[:4]}"
            ),
        }
    if EVALUATOR_ENTRY_SOURCE not in compiled_local:
        snapshot_dir.cleanup()
        build_dir.cleanup()
        return None, {
            "error": "evaluator_entry_not_compiled",
            "detail": (
                f"the snapshot compile did not report reading {EVALUATOR_ENTRY_SOURCE}"
            ),
        }

    module_path = out_root / EVALUATOR_ENTRY_OUTPUT
    if not module_path.is_file():
        snapshot_dir.cleanup()
        build_dir.cleanup()
        return None, {
            "error": "evaluator_build_incomplete",
            "detail": f"the build emitted no {EVALUATOR_ENTRY_OUTPUT}",
        }

    build = EvaluatorBuild(
        module_path=module_path,
        module_digest=sha256_hex(module_path.read_bytes()),
        source_fingerprint=_fingerprint(source_entries),
        source_files=tuple(sorted(source_entries)),
        dependency_pins=_dependency_pins(root),
    )
    # The snapshot must outlive the build only long enough to have been compiled;
    # it is retained alongside the output so a reviewer could inspect it, and is
    # released with the build.
    build.retained_dir = (snapshot_dir, build_dir)

    global _EVALUATOR_BUILD_DIR
    if tsconfig_path is None and repo_root is None:
        if _EVALUATOR_BUILD_DIR is not None:
            for handle in _iter_dir_handles(_EVALUATOR_BUILD_DIR):
                handle.cleanup()
        _EVALUATOR_BUILD_DIR = (snapshot_dir, build_dir)
        build.retained_dir = None

    return build, None


def _iter_dir_handles(handle: Any):
    if isinstance(handle, tuple):
        yield from handle
    elif handle is not None:
        yield handle


def _resolve_toolchain_for(root: Path) -> tuple[Path | None, dict[str, Any] | None]:
    """Toolchain resolution scoped to a given repository root (for isolated tests)."""

    if root == REPO_ROOT:
        return _resolve_toolchain()
    compiler = root / "node_modules/typescript/bin/tsc"
    if not compiler.is_file():
        return None, {
            "error": "evaluator_toolchain_unavailable",
            "detail": f"no repository-local TypeScript compiler under {root}",
        }
    return compiler, None


def ensure_evaluator() -> tuple[EvaluatorBuild | None, dict[str, Any] | None]:
    """Return a build known to correspond to the source as it is right now.

    Memoized per process, but the memo is re-checked rather than assumed: the
    fingerprinted files are re-hashed and the emitted module re-hashed on every
    use, so a source edit or a swapped module forces a rebuild instead of
    silently reusing a verdict from code that is no longer there.
    """

    global _EVALUATOR_BUILD

    cached = _EVALUATOR_BUILD
    if cached is not None:
        try:
            current = [
                (path, sha256_hex((REPO_ROOT / path).read_bytes()))
                for path, _ in cached.source_files
            ]
            module_unchanged = (
                cached.module_path.is_file()
                and sha256_hex(cached.module_path.read_bytes()) == cached.module_digest
            )
        except OSError:
            current, module_unchanged = [], False
        if module_unchanged and _fingerprint(current) == cached.source_fingerprint:
            return cached, None
        _EVALUATOR_BUILD = None

    build, error = build_evaluator()
    if error is not None:
        return None, error
    _EVALUATOR_BUILD = build
    return build, None


def canonical_contract_constants() -> dict[str, Any]:
    """Ask a freshly built contract what it is.

    The answer is an *agreement check* against this file's pins, never proof of
    identity: a substituted module can report anything. Identity comes from the
    build in :func:`build_evaluator`, which is what makes this question
    meaningful at all.
    """

    build, error = ensure_evaluator()
    if build is None:
        return {"ok": False, **(error or {"error": "evaluator_unavailable", "detail": ""})}
    return _run_bridge("constants", stdin_bytes=b"", build=build)


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
    bundle_root: Path,
    manifest: dict[str, Any],
    artifacts: list[ArtifactState],
    failures: list[Failure],
) -> None:
    """Verify type, byte length, and digest of one descriptor's exact bytes.

    Each artifact is opened once, descriptor-relatively and without following
    symlinks; its type and size are validated by ``fstat`` on that descriptor
    and its bytes read from it with a bounded read that reads at most ``cap + 1``
    bytes in total (peak reader ownership is one growing buffer plus one bounded
    read chunk and allocation headroom -- see ``_read_fd_capped``).
    Type, cap, size, and digest all bind to the same bytes. Once
    the digest matches, those bytes are frozen into an immutable ``bytes`` object
    -- the exact subject the digest authorized -- and it is that frozen object,
    never a re-read of the pathname and never a mutable alias, that later stages
    parse and evaluate. There is no stat-then-reopen window an oversized file,
    FIFO, device, or symlink could slip through, and no post-integrity in-place
    mutation window an alias could use to change what the evaluator judges.
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

        # One descriptor: open (no symlink follow), fstat (regular + cap), read
        # bounded. Type, size, and the bytes hashed all bind to the same inode.
        raw, (outcome, detail) = read_bundle_file(
            bundle_root, artifact.path, ARTIFACT_MAX_BYTES
        )
        if outcome != _ReadOutcome.OK:
            reason = {
                _ReadOutcome.MISSING: "BUNDLE_ARTIFACT_MISSING",
                _ReadOutcome.SYMLINK: "BUNDLE_PATH_NOT_REGULAR_FILE",
                _ReadOutcome.NOT_REGULAR: "BUNDLE_PATH_NOT_REGULAR_FILE",
                _ReadOutcome.TOO_LARGE: "BUNDLE_ARTIFACT_TOO_LARGE",
                _ReadOutcome.UNREADABLE: "BUNDLE_ARTIFACT_MISSING",
                _ReadOutcome.UNSUPPORTED: "BUNDLE_DESCRIPTOR_UNSUPPORTED",
            }[outcome]
            failures.append(Failure("integrity", reason, artifact.path, detail))
            artifact.block()
            continue
        assert raw is not None

        observed_size = len(raw)
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

        # The digest promise is made HERE: these exact bytes hash to the
        # manifest digest. Freeze them into an immutable ``bytes`` object at that
        # boundary so no later stage can alter the subject the digest authorized.
        # ``raw`` is a mutable ``bytearray`` from the bounded reader; aliasing it
        # into both fields (as the prior code did) let any holder flip a byte in
        # place -- e.g. a JSON-equivalent whitespace swap -- so the evaluator
        # could receive bytes whose SHA-256 no longer matched the digest just
        # proved. An immutable ``bytes`` copy cannot be mutated in place by any
        # alias, so the bytes parsed, schema-checked, and evaluated are byte-for-
        # byte the ones integrity bound. This copy is a deliberate second
        # payload-sized allocation made once, at the freeze; the mutable read
        # buffer is released immediately after (see ``_read_fd_capped`` and the
        # contract doc for the honest per-stage memory accounting).
        frozen = bytes(raw)
        del raw
        artifact.verified_bytes = frozen
        artifact.raw_bytes = frozen  # parsed in the next stage; same immutable object
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


# Exact, mutually exclusive bridge response envelopes. A response is admitted
# only if its key set matches one of these exactly and `ok` is the matching
# real boolean -- never a truthy non-boolean, never with extra or mixed fields.
_BRIDGE_CONSTANTS_KEYS = frozenset({"ok", "artifact_id", "schema_version"})
_BRIDGE_EVALUATE_KEYS = frozenset({"ok", "report"})
_BRIDGE_FAILURE_KEYS = frozenset({"ok", "error", "detail"})


def _bridge_failure(error: str, detail: str) -> dict[str, Any]:
    return {"ok": False, "error": error, "detail": detail}


def _run_bridge(mode: str, stdin_bytes: bytes, build: EvaluatorBuild) -> dict[str, Any]:
    """Invoke the Node bridge and admit exactly one strict, well-formed response.

    The transport is fail-closed at every step. A response is trusted only when
    the bridge exits 0, prints exactly one line, that line is a single strict
    JSON object with no duplicate keys, ``ok`` is a real boolean, and the object's
    key set matches the envelope for ``mode`` exactly. Anything else -- a nonzero
    exit, no output, extra lines, trailing bytes, a truthy non-boolean ``ok``,
    missing or extra fields, a mixed success/error shape -- is refused.

    The module path and its expected digest come from ``build``; the bridge
    re-hashes and refuses a mismatch, and executes the authenticated bytes
    in-memory without reopening the path.
    """

    if not BRIDGE_PATH.exists():
        return _bridge_failure("bridge_missing", f"{_repo_relative(BRIDGE_PATH)} is absent")

    try:
        completed = subprocess.run(  # noqa: S603 - fixed argv, no shell
            [
                "node",
                str(BRIDGE_PATH),
                mode,
                str(build.module_path),
                build.module_digest,
            ],
            input=stdin_bytes,
            capture_output=True,
            timeout=BRIDGE_TIMEOUT_SECONDS,
            cwd=str(REPO_ROOT),
            env={"PATH": os.environ.get("PATH", "")},
            check=False,
        )
    except FileNotFoundError:
        return _bridge_failure("node_unavailable", "the 'node' executable is not on PATH")
    except subprocess.TimeoutExpired:
        return _bridge_failure(
            "bridge_timeout", f"the bridge did not answer within {BRIDGE_TIMEOUT_SECONDS}s"
        )

    stderr_tail = completed.stderr.decode("utf-8", errors="replace").strip()[:400]

    # 1. Exit code must be success. A bridge that prints a success-looking line
    #    and then exits nonzero is refused here, before its output is trusted.
    if completed.returncode != 0:
        return _bridge_failure(
            "bridge_exit_nonzero",
            f"the bridge exited {completed.returncode}; its output is not trusted: {stderr_tail}",
        )

    # 2. Exactly one line of output. No output, or more than one line (a real
    #    refusal followed by a success line, say), is refused.
    try:
        text = completed.stdout.decode("utf-8")
    except UnicodeDecodeError as error:
        return _bridge_failure(
            "bridge_unreadable", f"the bridge output is not valid UTF-8: {error}"
        )
    lines = [line for line in text.split("\n") if line != ""]
    if len(lines) == 0:
        return _bridge_failure(
            "bridge_silent", f"the bridge exited 0 with no output: {stderr_tail}"
        )
    if len(lines) != 1:
        return _bridge_failure(
            "bridge_multiple_responses",
            f"the bridge emitted {len(lines)} lines; exactly one JSON object is required",
        )

    # 3. Exactly one strict JSON object, no duplicate keys, no JSON constants.
    try:
        payload = parse_json_strictly(lines[0].encode("utf-8"))
    except ValueError as error:
        reason = (
            "bridge_duplicate_key"
            if "duplicate object key" in str(error)
            else "bridge_unreadable"
        )
        return _bridge_failure(reason, f"the bridge response is not strict JSON: {error}")
    if not isinstance(payload, dict):
        return _bridge_failure("bridge_unreadable", "the bridge response is not a JSON object")

    # 4. `ok` must be a real boolean -- never a truthy string or number.
    ok = payload.get("ok")
    if ok is not True and ok is not False:
        return _bridge_failure(
            "bridge_ok_not_boolean",
            f"the bridge response 'ok' is {type(ok).__name__} {ok!r}, not a boolean",
        )

    keys = frozenset(payload)

    # 5. A declared failure must match the failure envelope exactly.
    if ok is False:
        if keys != _BRIDGE_FAILURE_KEYS:
            return _bridge_failure(
                "bridge_envelope_invalid",
                f"failure response keys {sorted(keys)} are not exactly "
                f"{sorted(_BRIDGE_FAILURE_KEYS)}",
            )
        return payload

    # 6. A success must match the envelope for this mode exactly -- never a
    #    mixed success/error shape, never extra fields.
    expected = _BRIDGE_CONSTANTS_KEYS if mode == "constants" else _BRIDGE_EVALUATE_KEYS
    if keys != expected:
        return _bridge_failure(
            "bridge_envelope_invalid",
            f"{mode} success keys {sorted(keys)} are not exactly {sorted(expected)}",
        )
    return payload


# The exact top-level shape Slice A's evaluator returns. Requiring the key set
# rather than a subset is deliberate: if the contract grows a field, this gate
# fails closed and gets re-reviewed instead of quietly ignoring it.
EVALUATOR_REPORT_KEYS = frozenset({"valid", "shape_valid", "violations", "reason_codes"})
EVALUATOR_VIOLATION_KEYS = frozenset({"reason_code", "path", "detail"})


def parse_evaluator_report(report: Any) -> tuple[dict[str, Any] | None, str | None]:
    """Validate the evaluator's verdict structurally, without coercion.

    A verdict is the one thing this gate cannot re-derive, so it has to be read
    exactly as given: no ``bool()``, no ``list()``, no ``or []``. Coercion is
    what let a report claiming ``valid: false`` with an empty ``violations``
    list produce a passing bundle -- the falsity was recorded on the artifact
    and then nothing was appended to the failure list.

    Returns ``(report, None)`` or ``(None, reason)``. Any malformed or
    internally contradictory report is a reason, and the caller turns it into
    ``BUNDLE_SEMANTIC_EVALUATOR_FAILED``.
    """

    if not isinstance(report, dict):
        return None, "the evaluator did not return an object"

    keys = set(report)
    if keys != EVALUATOR_REPORT_KEYS:
        missing = sorted(EVALUATOR_REPORT_KEYS - keys)
        unexpected = sorted(keys - EVALUATOR_REPORT_KEYS)
        return None, (
            f"the report's keys are {sorted(keys)}; expected exactly "
            f"{sorted(EVALUATOR_REPORT_KEYS)} (missing={missing}, unexpected={unexpected})"
        )

    valid = report["valid"]
    shape_valid = report["shape_valid"]
    # `isinstance(x, bool)` is exact here: it rejects 0/1 and "false" alike,
    # which truthiness would silently accept in opposite directions.
    if not isinstance(valid, bool):
        return None, f"'valid' is {type(valid).__name__} {valid!r}, not a boolean"
    if not isinstance(shape_valid, bool):
        return None, f"'shape_valid' is {type(shape_valid).__name__} {shape_valid!r}, not a boolean"

    reason_codes = report["reason_codes"]
    if not isinstance(reason_codes, list) or not all(
        isinstance(code, str) and code for code in reason_codes
    ):
        return None, "'reason_codes' is not a list of non-empty strings"
    if len(set(reason_codes)) != len(reason_codes):
        return None, "'reason_codes' repeats a code"

    violations = report["violations"]
    if not isinstance(violations, list):
        return None, "'violations' is not a list"
    for index, violation in enumerate(violations):
        if not isinstance(violation, dict) or set(violation) != EVALUATOR_VIOLATION_KEYS:
            return None, (
                f"violation {index} is not an object with exactly "
                f"{sorted(EVALUATOR_VIOLATION_KEYS)}"
            )
        if not isinstance(violation["reason_code"], str) or not violation["reason_code"]:
            return None, f"violation {index} has no non-empty reason_code"
        if not isinstance(violation["path"], str) or not isinstance(violation["detail"], str):
            return None, f"violation {index} has a non-string path or detail"

    violation_codes = {violation["reason_code"] for violation in violations}

    if valid:
        if violations:
            return None, "the report claims 'valid' while carrying violations"
        if reason_codes:
            return None, "the report claims 'valid' while carrying reason codes"
    else:
        if not violations:
            return None, "the report rejects the payload but names no violation"
        if not reason_codes:
            return None, "the report rejects the payload but names no reason code"

    if violation_codes != set(reason_codes):
        return None, (
            f"'reason_codes' {sorted(set(reason_codes))} disagrees with the violation codes "
            f"{sorted(violation_codes)}"
        )

    if not shape_valid and valid:
        return None, "the report claims 'valid' for a payload it could not parse"

    return report, None


def evaluate_semantics(artifacts: list[ArtifactState], failures: list[Failure]) -> None:
    """Hand the verified bytes to Slice A and reproduce its verdict verbatim.

    No reason code is invented, renamed, filtered or ranked here. The evaluator's
    own ``reason_codes`` are what a consumer reads, so a downstream CI check sees
    exactly the codes Slice A's tests pin.

    An invalid verdict always produces at least one failure. That is guaranteed
    structurally -- :func:`parse_evaluator_report` refuses a rejection that names
    no violation -- and then asserted again after the loop, so no path can mark
    an artifact rejected while leaving the failure list empty.
    """

    build, build_error = ensure_evaluator()
    if build is None:
        detail = (build_error or {}).get("detail", "")
        error = (build_error or {}).get("error", "evaluator_unavailable")
        for artifact in artifacts:
            if artifact.blocked or artifact.payload is UNPARSED:
                continue
            failures.append(
                Failure(
                    "semantic",
                    "BUNDLE_SEMANTIC_EVALUATOR_UNAVAILABLE",
                    artifact.path,
                    (
                        "the canonical evaluator could not be built from the reviewed source, so "
                        f"no verdict can be established: {error}: {detail}"
                    ),
                )
            )
            artifact.block()
        return

    for artifact in artifacts:
        if artifact.blocked or artifact.payload is UNPARSED:
            continue

        # The exact bytes integrity verified are sent to the evaluator. The
        # pathname is NOT reopened here: reopening would reintroduce a
        # time-of-use window and let a post-integrity swap decide what the
        # evaluator sees. Re-serialising the parsed payload would likewise let
        # this gate's serializer decide. Only the in-memory verified bytes go --
        # and they are the immutable ``bytes`` object integrity froze, so no
        # alias could have altered them in place since the digest was proved.
        raw = artifact.verified_bytes
        if raw is None:
            failures.append(
                Failure(
                    "semantic",
                    "BUNDLE_SEMANTIC_EVALUATOR_FAILED",
                    artifact.path,
                    "no verified bytes reached the semantic stage; refusing to evaluate",
                )
            )
            artifact.block()
            continue

        answer = _run_bridge("evaluate", stdin_bytes=raw, build=build)
        if answer.get("ok") is not True:
            error = answer.get("error")
            reason = (
                "BUNDLE_SEMANTIC_EVALUATOR_UNAVAILABLE"
                if error in {"node_unavailable", "bridge_missing", "compiled_module_unreadable"}
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

        report, malformed = parse_evaluator_report(answer.get("report"))
        if report is None:
            failures.append(
                Failure(
                    "semantic",
                    "BUNDLE_SEMANTIC_EVALUATOR_FAILED",
                    artifact.path,
                    (
                        "the canonical evaluator returned a report this gate will not act on, so "
                        f"the payload stays unvalidated: {malformed}"
                    ),
                )
            )
            artifact.block()
            continue

        artifact.contract = {
            "valid": report["valid"],
            "shape_valid": report["shape_valid"],
            "reason_codes": list(report["reason_codes"]),
        }

        if not report["valid"]:
            before = len(failures)
            for violation in report["violations"]:
                failures.append(
                    Failure(
                        "semantic",
                        violation["reason_code"],
                        artifact.path,
                        f"{violation['path']}: {violation['detail']}",
                    )
                )
            if len(failures) == before:  # pragma: no cover - structurally unreachable
                failures.append(
                    Failure(
                        "semantic",
                        "BUNDLE_SEMANTIC_EVALUATOR_FAILED",
                        artifact.path,
                        "the payload was rejected but no violation was recorded",
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

    # Preflight: the descriptor-bound read is the gate's only safe read path.
    # If the platform cannot provide its primitives, fail closed before opening
    # anything -- never fall back to a full-path open that could follow a symlink
    # out of the bundle.
    if not descriptor_primitives_available():
        failures.append(
            Failure(
                "manifest_read",
                "BUNDLE_DESCRIPTOR_UNSUPPORTED",
                ".",
                "the platform lacks the descriptor primitives (O_NOFOLLOW, O_PATH, "
                "O_NONBLOCK, dir_fd) required to prove no-follow component-relative "
                "access; the gate fails closed rather than reading bundle bytes",
            )
        )
        return GateResult(ok=False, failures=failures, artifacts=artifacts)

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
    check_integrity(bundle_root, manifest, artifacts, failures)
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

    # Closing sweep. An empty failure list is not, on its own, evidence that
    # anything was validated: an artifact could have been blocked by a path that
    # forgot to record why. Success therefore requires every declared artifact to
    # have *completed* the semantic stage, and any artifact that did not without
    # an explaining failure becomes one.
    # A manifest-scoped failure (an unreachable evaluator, a rejected identity)
    # already explains every artifact at once; the sweep is for the case where
    # nothing explains one.
    bundle_level_failure = any(failure.path == MANIFEST_FILENAME for failure in failures)
    for artifact in artifacts:
        if "semantic" in artifact.stages_passed:
            continue
        if not bundle_level_failure and not any(
            failure.path == artifact.path for failure in failures
        ):
            failures.append(
                Failure(
                    "semantic",
                    "BUNDLE_SEMANTIC_EVALUATOR_FAILED",
                    artifact.path,
                    (
                        "this artifact did not complete semantic evaluation and no failure "
                        "explains why; the gate refuses to report a pass it cannot account for"
                    ),
                )
            )

    complete = bool(artifacts) and all(
        "semantic" in artifact.stages_passed for artifact in artifacts
    )

    build, _ = ensure_evaluator()

    return GateResult(
        ok=not failures and complete,
        failures=sorted(failures, key=Failure.sort_key),
        artifacts=artifacts,
        evaluator=build.receipt() if build is not None else None,
    )


def render_human_report(bundle_root: Path, result: GateResult) -> str:
    """Deterministic human-readable diagnostics."""

    lines = [
        f"{GATE_ID}",
        f"bundle root: {bundle_root}",
        f"manifest:    {MANIFEST_FILENAME}",
        f"pinned:      {PINNED_ARTIFACT_ID} / {PINNED_SCHEMA_VERSION} / "
        f"{'|'.join(sorted(ADMITTED_DIGEST_ALGORITHMS))}",
        (
            "evaluator:   built from "
            f"{result.evaluator['entry_source']}, source fingerprint "
            f"{result.evaluator['source_fingerprint'][:16]}..., module "
            f"{result.evaluator['module_digest'][:16]}..."
            if result.evaluator is not None
            else "evaluator:   NOT BUILT - no semantic verdict was established"
        ),
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
        "--json-out",
        type=Path,
        default=None,
        help="disabled; capture deterministic --json stdout in the caller if needed",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    bundle_root = args.bundle_root

    if args.json_out is not None:
        # Fail before validation or any output-path inspection. A validated
        # bundle directory can be substituted for an ordinary real output
        # directory after a pathname preflight; descriptor no-follow checks do
        # not distinguish those two real directories. The gate therefore owns
        # no publication capability. Callers that need a file must capture the
        # deterministic ``--json`` stdout in a separately reviewed layer.
        raise GateUsageError(
            "--json-out is disabled: use --json and capture deterministic stdout outside the gate"
        )

    result = validate_bundle(bundle_root)
    machine = json.dumps(result.as_dict(), indent=2, sort_keys=True) + "\n"

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

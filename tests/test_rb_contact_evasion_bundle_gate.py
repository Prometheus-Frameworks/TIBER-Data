"""Boundary tests for the rb_contact_evasion_observations_v0 bundle gate (#234, Slice B).

Two things are proven here, and they are deliberately separate.

**Slice A still decides football.** Every committed Slice A fixture is driven
through the new boundary: P1-P9 stay accepted, and N1-N49 stay rejected for
their exact existing reason codes. The expected codes are *imported* from Slice
A's own test module rather than restated, so this file holds no second copy of
the reason-code map that could drift away from the contract.

**Slice B decides only bytes.** Everything the gate owns -- manifest shape,
pinned contract identity, path safety, bundle bijection, size and digest, strict
parsing, the committed JSON Schema -- is exercised against tampering, always on
temporary copies. No test in this module writes to a committed fixture, contract
file or schema.

The gate delegates semantic judgment to the compiled contract under ``dist/``.
The session fixture below builds it if it is absent; if it cannot be built the
tests fail rather than skip, because a skipped semantic stage is exactly the
false pass the gate exists to prevent.
"""

from __future__ import annotations

import hashlib
import json
import os
import socket
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
TESTS_DIR = Path(__file__).resolve().parent
FIXTURE_ROOT = REPO_ROOT / "test/fixtures/rb_contact_evasion"
REFERENCE_BUNDLE = FIXTURE_ROOT / "bundle"
ARTIFACT_SCHEMA_PATH = REPO_ROOT / "schemas/rb_contact_evasion_observations_v0.schema.json"

if str(TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(TESTS_DIR))

# Slice A's own pins. Importing them is the point: Slice B must preserve exactly
# the corpus and codes Slice A committed, not a copy of them.
import test_rb_contact_evasion_observations_v0 as slice_a  # noqa: E402

from scripts.validate_rb_contact_evasion_bundle import (  # noqa: E402
    ADMITTED_DIGEST_ALGORITHMS,
    EVALUATOR_ENTRY_SOURCE,
    FORBIDDEN_MANIFEST_KEYS,
    MANIFEST_FILENAME,
    PINNED_ARTIFACT_ID,
    PINNED_MANIFEST_VERSION,
    PINNED_SCHEMA_VERSION,
    GateUsageError,
    build_evaluator,
    canonical_contract_constants,
    ensure_evaluator,
    main,
    parse_evaluator_report,
    validate_bundle,
)

GATE_SCRIPT = REPO_ROOT / "scripts/validate_rb_contact_evasion_bundle.py"
BRIDGE_SCRIPT = REPO_ROOT / "scripts/rb_contact_evasion_contract_bridge.mjs"

POSITIVE_FIXTURES = slice_a.POSITIVE_FIXTURES
MANDATED_POSITIVE_FIXTURES = slice_a.MANDATED_POSITIVE_FIXTURES
NEGATIVE_FIXTURES = dict(slice_a.NEGATIVE_FIXTURES)
MANDATED_NEGATIVE_FIXTURES = dict(slice_a.MANDATED_NEGATIVE_FIXTURES)


# ---------------------------------------------------------------------------
# Session setup: the canonical evaluator must be reachable
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session", autouse=True)
def evaluator_is_buildable() -> None:
    """The gate compiles the contract itself; prove that works before anything else.

    Nothing here touches ``dist/``. If the build cannot be produced the tests
    fail rather than skip, because a skipped semantic stage is exactly the false
    pass the gate exists to prevent.
    """

    build, error = ensure_evaluator()
    assert build is not None, (
        "the gate must be able to compile the canonical contract from source; "
        f"it could not: {error}"
    )


@pytest.fixture
def fresh_evaluator_cache():
    """Clear the per-process build memo around a test that perturbs the build."""

    import scripts.validate_rb_contact_evasion_bundle as gate

    gate._EVALUATOR_BUILD = None
    yield
    gate._EVALUATOR_BUILD = None


# ---------------------------------------------------------------------------
# Bundle construction helpers. Temporary copies only.
# ---------------------------------------------------------------------------


def _fixture_path(name: str) -> Path:
    for sub in ("positive", "negative"):
        candidate = FIXTURE_ROOT / sub / name
        if candidate.exists():
            return candidate
    raise AssertionError(f"no committed fixture named {name}")


def make_bundle(
    root: Path,
    files: dict[str, bytes],
    *,
    manifest_overrides: dict | None = None,
    entry_overrides: dict[str, dict] | None = None,
    artifacts_override: list | None = None,
    manifest_bytes: bytes | None = None,
) -> Path:
    """Write a self-consistent bundle, then apply the requested tampering.

    The default is always a bundle that *passes*, so a test that fails proves
    the single thing it changed is what the gate caught.
    """

    root.mkdir(parents=True, exist_ok=True)
    entries = []
    for relative, raw in files.items():
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        entry = {
            "path": relative,
            "size_bytes": len(raw),
            "digest": hashlib.sha256(raw).hexdigest(),
        }
        entry.update((entry_overrides or {}).get(relative, {}))
        entries.append(entry)

    position = "fixture_only"
    for raw in files.values():
        try:
            position = json.loads(raw)["artifact_position"]
        except Exception:  # noqa: BLE001 - malformed payloads keep the default
            pass
        break

    manifest = {
        "manifest_version": PINNED_MANIFEST_VERSION,
        "artifact_id": PINNED_ARTIFACT_ID,
        "schema_version": PINNED_SCHEMA_VERSION,
        "artifact_position": position,
        "digest_algorithm": "sha256",
        "generated_at": "2026-08-25T00:00:00+00:00",
        "artifacts": entries if artifacts_override is None else artifacts_override,
    }
    manifest.update(manifest_overrides or {})

    payload = (
        manifest_bytes
        if manifest_bytes is not None
        else (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
    )
    (root / MANIFEST_FILENAME).write_bytes(payload)
    return root


def bundle_from_fixture(root: Path, name: str, **kwargs) -> Path:
    """A one-artifact bundle holding a byte-for-byte copy of a committed fixture."""

    raw = _fixture_path(name).read_bytes()
    return make_bundle(root, {f"observations/{name}": raw}, **kwargs)


def codes(result) -> list[str]:
    return result.reason_codes


def bundle_codes(result) -> list[str]:
    return [code for code in result.reason_codes if code.startswith("BUNDLE_")]


# ---------------------------------------------------------------------------
# Slice A's committed behaviour, exercised through the new boundary
# ---------------------------------------------------------------------------


def test_slice_a_corpus_is_intact() -> None:
    """Guard against corpus drift before anything is asserted about it."""

    assert MANDATED_POSITIVE_FIXTURES == [
        "p1_complete_derived_explosiveness_rate.json",
        "p2_raw_count_without_denominator.json",
        "p3_historical_testing_classified.json",
        "p4_rights_blocked_missing_component.json",
        "p5_declared_snapshot_supersession.json",
        "p6_weekly_and_season_windows_coexist.json",
        "p7_bucky_receipt_remains_partial.json",
    ]
    assert len(POSITIVE_FIXTURES) == 9
    assert len(NEGATIVE_FIXTURES) == 49
    assert len(MANDATED_NEGATIVE_FIXTURES) == 15
    assert len(set(NEGATIVE_FIXTURES.values())) == 49, "each negative fixture owns a distinct code"


@pytest.mark.parametrize("name", POSITIVE_FIXTURES)
def test_positive_fixtures_pass_the_gate(tmp_path: Path, name: str) -> None:
    """P1-P9 remain accepted end to end, through every Slice B stage."""

    result = validate_bundle(bundle_from_fixture(tmp_path / "b", name))
    assert result.ok, result.failures
    assert result.failures == []
    (artifact,) = result.artifacts
    assert artifact.contract == {"valid": True, "shape_valid": True, "reason_codes": []}
    assert artifact.stages_passed == [
        "path_safety",
        "bundle_bijection",
        "integrity",
        "payload_parse",
        "payload_shape",
        "manifest_payload_agreement",
        "semantic",
    ]


@pytest.mark.parametrize(("name", "expected"), sorted(NEGATIVE_FIXTURES.items()))
def test_negative_fixtures_keep_their_exact_reason_code(
    tmp_path: Path, name: str, expected: str
) -> None:
    """N1-N49 stay shape-valid and are rejected for their exact existing code.

    A self-consistent manifest is built for each one, so none of them can be
    rejected by integrity metadata. They reach the canonical evaluator, clear
    the committed JSON Schema, and are refused there -- and the code Slice A
    pins is reproduced verbatim, not translated.
    """

    result = validate_bundle(bundle_from_fixture(tmp_path / "b", name))
    assert not result.ok
    assert codes(result) == [expected]
    assert bundle_codes(result) == [], "no negative fixture may be rejected by the manifest gate"
    assert {failure.stage for failure in result.failures} == {"semantic"}

    (artifact,) = result.artifacts
    assert artifact.contract == {"valid": False, "shape_valid": True, "reason_codes": [expected]}
    assert (
        "payload_shape" in artifact.stages_passed
    ), "the fixture is shape-valid and reached semantics"
    assert "semantic" not in artifact.stages_passed


def test_no_negative_fixture_passes_because_its_manifest_is_consistent(tmp_path: Path) -> None:
    """The whole corpus in one bundle, perfectly described, still fails."""

    files = {
        f"observations/{name}": _fixture_path(name).read_bytes()
        for name in sorted(NEGATIVE_FIXTURES)
        if json.loads(_fixture_path(name).read_bytes())["artifact_position"] == "fixture_only"
    }
    result = validate_bundle(make_bundle(tmp_path / "b", files))
    assert not result.ok
    assert bundle_codes(result) == []
    expected = sorted(
        {NEGATIVE_FIXTURES[Path(path).name] for path in files}
    )
    assert codes(result) == expected


def test_mandated_negative_codes_are_reproduced_verbatim(tmp_path: Path) -> None:
    """N1-N15, the corpus #234 mandates, keep their exact codes at the boundary."""

    for name, expected in sorted(MANDATED_NEGATIVE_FIXTURES.items()):
        result = validate_bundle(bundle_from_fixture(tmp_path / name, name))
        assert codes(result) == [expected], name


# ---------------------------------------------------------------------------
# The committed reference bundle
# ---------------------------------------------------------------------------


def test_reference_bundle_passes() -> None:
    result = validate_bundle(REFERENCE_BUNDLE)
    assert result.ok, result.failures
    assert [artifact.path for artifact in result.artifacts] == [
        "observations/p2_raw_count_without_denominator.json",
        "observations/p7_bucky_receipt_remains_partial.json",
    ]


def test_reference_bundle_artifacts_are_byte_copies_of_committed_fixtures() -> None:
    """The bundle copies must never drift from the fixtures they mirror."""

    for name in (
        "p2_raw_count_without_denominator.json",
        "p7_bucky_receipt_remains_partial.json",
    ):
        assert (REFERENCE_BUNDLE / "observations" / name).read_bytes() == _fixture_path(
            name
        ).read_bytes(), name


def test_reference_bundle_is_not_a_candidate_artifact() -> None:
    """It is a gate fixture. It must not look like governed or candidate data."""

    manifest = json.loads((REFERENCE_BUNDLE / MANIFEST_FILENAME).read_text())
    assert manifest["artifact_position"] == "fixture_only"
    for path in (REFERENCE_BUNDLE / "observations").glob("*.json"):
        assert json.loads(path.read_text())["artifact_position"] == "fixture_only"
    assert not (REPO_ROOT / "exports/candidates/rb_contact_evasion").exists()
    assert not (REPO_ROOT / "exports/promoted/rb_contact_evasion").exists()


# ---------------------------------------------------------------------------
# Integrity: size and digest, before any parse
# ---------------------------------------------------------------------------


def test_byte_append_is_caught(tmp_path: Path) -> None:
    root = bundle_from_fixture(tmp_path / "b", "p2_raw_count_without_denominator.json")
    target = root / "observations/p2_raw_count_without_denominator.json"
    target.write_bytes(target.read_bytes() + b"\n")
    result = validate_bundle(root)
    assert codes(result) == ["BUNDLE_SIZE_MISMATCH"]


def test_byte_append_with_updated_size_is_caught_by_the_digest(tmp_path: Path) -> None:
    """Correcting the size does not launder the change; the digest still fails."""

    name = "p2_raw_count_without_denominator.json"
    raw = _fixture_path(name).read_bytes() + b"\n"
    root = make_bundle(
        tmp_path / "b",
        {f"observations/{name}": raw},
        entry_overrides={
            f"observations/{name}": {"digest": hashlib.sha256(b"other").hexdigest()}
        },
    )
    result = validate_bundle(root)
    assert codes(result) == ["BUNDLE_DIGEST_MISMATCH"]


def test_same_length_byte_flip_is_caught(tmp_path: Path) -> None:
    """A size check alone would miss this; the digest is what catches it."""

    name = "p2_raw_count_without_denominator.json"
    original = _fixture_path(name).read_bytes()
    root = bundle_from_fixture(tmp_path / "b", name)
    target = root / f"observations/{name}"
    flipped = original.replace(b'"value": 62', b'"value": 63', 1)
    assert flipped != original and len(flipped) == len(original)
    target.write_bytes(flipped)
    result = validate_bundle(root)
    assert codes(result) == ["BUNDLE_DIGEST_MISMATCH"]


def test_wrong_declared_size_is_caught(tmp_path: Path) -> None:
    name = "p2_raw_count_without_denominator.json"
    root = bundle_from_fixture(
        tmp_path / "b", name, entry_overrides={f"observations/{name}": {"size_bytes": 1}}
    )
    result = validate_bundle(root)
    assert codes(result) == ["BUNDLE_SIZE_MISMATCH"]


def test_wrong_declared_digest_is_caught(tmp_path: Path) -> None:
    name = "p2_raw_count_without_denominator.json"
    root = bundle_from_fixture(
        tmp_path / "b",
        name,
        entry_overrides={f"observations/{name}": {"digest": "0" * 64}},
    )
    result = validate_bundle(root)
    assert codes(result) == ["BUNDLE_DIGEST_MISMATCH"]


def test_integrity_runs_before_parsing(tmp_path: Path) -> None:
    """Malformed bytes with a wrong digest never reach the parser."""

    root = make_bundle(
        tmp_path / "b",
        {"observations/a.json": b"{ this is not json"},
        entry_overrides={"observations/a.json": {"digest": "1" * 64}},
    )
    result = validate_bundle(root)
    assert codes(result) == ["BUNDLE_DIGEST_MISMATCH"]
    (artifact,) = result.artifacts
    assert "payload_parse" not in artifact.stages_passed
    assert artifact.contract is None


def test_malformed_digest_value_is_rejected(tmp_path: Path) -> None:
    name = "p2_raw_count_without_denominator.json"
    for bad in ("abc", "0" * 63, "0" * 65):
        root = bundle_from_fixture(
            tmp_path / bad, name, entry_overrides={f"observations/{name}": {"digest": bad}}
        )
        assert codes(validate_bundle(root)) == ["BUNDLE_DIGEST_VALUE_MALFORMED"], bad


def test_non_hex_digest_fails_the_manifest_shape(tmp_path: Path) -> None:
    """Uppercase and non-hex digests never reach the byte checks at all."""

    name = "p2_raw_count_without_denominator.json"
    for bad in ("A" * 64, "z" * 64):
        root = bundle_from_fixture(
            tmp_path / bad, name, entry_overrides={f"observations/{name}": {"digest": bad}}
        )
        assert codes(validate_bundle(root)) == ["BUNDLE_MANIFEST_SHAPE_INVALID"], bad


def test_unsupported_digest_algorithm_is_rejected(tmp_path: Path) -> None:
    name = "p2_raw_count_without_denominator.json"
    for algorithm in ("md5", "sha1", "crc32", "none", ""):
        root = bundle_from_fixture(
            tmp_path / f"alg-{algorithm or 'empty'}",
            name,
            manifest_overrides={"digest_algorithm": algorithm},
        )
        result = validate_bundle(root)
        assert "BUNDLE_DIGEST_ALGORITHM_UNSUPPORTED" in codes(result) or codes(result) == [
            "BUNDLE_MANIFEST_SHAPE_INVALID"
        ], algorithm


def test_malformed_digest_algorithm_type_is_rejected(tmp_path: Path) -> None:
    root = bundle_from_fixture(
        tmp_path / "b",
        "p2_raw_count_without_denominator.json",
        manifest_overrides={"digest_algorithm": 256},
    )
    assert codes(validate_bundle(root)) == ["BUNDLE_MANIFEST_SHAPE_INVALID"]


# ---------------------------------------------------------------------------
# Bijection and containment
# ---------------------------------------------------------------------------


def test_missing_artifact_is_caught(tmp_path: Path) -> None:
    name = "p2_raw_count_without_denominator.json"
    root = bundle_from_fixture(tmp_path / "b", name)
    (root / f"observations/{name}").unlink()
    assert codes(validate_bundle(root)) == ["BUNDLE_ARTIFACT_MISSING"]


def test_undeclared_extra_file_is_caught(tmp_path: Path) -> None:
    """Every per-entry digest still matches; only the bijection catches this."""

    root = bundle_from_fixture(tmp_path / "b", "p2_raw_count_without_denominator.json")
    (root / "observations/smuggled.json").write_bytes(b"{}\n")
    result = validate_bundle(root)
    assert codes(result) == ["BUNDLE_UNDECLARED_FILE"]
    assert result.failures[0].path == "observations/smuggled.json"


def test_undeclared_file_outside_the_observations_directory_is_caught(tmp_path: Path) -> None:
    root = bundle_from_fixture(tmp_path / "b", "p2_raw_count_without_denominator.json")
    (root / "README.txt").write_bytes(b"harmless looking\n")
    assert codes(validate_bundle(root)) == ["BUNDLE_UNDECLARED_FILE"]


def test_duplicate_manifest_entry_is_caught(tmp_path: Path) -> None:
    name = "p2_raw_count_without_denominator.json"
    raw = _fixture_path(name).read_bytes()
    entry = {
        "path": f"observations/{name}",
        "size_bytes": len(raw),
        "digest": hashlib.sha256(raw).hexdigest(),
    }
    root = make_bundle(
        tmp_path / "b", {f"observations/{name}": raw}, artifacts_override=[entry, dict(entry)]
    )
    assert codes(validate_bundle(root)) == ["BUNDLE_DUPLICATE_MANIFEST_ENTRY"]


def test_empty_artifact_list_fails_closed(tmp_path: Path) -> None:
    """A bundle declaring nothing is not a bundle that passed."""

    root = make_bundle(tmp_path / "b", {}, artifacts_override=[])
    assert codes(validate_bundle(root)) == ["BUNDLE_MANIFEST_SHAPE_INVALID"]


def test_manifest_declaring_itself_is_rejected(tmp_path: Path) -> None:
    root = bundle_from_fixture(tmp_path / "b", "p2_raw_count_without_denominator.json")
    manifest = json.loads((root / MANIFEST_FILENAME).read_text())
    manifest["artifacts"].append(
        {"path": MANIFEST_FILENAME, "size_bytes": 2, "digest": "0" * 64}
    )
    (root / MANIFEST_FILENAME).write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    assert "BUNDLE_MANIFEST_DECLARES_ITSELF" in codes(validate_bundle(root))


# ---------------------------------------------------------------------------
# Path safety
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("/etc/passwd", "BUNDLE_PATH_NOT_RELATIVE"),
        ("/tmp/elsewhere.json", "BUNDLE_PATH_NOT_RELATIVE"),
        ("C:/windows/system32/config", "BUNDLE_PATH_NOT_RELATIVE"),
        ("../outside.json", "BUNDLE_PATH_TRAVERSAL"),
        ("observations/../../outside.json", "BUNDLE_PATH_TRAVERSAL"),
        ("observations/../observations/a.json", "BUNDLE_PATH_TRAVERSAL"),
        ("./observations/a.json", "BUNDLE_PATH_NOT_NORMALIZED"),
        ("observations//a.json", "BUNDLE_PATH_NOT_NORMALIZED"),
        ("observations/", "BUNDLE_PATH_NOT_NORMALIZED"),
        ("observations\\a.json", "BUNDLE_PATH_NOT_NORMALIZED"),
    ],
)
def test_unsafe_paths_are_rejected(tmp_path: Path, path: str, expected: str) -> None:
    """Rejected on shape, before the filesystem is touched at all."""

    root = tmp_path / "b"
    root.mkdir()
    (root / "observations").mkdir()
    (root / "observations/a.json").write_bytes(b"{}\n")
    make_bundle(
        root,
        {},
        artifacts_override=[{"path": path, "size_bytes": 3, "digest": "0" * 64}],
    )
    result = validate_bundle(root)
    assert expected in codes(result), (path, codes(result))


def test_traversal_target_outside_the_bundle_is_never_read(tmp_path: Path) -> None:
    """A real, digest-matching file one directory up still cannot be admitted."""

    outside = tmp_path / "outside.json"
    raw = _fixture_path("p2_raw_count_without_denominator.json").read_bytes()
    outside.write_bytes(raw)
    root = make_bundle(
        tmp_path / "b",
        {},
        artifacts_override=[
            {
                "path": "../outside.json",
                "size_bytes": len(raw),
                "digest": hashlib.sha256(raw).hexdigest(),
            }
        ],
    )
    result = validate_bundle(root)
    assert codes(result) == ["BUNDLE_PATH_TRAVERSAL"]
    assert result.artifacts[0].contract is None


def test_declared_symlink_is_rejected(tmp_path: Path) -> None:
    name = "p2_raw_count_without_denominator.json"
    raw = _fixture_path(name).read_bytes()
    outside = tmp_path / "real.json"
    outside.write_bytes(raw)
    root = tmp_path / "b"
    (root / "observations").mkdir(parents=True)
    os.symlink(outside, root / "observations/link.json")
    make_bundle(
        root,
        {},
        artifacts_override=[
            {
                "path": "observations/link.json",
                "size_bytes": len(raw),
                "digest": hashlib.sha256(raw).hexdigest(),
            }
        ],
    )
    assert "BUNDLE_PATH_NOT_REGULAR_FILE" in codes(validate_bundle(root))


def test_symlinked_parent_directory_is_rejected(tmp_path: Path) -> None:
    """A linked directory is as good an escape as a linked file."""

    name = "p2_raw_count_without_denominator.json"
    raw = _fixture_path(name).read_bytes()
    real_dir = tmp_path / "elsewhere"
    real_dir.mkdir()
    (real_dir / "a.json").write_bytes(raw)
    root = tmp_path / "b"
    root.mkdir()
    os.symlink(real_dir, root / "observations")
    make_bundle(
        root,
        {},
        artifacts_override=[
            {
                "path": "observations/a.json",
                "size_bytes": len(raw),
                "digest": hashlib.sha256(raw).hexdigest(),
            }
        ],
    )
    assert "BUNDLE_PATH_NOT_REGULAR_FILE" in codes(validate_bundle(root))


def test_declared_symlink_is_rejected_by_path_safety_specifically(tmp_path: Path) -> None:
    """The per-component symlink check is what refuses it, not root containment.

    Mutation testing found this gap: with the component check removed, a leaf
    symlink pointing outside was still refused, but by ``BUNDLE_PATH_ESCAPES_ROOT``
    after the gate had already resolved through the link. Asserting the exact code
    pins which control is doing the work.
    """

    name = "p2_raw_count_without_denominator.json"
    raw = _fixture_path(name).read_bytes()
    outside = tmp_path / "real.json"
    outside.write_bytes(raw)
    root = tmp_path / "b"
    (root / "observations").mkdir(parents=True)
    os.symlink(outside, root / "observations/link.json")
    make_bundle(
        root,
        {},
        artifacts_override=[
            {
                "path": "observations/link.json",
                "size_bytes": len(raw),
                "digest": hashlib.sha256(raw).hexdigest(),
            }
        ],
    )
    result = validate_bundle(root)
    # Exact equality is the point: without the component check the link resolves
    # and BUNDLE_PATH_ESCAPES_ROOT appears alongside this code.
    assert codes(result) == ["BUNDLE_PATH_NOT_REGULAR_FILE"]
    assert "path_safety" in {failure.stage for failure in result.failures}
    assert result.artifacts[0].observed_digest is None
    assert result.artifacts[0].stages_passed == []


def test_symlink_to_a_file_inside_the_bundle_is_never_read_through(tmp_path: Path) -> None:
    """Root containment cannot catch this one: the target is inside the bundle.

    Only the per-component symlink check stops the gate opening the file through
    a link, so this asserts that no bytes were read for the aliased entry.
    """

    name = "p2_raw_count_without_denominator.json"
    raw = _fixture_path(name).read_bytes()
    root = tmp_path / "b"
    (root / "observations").mkdir(parents=True)
    (root / "observations/real.json").write_bytes(raw)
    os.symlink(root / "observations/real.json", root / "observations/alias.json")
    digest = hashlib.sha256(raw).hexdigest()
    make_bundle(
        root,
        {},
        artifacts_override=[
            {"path": "observations/real.json", "size_bytes": len(raw), "digest": digest},
            {"path": "observations/alias.json", "size_bytes": len(raw), "digest": digest},
        ],
    )
    result = validate_bundle(root)
    assert "BUNDLE_PATH_NOT_REGULAR_FILE" in codes(result)

    alias = next(a for a in result.artifacts if a.path == "observations/alias.json")
    assert alias.observed_digest is None, "the gate must not read through a symlink at all"
    assert alias.observed_size is None
    assert alias.stages_passed == []


def test_symlinked_parent_directory_is_rejected_by_path_safety_specifically(
    tmp_path: Path,
) -> None:
    name = "p2_raw_count_without_denominator.json"
    raw = _fixture_path(name).read_bytes()
    real_dir = tmp_path / "elsewhere"
    real_dir.mkdir()
    (real_dir / "a.json").write_bytes(raw)
    root = tmp_path / "b"
    root.mkdir()
    os.symlink(real_dir, root / "observations")
    make_bundle(
        root,
        {},
        artifacts_override=[
            {
                "path": "observations/a.json",
                "size_bytes": len(raw),
                "digest": hashlib.sha256(raw).hexdigest(),
            }
        ],
    )
    result = validate_bundle(root)
    assert codes(result) == ["BUNDLE_PATH_NOT_REGULAR_FILE"]
    artifact = result.artifacts[0]
    assert artifact.observed_digest is None
    assert artifact.stages_passed == []


def test_undeclared_symlink_anywhere_in_the_bundle_is_rejected(tmp_path: Path) -> None:
    root = bundle_from_fixture(tmp_path / "b", "p2_raw_count_without_denominator.json")
    os.symlink(tmp_path, root / "escape")
    assert "BUNDLE_PATH_NOT_REGULAR_FILE" in codes(validate_bundle(root))


def test_non_regular_file_is_rejected(tmp_path: Path) -> None:
    root = bundle_from_fixture(tmp_path / "b", "p2_raw_count_without_denominator.json")
    os.mkfifo(root / "observations/pipe.json")
    result = validate_bundle(root)
    assert "BUNDLE_PATH_NOT_REGULAR_FILE" in codes(result)


def test_declared_non_regular_file_is_rejected(tmp_path: Path) -> None:
    root = tmp_path / "b"
    (root / "observations").mkdir(parents=True)
    os.mkfifo(root / "observations/pipe.json")
    make_bundle(
        root,
        {},
        artifacts_override=[
            {"path": "observations/pipe.json", "size_bytes": 0, "digest": "0" * 64}
        ],
    )
    assert "BUNDLE_PATH_NOT_REGULAR_FILE" in codes(validate_bundle(root))


def test_declared_directory_is_rejected(tmp_path: Path) -> None:
    root = tmp_path / "b"
    (root / "observations/nested").mkdir(parents=True)
    make_bundle(
        root,
        {},
        artifacts_override=[
            {"path": "observations/nested", "size_bytes": 0, "digest": "0" * 64}
        ],
    )
    assert "BUNDLE_PATH_NOT_REGULAR_FILE" in codes(validate_bundle(root))


# ---------------------------------------------------------------------------
# Pinned contract identity
# ---------------------------------------------------------------------------


def test_pins_agree_with_the_canonical_contract() -> None:
    """The pins in code are checked against Slice A, not asserted against a copy."""

    canonical = canonical_contract_constants()
    assert canonical["ok"], canonical
    assert canonical["artifact_id"] == PINNED_ARTIFACT_ID
    assert canonical["schema_version"] == PINNED_SCHEMA_VERSION


def test_pinned_schema_version_matches_the_committed_json_schema() -> None:
    schema = json.loads(ARTIFACT_SCHEMA_PATH.read_text())
    assert schema["properties"]["schema_version"]["const"] == PINNED_SCHEMA_VERSION
    assert schema["properties"]["artifact_id"]["const"] == PINNED_ARTIFACT_ID


@pytest.mark.parametrize(
    "override",
    [
        {"artifact_id": "rb_contact_evasion_observations_v1"},
        {"artifact_id": "player_season_coverage_v0"},
        {"schema_version": "rb_contact_evasion_observations_v0.3.0"},
        {"schema_version": "rb_contact_evasion_observations_v0.5.0"},
        {"manifest_version": "rb_contact_evasion_observations_bundle_manifest_v0.2.0"},
    ],
)
def test_wrong_declared_contract_identity_is_rejected(tmp_path: Path, override: dict) -> None:
    """The manifest restates the identity; it can never redefine it."""

    root = bundle_from_fixture(
        tmp_path / "b", "p2_raw_count_without_denominator.json", manifest_overrides=override
    )
    result = validate_bundle(root)
    assert "BUNDLE_CONTRACT_IDENTITY_MISMATCH" in codes(result)
    assert result.artifacts[0].contract is None, "semantics never run on an unestablished identity"


def test_identity_failure_suppresses_the_semantic_verdict(tmp_path: Path) -> None:
    """A wrong-identity bundle must not report a passing payload."""

    root = bundle_from_fixture(
        tmp_path / "b",
        "p2_raw_count_without_denominator.json",
        manifest_overrides={"artifact_id": "something_else"},
    )
    result = validate_bundle(root)
    assert not result.ok
    assert all(artifact.contract is None for artifact in result.artifacts)


# ---------------------------------------------------------------------------
# Parsing: a matching digest never excuses malformed JSON
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "raw",
    [
        b"{ this is not json",
        b"",
        # `null` and `[]` parse, so the committed shape gate is what stops them.
        # They are kept here to prove the boundary refuses them somewhere, and
        # that neither reaches the evaluator.
        b"null",
        b"[]",
        b'{"artifact_id": "rb_contact_evasion_observations_v0",}',
        b"\xff\xfe not utf-8",
    ],
)
def test_malformed_json_with_matching_digest_is_rejected(tmp_path: Path, raw: bytes) -> None:
    """Size and digest are correct by construction here; the parse is what fails."""

    root = make_bundle(tmp_path / "b", {"observations/a.json": raw})
    result = validate_bundle(root)
    assert not result.ok
    assert set(codes(result)) <= {
        "BUNDLE_ARTIFACT_JSON_MALFORMED",
        "BUNDLE_ARTIFACT_SCHEMA_INVALID",
    }, codes(result)
    (artifact,) = result.artifacts
    assert (
        "integrity" in artifact.stages_passed
    ), "integrity passed; the failure is downstream of it"
    assert artifact.contract is None, "nothing unparseable or misshapen reaches the evaluator"


def test_duplicate_json_key_with_matching_digest_is_rejected(tmp_path: Path) -> None:
    """Last-wins duplicate keys would let two readers see two different payloads."""

    raw = b'{"artifact_id": "a", "artifact_id": "b"}'
    root = make_bundle(tmp_path / "b", {"observations/a.json": raw})
    assert codes(validate_bundle(root)) == ["BUNDLE_ARTIFACT_DUPLICATE_KEY"]


def test_non_json_constants_are_rejected(tmp_path: Path) -> None:
    """Python accepts NaN by default; JavaScript does not. The gate rejects it."""

    raw = b'{"artifact_id": NaN}'
    root = make_bundle(tmp_path / "b", {"observations/a.json": raw})
    assert codes(validate_bundle(root)) == ["BUNDLE_ARTIFACT_JSON_MALFORMED"]


def test_malformed_manifest_json_is_rejected(tmp_path: Path) -> None:
    root = make_bundle(
        tmp_path / "b",
        {"observations/a.json": b"{}\n"},
        manifest_bytes=b"{ not json",
    )
    assert codes(validate_bundle(root)) == ["BUNDLE_MANIFEST_JSON_MALFORMED"]


def test_duplicate_manifest_json_key_is_rejected(tmp_path: Path) -> None:
    root = make_bundle(
        tmp_path / "b",
        {"observations/a.json": b"{}\n"},
        manifest_bytes=b'{"artifact_id": "a", "artifact_id": "b"}',
    )
    assert codes(validate_bundle(root)) == ["BUNDLE_MANIFEST_DUPLICATE_KEY"]


def test_missing_manifest_is_rejected(tmp_path: Path) -> None:
    root = tmp_path / "b"
    (root / "observations").mkdir(parents=True)
    (root / "observations/a.json").write_bytes(b"{}\n")
    assert codes(validate_bundle(root)) == ["BUNDLE_MANIFEST_UNREADABLE"]


def test_symlinked_manifest_is_rejected(tmp_path: Path) -> None:
    real = tmp_path / "real_manifest.json"
    real.write_text("{}")
    root = tmp_path / "b"
    root.mkdir()
    os.symlink(real, root / MANIFEST_FILENAME)
    assert codes(validate_bundle(root)) == ["BUNDLE_MANIFEST_UNREADABLE"]


def test_missing_bundle_root_is_rejected(tmp_path: Path) -> None:
    assert codes(validate_bundle(tmp_path / "nope")) == ["BUNDLE_ROOT_INVALID"]


# ---------------------------------------------------------------------------
# The committed JSON Schema shape gate
# ---------------------------------------------------------------------------


def test_schema_gate_rejects_a_structurally_wrong_payload(tmp_path: Path) -> None:
    raw = json.dumps({"artifact_id": "rb_contact_evasion_observations_v0"}).encode()
    root = make_bundle(tmp_path / "b", {"observations/a.json": raw})
    result = validate_bundle(root)
    assert codes(result) == ["BUNDLE_ARTIFACT_SCHEMA_INVALID"]
    assert result.artifacts[0].contract is None


def test_schema_gate_rejects_an_unknown_field(tmp_path: Path) -> None:
    payload = json.loads(_fixture_path("p2_raw_count_without_denominator.json").read_text())
    payload["smuggled_field"] = True
    raw = json.dumps(payload, indent=2).encode()
    root = make_bundle(tmp_path / "b", {"observations/a.json": raw})
    assert codes(validate_bundle(root)) == ["BUNDLE_ARTIFACT_SCHEMA_INVALID"]


def test_schema_gate_runs_before_semantics(tmp_path: Path) -> None:
    payload = json.loads(_fixture_path("p2_raw_count_without_denominator.json").read_text())
    payload["observations"][0]["mechanism_id"] = "elusiveness"
    raw = json.dumps(payload, indent=2).encode()
    root = make_bundle(tmp_path / "b", {"observations/a.json": raw})
    result = validate_bundle(root)
    assert codes(result) == ["BUNDLE_ARTIFACT_SCHEMA_INVALID"]
    assert result.artifacts[0].contract is None


# ---------------------------------------------------------------------------
# The manifest may never weaken a contract rule
# ---------------------------------------------------------------------------


def test_manifest_schema_is_closed_and_carries_no_contract_authority() -> None:
    """Structural proof, not prose: the manifest has no field to hide behind."""

    schema = json.loads(
        (
            REPO_ROOT / "schemas/rb_contact_evasion_observations_bundle_manifest_v0.schema.json"
        ).read_text()
    )
    assert schema["additionalProperties"] is False
    assert schema["$defs"]["artifactEntry"]["additionalProperties"] is False
    admitted = set(schema["properties"])
    assert admitted & FORBIDDEN_MANIFEST_KEYS == set()
    assert admitted == {
        "manifest_version",
        "artifact_id",
        "schema_version",
        "artifact_position",
        "digest_algorithm",
        "generated_at",
        "bundle_note",
        "artifacts",
    }
    assert set(schema["$defs"]["artifactEntry"]["properties"]) == {"path", "size_bytes", "digest"}


@pytest.mark.parametrize(
    "key",
    [
        "skip_semantic_validation",
        "suppressed_reason_codes",
        "permissions",
        "promotable",
        "valid",
        "waivers",
        "override",
        "score",
        "rank",
        "metric_dictionary",
        "missingness_reason",
        "provenance_mode",
    ],
)
def test_manifest_cannot_declare_a_weakening_field(tmp_path: Path, key: str) -> None:
    root = bundle_from_fixture(
        tmp_path / "b",
        "p2_raw_count_without_denominator.json",
        manifest_overrides={key: True},
    )
    assert codes(validate_bundle(root)) == ["BUNDLE_MANIFEST_SHAPE_INVALID"]


def test_every_forbidden_key_is_refused_by_the_committed_schema(tmp_path: Path) -> None:
    for key in sorted(FORBIDDEN_MANIFEST_KEYS):
        root = bundle_from_fixture(
            tmp_path / f"k-{key}",
            "p2_raw_count_without_denominator.json",
            manifest_overrides={key: "anything"},
        )
        assert codes(validate_bundle(root)) == ["BUNDLE_MANIFEST_SHAPE_INVALID"], key


def test_manifest_cannot_downgrade_a_candidate_to_fixture_position(tmp_path: Path) -> None:
    """The rules a candidate faces are not escapable by relabelling the manifest."""

    payload = json.loads(_fixture_path("p2_raw_count_without_denominator.json").read_text())
    payload["artifact_position"] = "candidate"
    raw = json.dumps(payload, indent=2).encode()
    root = make_bundle(
        tmp_path / "b",
        {"observations/a.json": raw},
        manifest_overrides={"artifact_position": "fixture_only"},
    )
    result = validate_bundle(root)
    assert codes(result) == ["BUNDLE_MANIFEST_PAYLOAD_DISAGREEMENT"]
    assert result.artifacts[0].contract is None


def test_manifest_cannot_upgrade_a_fixture_to_candidate_position(tmp_path: Path) -> None:
    root = bundle_from_fixture(
        tmp_path / "b",
        "p2_raw_count_without_denominator.json",
        manifest_overrides={"artifact_position": "candidate"},
    )
    assert codes(validate_bundle(root)) == ["BUNDLE_MANIFEST_PAYLOAD_DISAGREEMENT"]


def test_manifest_cannot_contradict_the_payload_identity(tmp_path: Path) -> None:
    """The payload's own artifact_id and schema_version are what the contract reads."""

    payload = json.loads(_fixture_path("p2_raw_count_without_denominator.json").read_text())
    payload["artifact_id"] = "rb_contact_evasion_observations_v1"
    raw = json.dumps(payload, indent=2).encode()
    root = make_bundle(tmp_path / "b", {"observations/a.json": raw})
    # The payload's own id no longer matches the committed schema's const, so the
    # shape gate stops it before the manifest can even be compared.
    assert codes(validate_bundle(root)) == ["BUNDLE_ARTIFACT_SCHEMA_INVALID"]


def test_promoted_position_still_fails_closed_through_the_gate(tmp_path: Path) -> None:
    """Slice A refuses promoted position outright, and the manifest cannot help."""

    payload = json.loads(_fixture_path("p2_raw_count_without_denominator.json").read_text())
    payload["artifact_position"] = "promoted"
    raw = json.dumps(payload, indent=2).encode()
    root = make_bundle(tmp_path / "b", {"observations/a.json": raw})
    result = validate_bundle(root)
    assert "PROMOTED_POSITION_REQUIRES_PROMOTION_GATE" in codes(result)
    assert bundle_codes(result) == [], "the refusal is Slice A's, not the manifest gate's"


# ---------------------------------------------------------------------------
# The decisive control: a self-consistent semantic tamper
# ---------------------------------------------------------------------------


def test_self_consistent_semantic_tamper_is_rejected_by_the_evaluator(tmp_path: Path) -> None:
    """Bytes and manifest digest updated together -- integrity is perfect.

    This is the case that proves the architecture: nothing about the manifest is
    wrong, so only the canonical semantic evaluator can refuse it, and it does,
    under Slice A's own code.
    """

    payload = json.loads(_fixture_path("p2_raw_count_without_denominator.json").read_text())
    payload["observations"][0]["identity"]["gsis_id"] = None
    payload["observations"][0]["identity"]["identity_resolution"] = "unresolved"
    raw = json.dumps(payload, indent=2).encode()
    root = make_bundle(tmp_path / "b", {"observations/a.json": raw})

    result = validate_bundle(root)
    assert codes(result) == ["CANONICAL_IDENTITY_UNRESOLVED"]
    assert bundle_codes(result) == [], "integrity metadata is entirely consistent here"

    (artifact,) = result.artifacts
    assert artifact.observed_digest == artifact.declared_digest
    assert artifact.observed_size == artifact.declared_size
    assert "integrity" in artifact.stages_passed
    assert "payload_shape" in artifact.stages_passed
    assert artifact.contract == {
        "valid": False,
        "shape_valid": True,
        "reason_codes": ["CANONICAL_IDENTITY_UNRESOLVED"],
    }


def test_second_self_consistent_semantic_tamper(tmp_path: Path) -> None:
    """A different rule, same lesson: consistent metadata is not validity."""

    payload = json.loads(_fixture_path("p1_complete_derived_explosiveness_rate.json").read_text())
    payload["observations"][0]["measurement"]["denominator"] = None
    raw = json.dumps(payload, indent=2).encode()
    root = make_bundle(tmp_path / "b", {"observations/a.json": raw})
    result = validate_bundle(root)
    assert bundle_codes(result) == []
    assert "RATE_MISSING_DENOMINATOR" in codes(result)


# ---------------------------------------------------------------------------
# Determinism, non-mutation, offline
# ---------------------------------------------------------------------------


def test_result_is_deterministic_across_runs(tmp_path: Path) -> None:
    root = bundle_from_fixture(tmp_path / "b", "n01_rate_missing_denominator.json")
    first = json.dumps(validate_bundle(root).as_dict(), sort_keys=True)
    second = json.dumps(validate_bundle(root).as_dict(), sort_keys=True)
    assert first == second


def test_machine_result_carries_no_absolute_path_or_clock(tmp_path: Path) -> None:
    """Two machines validating the same bytes must produce the same JSON."""

    root = bundle_from_fixture(tmp_path / "b", "n01_rate_missing_denominator.json")
    rendered = json.dumps(validate_bundle(root).as_dict(), sort_keys=True)
    assert str(tmp_path) not in rendered
    assert str(REPO_ROOT) not in rendered


def test_failures_are_ordered_deterministically(tmp_path: Path) -> None:
    files = {
        f"observations/{name}": _fixture_path(name).read_bytes()
        for name in (
            "n01_rate_missing_denominator.json",
            "n03_rushing_receiving_silently_combined.json",
        )
    }
    root = make_bundle(tmp_path / "b", files)
    result = validate_bundle(root)
    paths = [failure.path for failure in result.failures]
    assert paths == sorted(paths)


def test_gate_does_not_mutate_the_bundle(tmp_path: Path) -> None:
    root = bundle_from_fixture(tmp_path / "b", "p7_bucky_receipt_remains_partial.json")
    before = {
        path.relative_to(root).as_posix(): (
            hashlib.sha256(path.read_bytes()).hexdigest(),
            path.stat().st_mtime_ns,
        )
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }
    assert validate_bundle(root).ok
    after = {
        path.relative_to(root).as_posix(): (
            hashlib.sha256(path.read_bytes()).hexdigest(),
            path.stat().st_mtime_ns,
        )
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }
    assert before == after


def test_gate_does_not_mutate_committed_fixtures() -> None:
    before = {
        path.relative_to(REPO_ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(FIXTURE_ROOT.rglob("*.json"))
    }
    assert validate_bundle(REFERENCE_BUNDLE).ok
    after = {
        path.relative_to(REPO_ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(FIXTURE_ROOT.rglob("*.json"))
    }
    assert before == after


def test_gate_performs_no_network_access(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Any socket the gate itself opens raises, and the run still completes."""

    def refuse(*args, **kwargs):  # noqa: ANN002, ANN003
        raise AssertionError("the gate must not open a socket")

    monkeypatch.setattr(socket, "socket", refuse)
    monkeypatch.setattr(socket, "create_connection", refuse)
    root = bundle_from_fixture(tmp_path / "b", "p2_raw_count_without_denominator.json")
    assert validate_bundle(root).ok


def test_gate_and_bridge_sources_import_no_network_client() -> None:
    gate_source = GATE_SCRIPT.read_text()
    bridge_source = BRIDGE_SCRIPT.read_text()
    banned_gate_imports = (
        "import socket",
        "import urllib",
        "import http",
        "import requests",
        "import httpx",
    )
    for banned in banned_gate_imports:
        assert banned not in gate_source, banned
    for banned in ("node:http", "node:https", "node:net", "fetch(", "XMLHttpRequest"):
        assert banned not in bridge_source, banned


def test_bridge_holds_no_football_semantics() -> None:
    """The bridge must stay a pipe, not become a second authority."""

    source = BRIDGE_SCRIPT.read_text()
    for banned in (
        "mechanism",
        "denominator",
        "reason_code",
        "RATE_",
        "metric_id",
        "cohort",
        "gsis",
    ):
        assert banned not in source, banned
    # Imported, surface-checked, called. Nothing else in the file knows the name.
    assert source.count("evaluateRbContactEvasionObservationsV0") == 3, (
        "the bridge imports the canonical evaluator and calls it, nothing more"
    )


def test_gate_holds_no_football_semantics() -> None:
    """Slice B must not have re-implemented a single Slice A rule."""

    source = GATE_SCRIPT.read_text()
    for banned in (
        "contact_avoidance",
        "contact_survival",
        "explosiveness",
        "agility_change_of_direction",
        "forced_missed_tackles",
        "yards_after_contact",
        "minimum_eligible_opportunities",
        "RATE_MISSING_DENOMINATOR",
        "CANONICAL_IDENTITY_UNRESOLVED",
    ):
        assert banned not in source, banned


def test_gate_declares_no_score_or_ranking_surface() -> None:
    rendered = json.dumps(validate_bundle(REFERENCE_BUNDLE).as_dict())
    for banned in ("score", "grade", "ranking", "percentile", "tier", "elite", "rating"):
        assert banned not in rendered.lower(), banned


# ---------------------------------------------------------------------------
# CLI surface
# ---------------------------------------------------------------------------


def test_cli_exit_code_zero_on_pass(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    root = bundle_from_fixture(tmp_path / "b", "p2_raw_count_without_denominator.json")
    assert main([str(root)]) == 0
    assert "RESULT: PASS" in capsys.readouterr().out


def test_cli_exit_code_one_on_failure(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    root = bundle_from_fixture(tmp_path / "b", "n01_rate_missing_denominator.json")
    assert main([str(root)]) == 1
    out = capsys.readouterr().out
    assert "RESULT: FAIL" in out
    assert "RATE_MISSING_DENOMINATOR" in out


def test_cli_json_mode_emits_only_json(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    root = bundle_from_fixture(tmp_path / "b", "n01_rate_missing_denominator.json")
    assert main([str(root), "--json"]) == 1
    parsed = json.loads(capsys.readouterr().out)
    assert parsed["ok"] is False
    assert parsed["reason_codes"] == ["RATE_MISSING_DENOMINATOR"]
    assert parsed["gate"] == "rb_contact_evasion_observations_bundle_gate_v0"


def test_cli_json_out_writes_the_machine_result(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    root = bundle_from_fixture(tmp_path / "b", "p2_raw_count_without_denominator.json")
    out = tmp_path / "result.json"
    assert main([str(root), "--json-out", str(out)]) == 0
    capsys.readouterr()
    assert json.loads(out.read_text())["ok"] is True


def test_cli_refuses_to_write_inside_the_bundle(tmp_path: Path) -> None:
    """The gate never writes into what it validates."""

    root = bundle_from_fixture(tmp_path / "b", "p2_raw_count_without_denominator.json")
    with pytest.raises(GateUsageError):
        main([str(root), "--json-out", str(root / "result.json")])
    assert not (root / "result.json").exists()


def test_cli_subprocess_end_to_end(tmp_path: Path) -> None:
    """The documented invocation works as documented."""

    root = bundle_from_fixture(tmp_path / "b", "n11_canonical_identity_unresolved.json")
    completed = subprocess.run(
        [sys.executable, str(GATE_SCRIPT), str(root), "--json"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 1
    assert json.loads(completed.stdout)["reason_codes"] == ["CANONICAL_IDENTITY_UNRESOLVED"]


def test_cli_usage_error_exit_code(tmp_path: Path) -> None:
    root = bundle_from_fixture(tmp_path / "b", "p2_raw_count_without_denominator.json")
    completed = subprocess.run(
        [sys.executable, str(GATE_SCRIPT), str(root), "--json-out", str(root / "r.json")],
        cwd=str(REPO_ROOT),
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 2
    assert b"usage error" in completed.stderr


# ---------------------------------------------------------------------------
# Fail-closed when the canonical authority cannot be reached
# ---------------------------------------------------------------------------


def test_unbuildable_evaluator_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fresh_evaluator_cache
) -> None:
    """No evaluator, no pass. A missing authority is never a silent skip."""

    import scripts.validate_rb_contact_evasion_bundle as gate

    monkeypatch.setattr(gate, "EVALUATOR_TSCONFIG_PATH", tmp_path / "absent.tsconfig.json")
    root = bundle_from_fixture(tmp_path / "b", "p2_raw_count_without_denominator.json")
    result = gate.validate_bundle(root)
    assert not result.ok
    # One code, not two: the manifest-scoped identity failure already explains
    # why no artifact reached the semantic stage.
    assert codes(result) == ["BUNDLE_SEMANTIC_EVALUATOR_UNAVAILABLE"]
    assert all(artifact.contract is None for artifact in result.artifacts)
    assert result.evaluator is None, "no receipt is emitted when nothing was built"


def test_broken_bridge_fails_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import scripts.validate_rb_contact_evasion_bundle as gate

    broken = tmp_path / "broken_bridge.mjs"
    broken.write_text("process.exit(9);\n")
    monkeypatch.setattr(gate, "BRIDGE_PATH", broken)
    root = bundle_from_fixture(tmp_path / "b", "p2_raw_count_without_denominator.json")
    result = gate.validate_bundle(root)
    assert not result.ok
    assert "BUNDLE_SEMANTIC_EVALUATOR_UNAVAILABLE" in codes(result)


def test_bridge_returning_an_unreadable_report_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import scripts.validate_rb_contact_evasion_bundle as gate

    liar = tmp_path / "liar.mjs"
    liar.write_text(
        "const answer = process.argv[2] === 'constants'\n"
        f"  ? {{ok: true, artifact_id: {PINNED_ARTIFACT_ID!r},"
        f" schema_version: {PINNED_SCHEMA_VERSION!r}}}\n"
        "  : {ok: true, report: 'everything is fine'};\n"
        "console.log(JSON.stringify(answer));\n"
    )
    monkeypatch.setattr(gate, "BRIDGE_PATH", liar)
    root = bundle_from_fixture(tmp_path / "b", "p2_raw_count_without_denominator.json")
    result = gate.validate_bundle(root)
    assert not result.ok
    assert "BUNDLE_SEMANTIC_EVALUATOR_FAILED" in codes(result)


# ---------------------------------------------------------------------------
# Scope confirmations
# ---------------------------------------------------------------------------


def test_slice_b_wrote_nothing_under_exports() -> None:
    """Slice B creates no candidate or promoted artifact anywhere."""

    exports = REPO_ROOT / "exports"
    matches = [
        path.relative_to(REPO_ROOT).as_posix()
        for path in exports.rglob("*")
        if "rb_contact_evasion" in path.as_posix() or "contact_evasion" in path.name
    ]
    assert matches == []


def test_slice_b_did_not_modify_slice_a_contract_files() -> None:
    """The Slice A surface this gate depends on must be unmodified by this slice."""

    tracked = subprocess.run(
        ["git", "diff", "--name-only", "4498d5efd053e6bbc87f5f28214b0509550ad653", "--"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        check=False,
        text=True,
    )
    if tracked.returncode != 0:  # pragma: no cover - shallow clone or detached history
        pytest.skip("the authorized base commit is not reachable in this checkout")
    changed = {line for line in tracked.stdout.splitlines() if line}
    protected = {
        "src/contracts/v1/rbContactEvasionObservationsV0.ts",
        "schemas/rb_contact_evasion_observations_v0.schema.json",
        "docs/contracts/rb-contact-evasion-observations-v0.md",
        "test/rbContactEvasionObservationsV0.contract.test.ts",
        "tests/test_rb_contact_evasion_observations_v0.py",
    }
    protected |= {
        path.relative_to(REPO_ROOT).as_posix()
        for sub in ("positive", "negative")
        for path in (FIXTURE_ROOT / sub).glob("*.json")
    }
    assert changed & protected == set(), sorted(changed & protected)


def test_admitted_digest_algorithms_are_exactly_sha256() -> None:
    assert ADMITTED_DIGEST_ALGORITHMS == frozenset({"sha256"})


# ---------------------------------------------------------------------------
# Review repair 1: evaluator identity is established by build, never asserted
# ---------------------------------------------------------------------------
#
# Codex reproduced a fail-open at 0b48acf: a permissive module under the
# gitignored ``dist/`` exporting the correct artifact id and schema version made
# the gate return ok:true for the committed, shape-valid N11 fixture. Identity
# is now established by compiling the reviewed source, so a compiled module on
# disk -- stale, substituted or permissive -- is never consulted at all.


PERMISSIVE_MODULE = (
    'export const RB_CONTACT_EVASION_ARTIFACT_ID = "rb_contact_evasion_observations_v0";\n'
    'export const RB_CONTACT_EVASION_SCHEMA_VERSION = '
    '"rb_contact_evasion_observations_v0.4.0";\n'
    "export function evaluateRbContactEvasionObservationsV0() {\n"
    "  return { valid: true, shape_valid: true, violations: [], reason_codes: [] };\n"
    "}\n"
)


@pytest.fixture
def poisoned_dist():
    """Put a permissive compiled module where a build would normally sit.

    ``dist/`` is gitignored build output, never repository content, and the
    committed tree is untouched. It is restored by rebuilding afterwards.
    """

    dist_entry = REPO_ROOT / "dist/src/index.js"
    existed = dist_entry.exists()
    previous = dist_entry.read_bytes() if existed else None
    dist_entry.parent.mkdir(parents=True, exist_ok=True)
    dist_entry.write_text(PERMISSIVE_MODULE)
    try:
        yield dist_entry
    finally:
        if previous is not None:
            dist_entry.write_bytes(previous)
        else:
            dist_entry.unlink(missing_ok=True)


def test_permissive_substituted_compiled_module_is_never_consulted(
    tmp_path: Path, poisoned_dist: Path
) -> None:
    """The exact fail-open Codex reproduced, now closed.

    A module exporting the correct constants and calling everything valid is
    sitting on disk. N11 must still be rejected for its own reason code.
    """

    assert "valid: true" in poisoned_dist.read_text(), "the poison really is permissive"
    result = validate_bundle(
        bundle_from_fixture(tmp_path / "b", "n11_canonical_identity_unresolved.json")
    )
    assert not result.ok
    assert codes(result) == ["CANONICAL_IDENTITY_UNRESOLVED"]
    assert result.artifacts[0].contract == {
        "valid": False,
        "shape_valid": True,
        "reason_codes": ["CANONICAL_IDENTITY_UNRESOLVED"],
    }


def test_stale_compiled_module_with_correct_constants_is_never_consulted(
    tmp_path: Path, poisoned_dist: Path
) -> None:
    """A stale build cannot make a positive fixture pass for the wrong reason."""

    result = validate_bundle(
        bundle_from_fixture(tmp_path / "b", "p2_raw_count_without_denominator.json")
    )
    assert result.ok
    # The pass came from a fresh build of the reviewed source, and the receipt
    # names it -- not the module sitting in dist/.
    assert result.evaluator is not None
    assert result.evaluator["entry_source"] == EVALUATOR_ENTRY_SOURCE
    built = {entry["path"] for entry in result.evaluator["source_files"]}
    assert EVALUATOR_ENTRY_SOURCE in built
    assert result.evaluator["module_digest"] != hashlib.sha256(
        poisoned_dist.read_bytes()
    ).hexdigest()


def test_gate_never_reads_the_gitignored_build(tmp_path: Path) -> None:
    """Structural backstop: no code path in the gate or bridge opens dist/."""

    for source in (GATE_SCRIPT.read_text(), BRIDGE_SCRIPT.read_text()):
        code_lines = [
            line
            for line in source.splitlines()
            if "dist" in line
            and not line.lstrip().startswith(("#", "*", "//"))
            and "``dist" not in line
        ]
        assert code_lines == [], code_lines


def test_receipt_records_the_compiled_source_surface() -> None:
    """The receipt says exactly what was hashed, and is stable across runs."""

    build, error = ensure_evaluator()
    assert error is None and build is not None
    receipt = build.receipt()

    paths = [entry["path"] for entry in receipt["source_files"]]
    assert EVALUATOR_ENTRY_SOURCE in paths
    for required in (
        "tsconfig.json",
        "scripts/rb_contact_evasion_evaluator.tsconfig.json",
        "package.json",
        "package-lock.json",
    ):
        assert required in paths, required
    assert paths == sorted(paths)
    assert all(len(entry["sha256"]) == 64 for entry in receipt["source_files"])
    assert len(receipt["source_fingerprint"]) == 64
    assert len(receipt["module_digest"]) == 64
    assert [pin["name"] for pin in receipt["dependency_pins"]] == ["zod"]

    # Repo-relative only: two machines validating one source must agree.
    assert str(REPO_ROOT) not in json.dumps(receipt)


def test_receipt_matches_the_committed_contract_source() -> None:
    """The hash in the receipt is the hash of the file a reviewer can read."""

    build, _ = ensure_evaluator()
    assert build is not None
    recorded = {entry[0]: entry[1] for entry in build.source_files}
    on_disk = hashlib.sha256((REPO_ROOT / EVALUATOR_ENTRY_SOURCE).read_bytes()).hexdigest()
    assert recorded[EVALUATOR_ENTRY_SOURCE] == on_disk


def _isolated_repo(tmp_path: Path, contract_source: str) -> Path:
    """A minimal repository copy whose contract source has been modified.

    The committed contract is never touched: everything here is a copy, and the
    modification exists only to prove the verdict follows the source that was
    compiled rather than any build lying around.
    """

    root = tmp_path / "repo"
    (root / "src/contracts/v1").mkdir(parents=True)
    (root / "scripts").mkdir()
    (root / "schemas").mkdir()
    (root / "dist/src").mkdir(parents=True)

    for relative in (
        "tsconfig.json",
        "package.json",
        "package-lock.json",
        "scripts/validate_rb_contact_evasion_bundle.py",
        "scripts/rb_contact_evasion_contract_bridge.mjs",
        "scripts/rb_contact_evasion_evaluator.tsconfig.json",
        "schemas/rb_contact_evasion_observations_v0.schema.json",
        "schemas/rb_contact_evasion_observations_bundle_manifest_v0.schema.json",
    ):
        (root / relative).write_bytes((REPO_ROOT / relative).read_bytes())

    (root / EVALUATOR_ENTRY_SOURCE).write_text(contract_source)
    os.symlink(REPO_ROOT / "node_modules", root / "node_modules", target_is_directory=True)
    # A stale, correct-constants build already sitting where dist/ would be.
    (root / "dist/src/index.js").write_text(PERMISSIVE_MODULE)
    return root


def _run_isolated_gate(root: Path, bundle: Path) -> dict:
    completed = subprocess.run(
        [sys.executable, str(root / "scripts/validate_rb_contact_evasion_bundle.py"),
         str(bundle), "--json"],
        cwd=str(root),
        capture_output=True,
        check=False,
    )
    assert completed.stdout, completed.stderr.decode()
    return json.loads(completed.stdout)


def test_modified_contract_source_changes_the_verdict_despite_a_stale_build(
    tmp_path: Path,
) -> None:
    """Control 3: modified canonical source, unchanged existing dist.

    The isolated copy carries a permissive ``dist/`` *and* a contract whose
    declared schema version has been altered. If the gate were trusting the
    build on disk it would report the pinned version and pass; instead it
    reports drift, which can only come from compiling the modified source.
    """

    source = (REPO_ROOT / EVALUATOR_ENTRY_SOURCE).read_text()
    altered = source.replace(
        "'rb_contact_evasion_observations_v0.4.0'",
        "'rb_contact_evasion_observations_v0.9.9-modified'",
    )
    assert altered != source

    root = _isolated_repo(tmp_path, altered)
    bundle = make_bundle(
        tmp_path / "bundle",
        {
            "observations/a.json": _fixture_path(
                "p2_raw_count_without_denominator.json"
            ).read_bytes()
        },
    )
    result = _run_isolated_gate(root, bundle)
    assert result["ok"] is False
    assert "BUNDLE_CONTRACT_IDENTITY_DRIFT" in result["reason_codes"]
    assert any(
        "0.9.9-modified" in failure["detail"] for failure in result["failures"]
    ), result["failures"]


def test_modified_contract_behaviour_changes_the_verdict_despite_a_stale_build(
    tmp_path: Path,
) -> None:
    """Control 3, behavioural half: a source edit changes what is accepted.

    Again in an isolated copy with a permissive ``dist/``. The edit inverts one
    existing guard, so the normally-valid ``fixture_only`` P2 fixture is refused
    instead of ``promoted``. If the stale build were being used, P2 would pass.
    """

    source = (REPO_ROOT / EVALUATOR_ENTRY_SOURCE).read_text()
    altered = source.replace(
        "if (artifact.artifact_position === 'promoted') {",
        "if (artifact.artifact_position !== 'promoted') {",
    )
    assert altered != source

    root = _isolated_repo(tmp_path, altered)
    bundle = make_bundle(
        tmp_path / "bundle",
        {
            "observations/a.json": _fixture_path(
                "p2_raw_count_without_denominator.json"
            ).read_bytes()
        },
    )
    result = _run_isolated_gate(root, bundle)
    assert result["ok"] is False
    assert result["reason_codes"] == ["PROMOTED_POSITION_REQUIRES_PROMOTION_GATE"]


def test_correctly_rebuilt_current_evaluator_passes(tmp_path: Path) -> None:
    """Control 4: an unmodified isolated copy reproduces the committed verdicts."""

    root = _isolated_repo(tmp_path, (REPO_ROOT / EVALUATOR_ENTRY_SOURCE).read_text())
    positive = make_bundle(
        tmp_path / "pos",
        {
            "observations/a.json": _fixture_path(
                "p2_raw_count_without_denominator.json"
            ).read_bytes()
        },
    )
    assert _run_isolated_gate(root, positive)["ok"] is True

    negative = make_bundle(
        tmp_path / "neg",
        {
            "observations/a.json": _fixture_path(
                "n11_canonical_identity_unresolved.json"
            ).read_bytes()
        },
    )
    rejected = _run_isolated_gate(root, negative)
    assert rejected["ok"] is False
    assert rejected["reason_codes"] == ["CANONICAL_IDENTITY_UNRESOLVED"]


def test_build_failure_fails_closed(tmp_path: Path, fresh_evaluator_cache) -> None:
    """Control 5: a contract source that does not compile yields no verdict."""

    broken_source = tmp_path / "broken"
    (broken_source / "src/contracts/v1").mkdir(parents=True)
    (broken_source / EVALUATOR_ENTRY_SOURCE).write_text(
        "export const oops: number = 'not a number';\n"
    )
    tsconfig = tmp_path / "broken.tsconfig.json"
    tsconfig.write_text(
        json.dumps(
            {
                "extends": str(REPO_ROOT / "tsconfig.json"),
                "compilerOptions": {"declaration": False, "rootDir": str(broken_source)},
                "files": [str(broken_source / EVALUATOR_ENTRY_SOURCE)],
                "include": [],
            }
        )
    )
    build, error = build_evaluator(tsconfig_path=tsconfig, repo_root=broken_source)
    assert build is None
    assert error is not None
    assert error["error"] in {"evaluator_build_failed", "evaluator_source_unreadable"}


def test_missing_build_surface_fails_closed(tmp_path: Path) -> None:
    build, error = build_evaluator(tsconfig_path=tmp_path / "nope.json")
    assert build is None
    assert error is not None and error["error"] == "evaluator_tsconfig_missing"


def test_bridge_refuses_a_module_that_does_not_match_its_digest(tmp_path: Path) -> None:
    """The bridge re-hashes before importing, closing the build-to-import window."""

    module = tmp_path / "module.mjs"
    module.write_text(PERMISSIVE_MODULE)
    completed = subprocess.run(
        [
            "node",
            str(BRIDGE_SCRIPT),
            "constants",
            str(module),
            "0" * 64,
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        check=False,
    )
    answer = json.loads(completed.stdout.decode().strip().splitlines()[-1])
    assert answer["ok"] is False
    assert answer["error"] == "compiled_module_tampered"


def test_bridge_requires_a_module_and_a_digest() -> None:
    completed = subprocess.run(
        ["node", str(BRIDGE_SCRIPT), "constants"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        check=False,
    )
    answer = json.loads(completed.stdout.decode().strip().splitlines()[-1])
    assert answer["ok"] is False
    assert answer["error"] == "usage"


def test_barrel_and_module_expose_the_same_evaluator(tmp_path: Path) -> None:
    """The narrowed build surface is still Slice A's public evaluator.

    The gate compiles the module that *defines* the evaluator rather than the
    ``src/index.ts`` barrel. This proves the barrel is a re-export of exactly
    that function, so nothing about which surface is "public" changed.

    Compiled into a temporary directory on purpose: this test must not depend on
    -- or be fooled by -- whatever happens to be sitting in the gitignored
    ``dist/``.
    """

    barrel = (REPO_ROOT / "src/index.ts").read_text()
    contracts_barrel = (REPO_ROOT / "src/contracts/v1/index.ts").read_text()
    assert "export * from './contracts/v1/index.js';" in barrel
    assert "export * from './rbContactEvasionObservationsV0.js';" in contracts_barrel

    out = tmp_path / "out"
    tsconfig = tmp_path / "barrel.tsconfig.json"
    tsconfig.write_text(
        json.dumps(
            {
                "extends": str(REPO_ROOT / "tsconfig.json"),
                "compilerOptions": {
                    "declaration": False,
                    "outDir": str(out),
                    # The tsconfig lives outside the repo, so ambient @types
                    # would not resolve from here.
                    "typeRoots": [str(REPO_ROOT / "node_modules/@types")],
                },
                "files": [str(REPO_ROOT / "src/index.ts")],
                "include": [],
            }
        )
    )
    built = subprocess.run(
        ["npx", "tsc", "-p", str(tsconfig)],
        cwd=str(REPO_ROOT),
        capture_output=True,
        check=False,
    )
    assert built.returncode == 0, built.stdout.decode()[-2000:]

    os.symlink(REPO_ROOT / "node_modules", out / "node_modules", target_is_directory=True)
    (out / "package.json").write_text('{"type": "module"}\n')

    completed = subprocess.run(
        [
            "node",
            "--input-type=module",
            "-e",
            "const a = await import('./src/index.js');"
            "const b = await import('./src/contracts/v1/"
            "rbContactEvasionObservationsV0.js');"
            "console.log(a.evaluateRbContactEvasionObservationsV0 === "
            "b.evaluateRbContactEvasionObservationsV0);",
        ],
        cwd=str(out),
        capture_output=True,
        check=False,
    )
    assert completed.stdout.decode().strip() == "true", completed.stderr.decode()


# ---------------------------------------------------------------------------
# Review repair 2: an invalid verdict can never produce a passing bundle
# ---------------------------------------------------------------------------
#
# Codex reproduced a fail-open at 0b48acf: a report of
# {"valid": false, "reason_codes": [...], "violations": []} recorded
# contract.valid=false on the artifact, appended nothing to the failure list,
# and the gate computed ok = not failures -> true.


def _report_bundle(tmp_path: Path, report, monkeypatch) -> object:
    """Run a real bundle against a bridge that returns a chosen report."""

    import scripts.validate_rb_contact_evasion_bundle as gate

    liar = tmp_path / "liar.mjs"
    liar.write_text(
        "const answer = process.argv[2] === 'constants'\n"
        f"  ? {{ok: true, artifact_id: {PINNED_ARTIFACT_ID!r},"
        f" schema_version: {PINNED_SCHEMA_VERSION!r}}}\n"
        f"  : {{ok: true, report: {json.dumps(report)}}};\n"
        "console.log(JSON.stringify(answer));\n"
    )
    monkeypatch.setattr(gate, "BRIDGE_PATH", liar)
    root = bundle_from_fixture(tmp_path / "b", "p2_raw_count_without_denominator.json")
    return gate.validate_bundle(root)


VIOLATION = {
    "reason_code": "CANONICAL_IDENTITY_UNRESOLVED",
    "path": "observations[0]",
    "detail": "d",
}

CONTRADICTORY_REPORTS = {
    # The exact report Codex used.
    "invalid_with_no_violations": {
        "valid": False,
        "shape_valid": True,
        "reason_codes": ["CANONICAL_IDENTITY_UNRESOLVED"],
        "violations": [],
    },
    "invalid_with_no_codes_and_no_violations": {
        "valid": False,
        "shape_valid": True,
        "reason_codes": [],
        "violations": [],
    },
    "invalid_with_violations_but_no_codes": {
        "valid": False,
        "shape_valid": True,
        "reason_codes": [],
        "violations": [VIOLATION],
    },
    "valid_string": {
        "valid": "false",
        "shape_valid": True,
        "reason_codes": [],
        "violations": [],
    },
    "valid_numeric_falsy": {"valid": 0, "shape_valid": True, "reason_codes": [], "violations": []},
    "valid_numeric_truthy": {"valid": 1, "shape_valid": True, "reason_codes": [], "violations": []},
    "shape_valid_not_boolean": {
        "valid": True,
        "shape_valid": 1,
        "reason_codes": [],
        "violations": [],
    },
    "valid_with_violations": {
        "valid": True,
        "shape_valid": True,
        "reason_codes": ["CANONICAL_IDENTITY_UNRESOLVED"],
        "violations": [VIOLATION],
    },
    "valid_with_reason_codes": {
        "valid": True,
        "shape_valid": True,
        "reason_codes": ["CANONICAL_IDENTITY_UNRESOLVED"],
        "violations": [],
    },
    "codes_disagree_with_violations": {
        "valid": False,
        "shape_valid": True,
        "reason_codes": ["MINIMUM_SAMPLE_NOT_MET_RATE_EMITTED"],
        "violations": [VIOLATION],
    },
    "malformed_violation_entry": {
        "valid": False,
        "shape_valid": True,
        "reason_codes": ["CANONICAL_IDENTITY_UNRESOLVED"],
        "violations": ["CANONICAL_IDENTITY_UNRESOLVED"],
    },
    "violation_missing_detail": {
        "valid": False,
        "shape_valid": True,
        "reason_codes": ["CANONICAL_IDENTITY_UNRESOLVED"],
        "violations": [{"reason_code": "CANONICAL_IDENTITY_UNRESOLVED", "path": "p"}],
    },
    "violation_code_not_a_string": {
        "valid": False,
        "shape_valid": True,
        "reason_codes": ["CANONICAL_IDENTITY_UNRESOLVED"],
        "violations": [{"reason_code": 7, "path": "p", "detail": "d"}],
    },
    "reason_codes_not_a_list": {
        "valid": False,
        "shape_valid": True,
        "reason_codes": "CANONICAL_IDENTITY_UNRESOLVED",
        "violations": [VIOLATION],
    },
    "duplicate_reason_codes": {
        "valid": False,
        "shape_valid": True,
        "reason_codes": ["CANONICAL_IDENTITY_UNRESOLVED", "CANONICAL_IDENTITY_UNRESOLVED"],
        "violations": [VIOLATION],
    },
    "unparseable_but_valid": {
        "valid": True,
        "shape_valid": False,
        "reason_codes": [],
        "violations": [],
    },
    "unexpected_extra_key": {
        "valid": True,
        "shape_valid": True,
        "reason_codes": [],
        "violations": [],
        "override": True,
    },
    "missing_key": {"valid": True, "shape_valid": True, "reason_codes": []},
    "not_an_object": "everything is fine",
}


@pytest.mark.parametrize("label", sorted(CONTRADICTORY_REPORTS))
def test_contradictory_evaluator_report_never_passes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, label: str
) -> None:
    """Every malformed or self-contradictory verdict fails closed, with one code."""

    result = _report_bundle(tmp_path, CONTRADICTORY_REPORTS[label], monkeypatch)
    assert not result.ok, label
    assert codes(result) == ["BUNDLE_SEMANTIC_EVALUATOR_FAILED"], label
    assert result.artifacts[0].contract is None, label
    assert "semantic" not in result.artifacts[0].stages_passed, label


@pytest.mark.parametrize("label", sorted(CONTRADICTORY_REPORTS))
def test_parse_evaluator_report_rejects_each_contradiction(label: str) -> None:
    """The envelope check is the thing doing it, and it explains itself."""

    report, reason = parse_evaluator_report(CONTRADICTORY_REPORTS[label])
    assert report is None, label
    assert isinstance(reason, str) and reason, label


def test_parse_evaluator_report_accepts_a_real_rejection() -> None:
    """Slice A's own negative report shape is untouched by the new strictness."""

    report, reason = parse_evaluator_report(
        {
            "valid": False,
            "shape_valid": True,
            "reason_codes": ["CANONICAL_IDENTITY_UNRESOLVED"],
            "violations": [VIOLATION],
        }
    )
    assert reason is None
    assert report is not None and report["valid"] is False


def test_parse_evaluator_report_accepts_a_real_acceptance() -> None:
    report, reason = parse_evaluator_report(
        {"valid": True, "shape_valid": True, "reason_codes": [], "violations": []}
    )
    assert reason is None
    assert report is not None and report["valid"] is True


def test_parse_evaluator_report_accepts_a_shape_failure() -> None:
    """Slice A reports shape_valid:false with SCHEMA_SHAPE_INVALID; still admitted."""

    report, reason = parse_evaluator_report(
        {
            "valid": False,
            "shape_valid": False,
            "reason_codes": ["SCHEMA_SHAPE_INVALID"],
            "violations": [
                {"reason_code": "SCHEMA_SHAPE_INVALID", "path": "<root>", "detail": "d"}
            ],
        }
    )
    assert reason is None
    assert report is not None


def test_every_real_slice_a_report_is_admitted_by_the_envelope_check(tmp_path: Path) -> None:
    """The corpus is the regression: no committed fixture's verdict is refused."""

    for name in [*POSITIVE_FIXTURES, *sorted(NEGATIVE_FIXTURES)]:
        result = validate_bundle(bundle_from_fixture(tmp_path / name, name))
        assert "BUNDLE_SEMANTIC_EVALUATOR_FAILED" not in codes(result), name
        assert result.artifacts[0].contract is not None, name


def test_blocked_artifact_without_a_recorded_failure_cannot_pass(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The closing sweep: an unexplained block is itself a failure.

    ``evaluate_semantics`` is replaced by one that silently blocks without
    recording anything -- the shape of any future bug that forgets a failure.
    The bundle must not pass.
    """

    import scripts.validate_rb_contact_evasion_bundle as gate

    def silent_block(artifacts, failures):
        for artifact in artifacts:
            artifact.block()

    monkeypatch.setattr(gate, "evaluate_semantics", silent_block)
    root = bundle_from_fixture(tmp_path / "b", "p2_raw_count_without_denominator.json")
    result = gate.validate_bundle(root)
    assert not result.ok
    assert codes(result) == ["BUNDLE_SEMANTIC_EVALUATOR_FAILED"]


def test_success_requires_every_artifact_to_complete_the_semantic_stage(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An empty failure list alone is never enough to report a pass."""

    import scripts.validate_rb_contact_evasion_bundle as gate

    def do_nothing(artifacts, failures):
        return None

    monkeypatch.setattr(gate, "evaluate_semantics", do_nothing)
    root = bundle_from_fixture(tmp_path / "b", "p2_raw_count_without_denominator.json")
    result = gate.validate_bundle(root)
    assert not result.ok
    assert all("semantic" not in a.stages_passed for a in result.artifacts)


def test_module_swapped_after_the_build_forces_a_rebuild(fresh_evaluator_cache) -> None:
    """The per-process memo is re-checked, not assumed.

    Overwriting the module the gate built -- the shape of a swap between one
    validation and the next -- must not be reused. The memo is discarded and the
    source is compiled again.
    """

    first, error = ensure_evaluator()
    assert error is None and first is not None
    assert REPO_ROOT not in first.module_path.parents, (
        "the gate must build into a private directory outside the repository; "
        f"it built into {first.module_path}"
    )
    original_digest = first.module_digest
    original_bytes = first.module_path.read_bytes()

    first.module_path.write_text(PERMISSIVE_MODULE)
    assert first.module_path.read_bytes() != original_bytes

    second, error = ensure_evaluator()
    assert error is None and second is not None
    # Rebuilt from the same unchanged source, so the digest is reproduced, and
    # the permissive bytes are gone.
    assert second.module_digest == original_digest
    assert second.source_fingerprint == first.source_fingerprint
    assert second.module_path.read_bytes() != PERMISSIVE_MODULE.encode()


def test_swapped_module_cannot_deliver_a_verdict(tmp_path: Path, fresh_evaluator_cache) -> None:
    """End to end: a swapped module never yields a passing N11."""

    build, _ = ensure_evaluator()
    assert build is not None
    assert REPO_ROOT not in build.module_path.parents, (
        "refusing to tamper with a module inside the repository; "
        f"the gate built into {build.module_path}"
    )
    build.module_path.write_text(PERMISSIVE_MODULE)

    result = validate_bundle(
        bundle_from_fixture(tmp_path / "b", "n11_canonical_identity_unresolved.json")
    )
    assert not result.ok
    assert codes(result) == ["CANONICAL_IDENTITY_UNRESOLVED"]


def test_build_surface_that_omits_the_contract_is_refused(tmp_path: Path) -> None:
    """A build that never compiled the canonical contract is not an evaluator.

    Without this check a tsconfig pointing anywhere else would still produce a
    "build", and the gate would run whatever it emitted.
    """

    other = tmp_path / "elsewhere"
    (other / "src/contracts/v1").mkdir(parents=True)
    decoy = other / "src/contracts/v1/decoy.ts"
    decoy.write_text("export const unrelated = 1;\n")
    tsconfig = tmp_path / "decoy.tsconfig.json"
    tsconfig.write_text(
        json.dumps(
            {
                "extends": str(REPO_ROOT / "tsconfig.json"),
                "compilerOptions": {
                    "declaration": False,
                    "rootDir": str(other),
                    "typeRoots": [str(REPO_ROOT / "node_modules/@types")],
                },
                "files": [str(decoy)],
                "include": [],
            }
        )
    )
    build, error = build_evaluator(tsconfig_path=tsconfig, repo_root=other)
    assert build is None
    assert error is not None and error["error"] in {
        "evaluator_entry_not_compiled",
        "evaluator_build_incomplete",
    }


def test_a_bundle_declaring_no_artifact_can_never_pass(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Success requires artifacts, not merely an empty failure list.

    The committed manifest schema already refuses an empty ``artifacts`` list, so
    this bypasses the shape gate to reach the condition underneath it: if that
    schema were ever widened, a bundle validating nothing must still not pass.
    """

    import scripts.validate_rb_contact_evasion_bundle as gate

    monkeypatch.setattr(gate, "check_manifest_shape", lambda manifest, failures: True)
    root = make_bundle(tmp_path / "b", {}, artifacts_override=[])
    result = gate.validate_bundle(root)
    assert result.artifacts == []
    assert not result.ok, "a bundle that validated nothing is not a bundle that passed"


def test_backstop_holds_if_the_envelope_check_ever_admits_a_rejection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Layering, proven: the two guards on an invalid verdict are independent.

    ``parse_evaluator_report`` normally refuses a rejection that names no
    violation. Here it is replaced by one that admits it -- the shape of a future
    weakening of that check -- and the gate must still refuse the bundle rather
    than record ``valid: false`` and report a pass, which is the exact fail-open
    the review found.
    """

    import scripts.validate_rb_contact_evasion_bundle as gate

    monkeypatch.setattr(gate, "parse_evaluator_report", lambda report: (report, None))
    result = _report_bundle(
        tmp_path,
        {
            "valid": False,
            "shape_valid": True,
            "reason_codes": ["CANONICAL_IDENTITY_UNRESOLVED"],
            "violations": [],
        },
        monkeypatch,
    )
    assert not result.ok
    assert codes(result) == ["BUNDLE_SEMANTIC_EVALUATOR_FAILED"]

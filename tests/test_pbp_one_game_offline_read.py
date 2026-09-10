"""Synthetic-fixture tests for the offline one-game PBP reader (Research #22 first PR).

Every fixture here is fictional and clearly labeled SYNTHETIC. Team codes `SYA`/`SYB`,
season 1999, and `SYN_` game IDs cannot be mistaken for any real game. No row is
reconstructed from the operator's personal film chart. No network or database access.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import polars as pl
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.pbp_one_game import offline_read as mod  # noqa: E402

SYN_GAME_ID = "SYN_1999_01_SYB_SYA"
SYN_DATE = "1999-01-01"
SYN_SEASON = 1999
HOME, AWAY = "SYA", "SYB"
REQ = mod.GameRequest(season=SYN_SEASON, game_date=SYN_DATE, away_team=AWAY, home_team=HOME)


def play(
    play_id: float, posteam: str | None, drive: float | None, **overrides: Any
) -> dict[str, Any]:
    base: dict[str, Any] = {
        "game_id": SYN_GAME_ID,
        "play_id": play_id,
        "season": SYN_SEASON,
        "week": 1,
        "season_type": "REG",
        "game_date": SYN_DATE,
        "home_team": HOME,
        "away_team": AWAY,
        "posteam": posteam,
        "defteam": None if posteam is None else (AWAY if posteam == HOME else HOME),
        "drive": drive,
        "fixed_drive": drive,
        "qtr": 1,
        "time": "15:00",
        "quarter_seconds_remaining": 900.0,
        "down": 1.0,
        "ydstogo": 10.0,
        "yardline_100": 75.0,
        "play_type": "run",
        "desc": f"SYNTHETIC play {play_id}",
        "yards_gained": 3.0,
        "penalty": 0.0,
        "penalty_team": None,
        "play_deleted": 0.0,
        "shotgun": 0.0,
        "passer_player_id": None,
        "rusher_player_id": "SYN-0001",
        "receiver_player_id": None,
        "offense_personnel": None,
        "epa": 0.0,
    }
    base.update(overrides)
    return base


def alternating_game(possessions: list[tuple[str, float, int]]) -> list[dict[str, Any]]:
    """possessions: (posteam, provider_drive, play_count) in game order."""
    rows: list[dict[str, Any]] = []
    play_id = 1.0
    for posteam, drive, count in possessions:
        for _ in range(count):
            rows.append(play(play_id, posteam, drive))
            play_id += 1
    return rows


DEFAULT_POSSESSIONS = [
    (AWAY, 1.0, 3), (HOME, 2.0, 4), (AWAY, 3.0, 2), (HOME, 4.0, 5), (AWAY, 5.0, 3),
]


def write_parquet(
    tmp_path: Path, rows: list[dict[str, Any]], name: str = "synthetic.parquet"
) -> Path:
    path = tmp_path / name
    pl.DataFrame(rows).write_parquet(path)
    return path


def receipt_args(path: Path) -> dict[str, Any]:
    content = path.read_bytes()
    return {
        "path": path,
        "expected_bytes": len(content),
        "expected_sha256": hashlib.sha256(content).hexdigest(),
    }


def run(path: Path, *, possession: mod.PossessionRequest | None = None, request=REQ, **kw):
    return mod.read_one_game(**receipt_args(path), request=request, possession=possession, **kw)


# ---------------------------------------------------------------------------
# Receipt verification: reject before parsing, no side effects
# ---------------------------------------------------------------------------


def test_missing_input_rejected_before_parse(tmp_path, monkeypatch):
    monkeypatch.setattr(pl, "read_parquet", lambda *a, **k: pytest.fail("parsed"))
    monkeypatch.setattr(pl, "read_parquet_schema", lambda *a, **k: pytest.fail("parsed"))
    result = mod.read_one_game(
        path=tmp_path / "absent.parquet", expected_bytes=1, expected_sha256="00" * 32, request=REQ
    )
    assert result["status"] == "rejected"
    assert result["rejection"]["reason"] == "missing_input"
    assert result["rejection"]["parsed"] is False
    assert result["receipt"]["source"]["actual_sha256"] is None
    assert result["game"] is None and result["events"] is None
    assert list(tmp_path.iterdir()) == []


def test_wrong_digest_rejected_before_parse(tmp_path, monkeypatch):
    path = write_parquet(tmp_path, alternating_game(DEFAULT_POSSESSIONS))
    args = receipt_args(path)
    monkeypatch.setattr(pl, "read_parquet", lambda *a, **k: pytest.fail("parsed"))
    monkeypatch.setattr(pl, "read_parquet_schema", lambda *a, **k: pytest.fail("parsed"))
    result = mod.read_one_game(
        path=path, expected_bytes=args["expected_bytes"], expected_sha256="ab" * 32, request=REQ
    )
    assert result["status"] == "rejected"
    assert result["rejection"]["reason"] == "sha256_mismatch"
    assert result["receipt"]["source"]["actual_sha256"] == args["expected_sha256"]
    assert result["receipt"]["source"]["receipt_status"] == "rejected"


def test_wrong_byte_count_rejected(tmp_path):
    path = write_parquet(tmp_path, alternating_game(DEFAULT_POSSESSIONS))
    args = receipt_args(path)
    result = mod.read_one_game(
        path=path,
        expected_bytes=args["expected_bytes"] + 1,
        expected_sha256=args["expected_sha256"],
        request=REQ,
    )
    assert result["rejection"]["reason"] == "byte_count_mismatch"


def test_unsupported_format_rejected_even_with_matching_digest(tmp_path):
    path = tmp_path / "not_parquet.parquet"
    path.write_bytes(b"game_id,play_id\nSYN,1\n")
    result = mod.read_one_game(**receipt_args(path), request=REQ)
    assert result["status"] == "rejected"
    assert result["rejection"]["reason"] == "unsupported_format"
    assert result["receipt"]["source"]["format_detected"] == "unsupported"


def test_verified_receipt_records_exact_bytes_and_reader_revision(tmp_path):
    path = write_parquet(tmp_path, alternating_game(DEFAULT_POSSESSIONS))
    args = receipt_args(path)
    result = run(path)
    source = result["receipt"]["source"]
    assert source["receipt_status"] == "verified"
    assert source["actual_bytes"] == args["expected_bytes"]
    assert source["actual_sha256"] == args["expected_sha256"]
    assert source["format_detected"] == "parquet"
    reader = result["receipt"]["reader"]
    assert reader["version"] == mod.READER_VERSION
    assert reader["code_sha256"] == hashlib.sha256(Path(mod.__file__).read_bytes()).hexdigest()


# ---------------------------------------------------------------------------
# Game identity: no certified game without exact identity, no silent fallback
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "request_",
    [
        mod.GameRequest(season=SYN_SEASON, game_date=SYN_DATE, away_team=HOME, home_team=AWAY),
        mod.GameRequest(season=SYN_SEASON, game_date="1999-01-02", away_team=AWAY, home_team=HOME),
        mod.GameRequest(season=2000, game_date=SYN_DATE, away_team=AWAY, home_team=HOME),
        mod.GameRequest(season=2026, game_date="2026-09-09", away_team="NE", home_team="SEA"),
    ],
    ids=[
        "swapped_home_away", "wrong_date", "wrong_season", "real_target_request_not_in_fixture",
    ],
)
def test_wrong_identity_is_unresolved_not_substituted(tmp_path, request_):
    path = write_parquet(tmp_path, alternating_game(DEFAULT_POSSESSIONS))
    result = run(path, request=request_, possession=mod.PossessionRequest(HOME, 2))
    assert result["status"] == "unresolved"
    assert result["game"]["status"] == "unresolved"
    assert result["game"]["reason"] == "no_matching_game"
    assert result["game"]["observed"] is None
    assert result["inventory"] is None and result["events"] is None
    assert result["receipt"]["source"]["receipt_status"] == "verified"


def test_swapped_orientation_is_reported_as_diagnostic_only(tmp_path):
    path = write_parquet(tmp_path, alternating_game(DEFAULT_POSSESSIONS))
    swapped = mod.GameRequest(
        season=SYN_SEASON, game_date=SYN_DATE, away_team=HOME, home_team=AWAY
    )
    result = run(path, request=swapped)
    assert result["game"]["reason"] == "no_matching_game"
    assert result["game"]["diagnostics"]["swapped_home_away_on_requested_date"] == 1


def test_ambiguous_date_within_one_game_is_conflicting_metadata(tmp_path):
    rows = alternating_game(DEFAULT_POSSESSIONS)
    rows[-1]["game_date"] = "1999-01-02"
    path = write_parquet(tmp_path, rows)
    result = run(path)
    assert result["status"] == "unresolved"
    assert result["game"]["reason"] == "conflicting_game_metadata"
    assert len(result["game"]["diagnostics"]["conflicting_identity_tuples"]) == 2


def test_multiple_matching_games_is_unresolved(tmp_path):
    rows = alternating_game(DEFAULT_POSSESSIONS)
    twin = [dict(r, game_id="SYN_1999_01_SYB_SYA_TWIN") for r in rows]
    path = write_parquet(tmp_path, rows + twin)
    result = run(path)
    assert result["game"]["reason"] == "multiple_matching_games"
    assert result["game"]["diagnostics"]["matching_game_ids"] == [
        SYN_GAME_ID, "SYN_1999_01_SYB_SYA_TWIN"
    ]


def test_missing_identity_column_prevents_certification(tmp_path):
    rows = [
        {k: v for k, v in r.items() if k != "home_team"}
        for r in alternating_game(DEFAULT_POSSESSIONS)
    ]
    path = write_parquet(tmp_path, rows)
    result = run(path)
    assert result["game"]["reason"] == "missing_game_identity_columns"
    assert result["game"]["diagnostics"]["missing_columns"] == ["home_team"]


def test_matched_game_preserves_raw_identity_and_only_scans_identity_columns(tmp_path):
    rows = alternating_game(DEFAULT_POSSESSIONS)
    other = [
        dict(r, game_id="SYN_1999_01_SYC_SYD", home_team="SYD", away_team="SYC") for r in rows
    ]
    path = write_parquet(tmp_path, rows + other)
    result = run(path)
    assert result["status"] == "read"
    observed = result["game"]["observed"]
    assert observed["game_id"] == SYN_GAME_ID
    assert observed["home_team"] == HOME and observed["away_team"] == AWAY
    assert observed["game_date"] == SYN_DATE
    assert result["game"]["date_match_basis"] == "string_exact"
    scanned = set(result["game"]["selection_scan"]["columns_scanned"])
    assert scanned <= set(mod.GAME_IDENTITY_COLUMNS)
    assert result["inventory"]["keys"]["row_count"] == len(rows)
    assert result["game"]["diagnostics"]["distinct_identity_tuples_scanned"] == 2


def test_request_team_canonicalization_preserves_raw_source_value(tmp_path):
    rows = [dict(r, home_team="LA") for r in alternating_game(DEFAULT_POSSESSIONS)]
    for r in rows:
        if r["posteam"] == HOME:
            r["posteam"] = "LA"
    path = write_parquet(tmp_path, rows)
    req = mod.GameRequest(season=SYN_SEASON, game_date=SYN_DATE, away_team=AWAY, home_team="LAR")
    result = run(path, request=req)
    assert result["status"] == "read"
    assert result["game"]["observed"]["home_team"] == "LA"
    assert result["game"]["requested"]["home_team_canonical"] == "LAR"


# ---------------------------------------------------------------------------
# Duplicate keys: identical vs conflicting, never discarded
# ---------------------------------------------------------------------------


def test_duplicate_keys_identical_versus_conflicting(tmp_path):
    rows = alternating_game(DEFAULT_POSSESSIONS)
    rows.append(dict(rows[1]))  # identical duplicate of play 2
    rows.append(dict(rows[5], yards_gained=99.0))  # conflicting duplicate of play 6
    path = write_parquet(tmp_path, rows)
    result = run(path, possession=mod.PossessionRequest(HOME, 1))
    keys = result["inventory"]["keys"]
    assert keys["row_count"] == 19
    assert keys["distinct_game_play_key_count"] == 17
    assert keys["identical_duplicate_keys"] == [
        {"game_id": SYN_GAME_ID, "play_id": 2.0, "occurrences": 2}
    ]
    assert keys["conflicting_duplicate_keys"] == [
        {
            "game_id": SYN_GAME_ID,
            "play_id": 6.0,
            "occurrences": 2,
            "differing_columns": ["yards_gained"],
        }
    ]
    statuses = {r["play_id"]: r["duplicate_status"] for r in result["events"]["rows"]}
    assert statuses[6.0] == "conflicting_duplicate"
    emitted_six = [r for r in result["events"]["rows"] if r["play_id"] == 6.0]
    assert sorted(r["fields"]["yards_gained"] for r in emitted_six) == [3.0, 99.0]


# ---------------------------------------------------------------------------
# Possession selection by evidenced semantics
# ---------------------------------------------------------------------------


def test_second_home_possession_is_provider_drive_four_not_two(tmp_path):
    path = write_parquet(tmp_path, alternating_game(DEFAULT_POSSESSIONS))
    result = run(path, possession=mod.PossessionRequest(HOME, 2))
    selection = result["possession"]["selection"]
    assert selection["status"] == "resolved"
    assert selection["selected_run"]["provider_drive"] == 4.0
    assert selection["selected_run"]["team_possession_ordinal"] == 2
    assert selection["selected_run"]["first_play_id"] == 10.0
    assert selection["selected_run"]["last_play_id"] == 14.0
    assert [r["provider_drive"] for r in result["possession"]["runs"]] == [1.0, 2.0, 3.0, 4.0, 5.0]


def test_consecutive_same_team_drives_are_separate_possessions(tmp_path):
    possessions = [(AWAY, 1.0, 2), (HOME, 2.0, 3), (HOME, 3.0, 3), (AWAY, 4.0, 2)]
    path = write_parquet(tmp_path, alternating_game(possessions))
    result = run(path, possession=mod.PossessionRequest(HOME, 2))
    assert result["possession"]["selection"]["selected_run"]["provider_drive"] == 3.0


def test_unattributed_rows_do_not_break_or_count_as_possession(tmp_path):
    rows = alternating_game(DEFAULT_POSSESSIONS)
    rows.insert(9, play(8.5, None, None, play_type=None, desc="SYNTHETIC end of quarter"))
    path = write_parquet(tmp_path, rows)
    result = run(path, possession=mod.PossessionRequest(HOME, 2))
    assert result["possession"]["unattributed_rows"] == 1
    assert result["possession"]["selection"]["selected_run"]["provider_drive"] == 4.0


def test_null_provider_drive_in_possession_is_unresolved(tmp_path):
    rows = alternating_game(DEFAULT_POSSESSIONS)
    for r in rows:
        if r["drive"] == 4.0:
            r["drive"] = None
            r["fixed_drive"] = None
    path = write_parquet(tmp_path, rows)
    result = run(path, possession=mod.PossessionRequest(HOME, 2))
    assert result["possession"]["selection"]["status"] == "unresolved"
    assert result["possession"]["selection"]["reason"] == "null_provider_drive_in_possession"
    assert result["events"]["status"] == "withheld"
    assert result["events"]["rows"] == []


def test_non_contiguous_provider_drive_is_unresolved(tmp_path):
    possessions = [
        (AWAY, 1.0, 2), (HOME, 2.0, 2), (AWAY, 3.0, 2), (HOME, 4.0, 2), (AWAY, 3.0, 2),
    ]
    path = write_parquet(tmp_path, alternating_game(possessions))
    result = run(path, possession=mod.PossessionRequest(AWAY, 2))
    assert result["possession"]["selection"]["reason"] == "provider_drive_not_contiguous"


def test_missing_drive_column_is_unresolved(tmp_path):
    rows = [
        {k: v for k, v in r.items() if k not in ("drive", "fixed_drive")}
        for r in alternating_game(DEFAULT_POSSESSIONS)
    ]
    path = write_parquet(tmp_path, rows)
    result = run(path, possession=mod.PossessionRequest(HOME, 2))
    assert result["possession"]["basis"]["drive_column_used"] is None
    assert result["possession"]["selection"]["reason"] == "no_provider_drive_column"


def test_ordinal_beyond_observed_possessions_is_unresolved(tmp_path):
    path = write_parquet(tmp_path, alternating_game(DEFAULT_POSSESSIONS))
    result = run(path, possession=mod.PossessionRequest(HOME, 3))
    assert result["possession"]["selection"]["reason"] == "team_possession_ordinal_not_present"
    assert result["possession"]["selection"]["team_possession_runs_observed"] == 2


# ---------------------------------------------------------------------------
# Field states: absent vs null vs explicit false/zero vs value; binary shotgun
# ---------------------------------------------------------------------------


def test_field_state_distinctions_and_shotgun_limitation(tmp_path):
    rows = alternating_game(DEFAULT_POSSESSIONS)
    rows[0]["shotgun"] = 1.0
    rows[1]["shotgun"] = None
    path = write_parquet(tmp_path, rows)
    result = run(path, possession=mod.PossessionRequest(AWAY, 1))
    fields = result["inventory"]["fields"]
    families = fields["inventoried_families"]
    separate = fields["separately_inventoried_families"]
    assert families["field_position"]["side_of_field"] == {"status": "absent", "dtype": None}
    penalty = families["penalty_no_play"]["penalty"]
    assert penalty["status"] == "present"
    assert penalty["explicit_false_or_zero_rows"] == len(rows) and penalty["null_rows"] == 0
    passer = families["actor_ids"]["passer_player_id"]
    assert passer["null_rows"] == len(rows) and passer["value_rows"] == 0
    shotgun = separate["qb_alignment"]["fields"]["shotgun"]
    assert shotgun["value_rows"] == 1
    assert shotgun["null_rows"] == 1
    assert shotgun["explicit_false_or_zero_rows"] == len(rows) - 2
    assert "Under, Gun, or Pistol" in separate["qb_alignment"]["note"]
    assert separate["routes"]["fields"]["route"]["status"] == "absent"
    assert separate["protection"]["fields"] == {}
    assert "epa" in fields["uninspected_columns"]
    event_fields = result["events"]["rows"][0]["fields"]
    assert event_fields["shotgun"] == 1.0 and event_fields["penalty"] == 0.0
    assert event_fields["passer_player_id"] is None
    assert "side_of_field" not in event_fields


def test_classify_value_distinguishes_every_state():
    columns = {"a", "b", "c", "d", "e"}
    row = {"a": None, "b": 0.0, "c": False, "d": 5, "e": "x"}
    assert mod.classify_value(row, "zz", columns) == "absent_column"
    assert mod.classify_value(row, "a", columns) == "null"
    assert mod.classify_value(row, "b", columns) == "explicit_false_or_zero"
    assert mod.classify_value(row, "c", columns) == "explicit_false_or_zero"
    assert mod.classify_value(row, "d", columns) == "value"
    assert mod.classify_value(row, "e", columns) == "value"


# ---------------------------------------------------------------------------
# Penalty / nullified events and repeated keys: status preserved, no snap counting
# ---------------------------------------------------------------------------


def test_nullified_event_and_repeated_key_preserve_status_without_snap_counting(tmp_path):
    rows = alternating_game(DEFAULT_POSSESSIONS)
    rows[3] = play(
        4.0, HOME, 2.0, play_type="no_play", penalty=1.0, penalty_team=AWAY,
        desc="SYNTHETIC nullified",
    )
    rows.append(dict(rows[3]))
    path = write_parquet(tmp_path, rows)
    result = run(path, possession=mod.PossessionRequest(HOME, 1))
    events = result["events"]
    nullified = [r for r in events["rows"] if r["play_id"] == 4.0]
    assert len(nullified) == 2
    assert all(r["event_status"]["no_play"] is True for r in nullified)
    assert all(r["event_status"]["penalty_raw"] == 1.0 for r in nullified)
    assert all(r["duplicate_status"] == "identical_duplicate" for r in nullified)
    assert events["row_count"] == 5 and events["distinct_game_play_key_count"] == 4
    assert result["inventory"]["fields"]["no_play_rows"] == 2
    assert "snap" in events["snap_denominator_note"]
    assert not any("snap" in key for key in events if key != "snap_denominator_note")


# ---------------------------------------------------------------------------
# Limits and truncation
# ---------------------------------------------------------------------------


def test_more_than_forty_events_truncated_with_two_boundaries_per_side(tmp_path):
    possessions = [(AWAY, 1.0, 3), (HOME, 2.0, 45), (AWAY, 3.0, 3)]
    path = write_parquet(tmp_path, alternating_game(possessions))
    result = run(path, possession=mod.PossessionRequest(HOME, 1))
    events = result["events"]
    assert events["truncated"] is True
    assert events["row_count"] == 45 and events["emitted_row_count"] == 40
    assert events["omitted_row_count"] == 5
    assert [r["play_id"] for r in events["boundary_before"]] == [2.0, 3.0]
    assert [r["play_id"] for r in events["boundary_after"]] == [49.0, 50.0]
    assert [r["play_id"] for r in events["rows"]][:2] == [4.0, 5.0]


def test_boundaries_are_omitted_when_not_supportable(tmp_path):
    possessions = [(HOME, 1.0, 2), (AWAY, 2.0, 1)]
    path = write_parquet(tmp_path, alternating_game(possessions))
    result = run(path, possession=mod.PossessionRequest(HOME, 1))
    assert result["events"]["boundary_before"] == []
    assert [r["play_id"] for r in result["events"]["boundary_after"]] == [3.0]


# ---------------------------------------------------------------------------
# Receipt timestamps and admission are never invented
# ---------------------------------------------------------------------------


def test_receipt_never_invents_publication_ingestion_or_admission(tmp_path):
    path = write_parquet(tmp_path, alternating_game(DEFAULT_POSSESSIONS))
    result = run(path)
    receipt = result["receipt"]
    assert receipt["source"]["published_at"] is None
    assert receipt["source"]["published_at_basis"] == "not_evidenced"
    assert receipt["source"]["retrieved_at"] is None
    assert receipt["source"]["retrieved_at_basis"] == "unknown"
    assert receipt["source"]["provider_dataset_ref"] is None
    assert receipt["times"]["ingestion_time"] is None
    assert receipt["times"]["processing_time"] is not None
    assert receipt["lineage"]["status"] == "unknown"
    assert receipt["admission"]["status"] == "not_admitted"
    assert receipt["governance_status"] == "ungoverned" and receipt["canonical"] is False
    assert receipt["side_effects"] == {
        "network": False, "database": False, "schema_change": False, "app_startup": False
    }


def test_operator_supplied_times_are_carried_as_supplied_not_processing_time(tmp_path):
    path = write_parquet(tmp_path, alternating_game(DEFAULT_POSSESSIONS))
    result = run(
        path,
        declaration=mod.SourceDeclaration(
            provider_dataset_ref="synthetic-provider:fixture",
            retrieved_at="1999-01-02T00:00:00Z",
            published_at="1999-01-01T12:00:00Z",
        ),
    )
    source = result["receipt"]["source"]
    assert source["published_at"] == "1999-01-01T12:00:00Z"
    assert source["published_at_basis"] == "operator_supplied"
    assert source["retrieved_at"] == "1999-01-02T00:00:00Z"
    assert source["provider_dataset_ref_basis"] == "operator_supplied"
    assert source["published_at"] != result["receipt"]["times"]["processing_time"]


def test_output_reproducible_apart_from_named_processing_time(tmp_path):
    path = write_parquet(tmp_path, alternating_game(DEFAULT_POSSESSIONS))
    first = json.loads(mod.dumps(run(path, possession=mod.PossessionRequest(HOME, 2))))
    second = json.loads(mod.dumps(run(path, possession=mod.PossessionRequest(HOME, 2))))
    first["receipt"]["times"]["processing_time"] = "X"
    second["receipt"]["times"]["processing_time"] = "X"
    assert first == second


# ---------------------------------------------------------------------------
# Read-only guarantees and CLI behavior
# ---------------------------------------------------------------------------


def test_reader_module_imports_no_network_database_or_app_code():
    source = Path(mod.__file__).read_text(encoding="utf-8")
    for forbidden in ("httpx", "urllib", "requests", "nflreadpy", "psycopg", "sqlalchemy",
                      "fastapi", "socket", "subprocess", "asyncpg"):
        assert forbidden not in source, forbidden


def test_cli_rejection_exits_2_and_writes_nothing(tmp_path):
    path = write_parquet(tmp_path, alternating_game(DEFAULT_POSSESSIONS))
    out = tmp_path / "result.json"
    proc = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "read_pbp_one_game_offline.py"),
         "--path", str(path), "--expected-bytes", str(path.stat().st_size),
         "--expected-sha256", "cd" * 32, "--season", str(SYN_SEASON), "--date", SYN_DATE,
         "--away", AWAY, "--home", HOME, "--out", str(out)],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    assert proc.returncode == 2
    assert not out.exists()
    assert json.loads(proc.stdout)["rejection"]["reason"] == "sha256_mismatch"


def test_cli_success_writes_result_and_exits_0(tmp_path):
    path = write_parquet(tmp_path, alternating_game(DEFAULT_POSSESSIONS))
    args = receipt_args(path)
    out = tmp_path / "result.json"
    proc = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "read_pbp_one_game_offline.py"),
         "--path", str(path), "--expected-bytes", str(args["expected_bytes"]),
         "--expected-sha256", args["expected_sha256"], "--season", str(SYN_SEASON),
         "--date", SYN_DATE, "--away", AWAY, "--home", HOME,
         "--possession-team", HOME, "--possession-ordinal", "2", "--out", str(out)],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    assert proc.returncode == 0, proc.stderr
    result = json.loads(out.read_text())
    assert result["status"] == "read"
    assert result["possession"]["selection"]["selected_run"]["provider_drive"] == 4.0


def test_cli_rejects_partial_possession_arguments(tmp_path):
    proc = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "read_pbp_one_game_offline.py"),
         "--path", "x", "--expected-bytes", "1", "--expected-sha256", "00" * 32,
         "--season", "1999", "--date", SYN_DATE, "--away", AWAY, "--home", HOME,
         "--possession-team", HOME],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    assert proc.returncode == 3

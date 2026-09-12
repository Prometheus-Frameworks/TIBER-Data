"""Synthetic-fixture tests for the offline one-game PBP reader (Research #22 first PR).

Every fixture here is fictional and clearly labeled SYNTHETIC. Team codes `SYA`/`SYB`,
season 1999, and `SYN_` game IDs cannot be mistaken for any real game. No row is
reconstructed from the operator's personal film chart. No network or database access.
"""

from __future__ import annotations

import hashlib
import json
import os
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
    assert result["rejection"]["parsed"] == "not_attempted"
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
            "affects_possession_order": False,
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
    assert all(r["event_status"]["no_play"] == "no_play" for r in nullified)
    assert all(r["event_status"]["penalty_raw"] == 1.0 for r in nullified)
    assert all(r["duplicate_status"] == "identical_duplicate" for r in nullified)
    assert events["row_count"] == 5 and events["distinct_game_play_key_count"] == 4
    assert result["inventory"]["fields"]["no_play_status_rows"]["no_play"] == 2
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


# ---------------------------------------------------------------------------
# Review repairs (Research #22 branch review, 2026-09-10)
# ---------------------------------------------------------------------------


def test_f1_event_varying_time_of_day_does_not_conflict_game_identity(tmp_path):
    rows = alternating_game(DEFAULT_POSSESSIONS)
    for i, r in enumerate(rows):
        r["time_of_day"] = f"01:{i:02d}:00"
        r["start_time"] = "13:00:00"
    path = write_parquet(tmp_path, rows)
    result = run(path, possession=mod.PossessionRequest(HOME, 2))
    assert result["status"] == "read"
    assert result["game"]["status"] == "matched"
    assert "time_of_day" not in mod.GAME_IDENTITY_COLUMNS
    assert "time_of_day" in mod.INVENTORY_FIELD_FAMILIES["quarter_clock"]
    assert set(result["game"]["selection_scan"]["columns_scanned"]) == set(
        mod.GAME_IDENTITY_COLUMNS
    )
    descriptors = result["game"]["descriptors"]
    assert descriptors["start_time"] == {
        "distinct_count": 1, "distinct_values": ["13:00:00"],
        "varies_within_game": False, "truncated": False,
    }
    assert descriptors["week"]["distinct_values"] == [1]
    assert result["events"]["rows"][0]["fields"]["time_of_day"] == "01:09:00"


def test_f1_varying_descriptor_is_disclosed_not_fatal(tmp_path):
    rows = alternating_game(DEFAULT_POSSESSIONS)
    rows[-1]["week"] = 2
    path = write_parquet(tmp_path, rows)
    result = run(path)
    assert result["game"]["status"] == "matched"
    assert result["game"]["descriptors"]["week"]["varies_within_game"] is True
    assert result["game"]["descriptors"]["week"]["distinct_values"] == [1, 2]


def test_f1_conflicting_home_team_within_one_game_stays_unresolved(tmp_path):
    rows = alternating_game(DEFAULT_POSSESSIONS)
    rows[-1]["home_team"] = "SYZ"
    path = write_parquet(tmp_path, rows)
    result = run(path)
    assert result["status"] == "unresolved"
    assert result["game"]["reason"] == "conflicting_game_metadata"


def test_f2_null_drive_earlier_in_prefix_withholds_ordinal(tmp_path):
    # (SYA,null), (SYA,1), (SYB,2), (SYA,3): the missing earlier drive may simply be part
    # of the first possession, so "SYA possession 2" cannot be established.
    possessions = [(HOME, None, 2), (HOME, 1.0, 2), (AWAY, 2.0, 2), (HOME, 3.0, 2)]
    path = write_parquet(tmp_path, alternating_game(possessions))
    result = run(path, possession=mod.PossessionRequest(HOME, 2))
    selection = result["possession"]["selection"]
    assert selection["status"] == "unresolved"
    assert selection["reason"] == "null_provider_drive_in_prefix"
    assert selection["affected_runs"] == [1]
    assert result["events"]["status"] == "withheld"
    assert len(result["possession"]["runs"]) == 4  # records retained


def test_f2_non_monotone_drive_earlier_in_prefix_withholds_ordinal(tmp_path):
    possessions = [(AWAY, 5.0, 2), (HOME, 1.0, 2), (AWAY, 2.0, 2), (HOME, 3.0, 2)]
    path = write_parquet(tmp_path, alternating_game(possessions))
    result = run(path, possession=mod.PossessionRequest(HOME, 2))
    assert result["possession"]["selection"]["reason"] == "provider_drive_order_non_monotone"


def test_f2_conflicting_duplicate_on_earlier_team_or_drive_withholds_ordinal(tmp_path):
    rows = alternating_game(DEFAULT_POSSESSIONS)
    rows.append(dict(rows[4], posteam=AWAY, defteam=HOME))  # play 5 duplicated with other team
    path = write_parquet(tmp_path, rows)
    result = run(path, possession=mod.PossessionRequest(HOME, 2))
    selection = result["possession"]["selection"]
    assert selection["status"] == "unresolved"
    assert selection["reason"] == "conflicting_duplicate_in_prefix"
    assert selection["affected_play_ids"] == [5.0]
    conflict = result["inventory"]["keys"]["conflicting_duplicate_keys"][0]
    assert conflict["affects_possession_order"] is True


def test_f2_conflicting_duplicate_on_non_order_field_does_not_withhold(tmp_path):
    rows = alternating_game(DEFAULT_POSSESSIONS)
    rows.append(dict(rows[4], yards_gained=99.0))
    path = write_parquet(tmp_path, rows)
    result = run(path, possession=mod.PossessionRequest(HOME, 2))
    assert result["possession"]["selection"]["status"] == "resolved"
    conflict = result["inventory"]["keys"]["conflicting_duplicate_keys"][0]
    assert conflict["affects_possession_order"] is False


def test_f2_conflicting_duplicate_after_selection_does_not_withhold(tmp_path):
    rows = alternating_game(DEFAULT_POSSESSIONS)
    rows.append(dict(rows[-1], posteam=HOME, defteam=AWAY))  # last play (drive 5) conflict
    path = write_parquet(tmp_path, rows)
    result = run(path, possession=mod.PossessionRequest(HOME, 2))
    assert result["possession"]["selection"]["status"] == "resolved"


def test_f2_unattributed_row_carrying_unaccounted_drive_withholds_ordinal(tmp_path):
    rows = alternating_game(DEFAULT_POSSESSIONS)
    # A posteam-null row with its own provider drive number between drives 1 and 2 is
    # evidence of a possession the run count did not see.
    rows.insert(3, play(3.5, None, 1.5, desc="SYNTHETIC unattributed with own drive"))
    path = write_parquet(tmp_path, rows)
    result = run(path, possession=mod.PossessionRequest(HOME, 2))
    selection = result["possession"]["selection"]
    assert selection["reason"] == "unattributed_drive_value_in_prefix"
    assert selection["affected_play_ids"] == [3.5]


def test_f2_neutral_unattributed_row_inside_a_drive_still_resolves(tmp_path):
    rows = alternating_game(DEFAULT_POSSESSIONS)
    rows.insert(4, play(4.5, None, 2.0, desc="SYNTHETIC timeout inside drive 2"))
    path = write_parquet(tmp_path, rows)
    result = run(path, possession=mod.PossessionRequest(HOME, 2))
    assert result["possession"]["selection"]["status"] == "resolved"
    assert result["possession"]["selection"]["selected_run"]["provider_drive"] == 4.0


def _cli(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "read_pbp_one_game_offline.py"), *args],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )


def _cli_args(path: Path, out: Path) -> list[str]:
    args = receipt_args(path)
    return [
        "--path", str(path), "--expected-bytes", str(args["expected_bytes"]),
        "--expected-sha256", args["expected_sha256"], "--season", str(SYN_SEASON),
        "--date", SYN_DATE, "--away", AWAY, "--home", HOME, "--out", str(out),
    ]


@pytest.mark.parametrize("alias", ["input_itself", "symlink", "hardlink", "dangling_symlink"])
def test_f3_cli_refuses_out_that_aliases_or_exists(tmp_path, alias):
    path = write_parquet(tmp_path, alternating_game(DEFAULT_POSSESSIONS))
    original = path.read_bytes()
    if alias == "input_itself":
        out = path
    elif alias == "symlink":
        out = tmp_path / "alias.json"
        out.symlink_to(path)
    elif alias == "hardlink":
        out = tmp_path / "alias.json"
        os.link(path, out)
    else:
        out = tmp_path / "dangling.json"
        out.symlink_to(tmp_path / "does_not_exist")
    proc = _cli(_cli_args(path, out))
    assert proc.returncode == 4, proc.stderr
    assert "refusing --out" in proc.stderr
    assert path.read_bytes() == original
    if alias != "dangling_symlink":
        assert Path(out).read_bytes() == original
    else:
        assert os.path.lexists(out) and not out.exists()


def test_f3_cli_refuses_unrelated_existing_output(tmp_path):
    path = write_parquet(tmp_path, alternating_game(DEFAULT_POSSESSIONS))
    out = tmp_path / "existing.json"
    out.write_text("keep me", encoding="utf-8")
    proc = _cli(_cli_args(path, out))
    assert proc.returncode == 4
    assert out.read_text(encoding="utf-8") == "keep me"


def test_f3_cli_creates_new_output_exclusively(tmp_path):
    path = write_parquet(tmp_path, alternating_game(DEFAULT_POSSESSIONS))
    out = tmp_path / "fresh.json"
    proc = _cli(_cli_args(path, out))
    assert proc.returncode == 0, proc.stderr
    assert json.loads(out.read_text())["status"] == "read"


def test_f4_game_read_pushes_selection_into_scan_and_never_uses_eager_read(tmp_path, monkeypatch):
    rows = alternating_game(DEFAULT_POSSESSIONS)
    other = [
        dict(r, game_id="SYN_1999_01_SYC_SYD", home_team="SYD", away_team="SYC") for r in rows
    ]
    path = write_parquet(tmp_path, rows + other)
    content = path.read_bytes()
    plan = mod.game_scan(content, SYN_GAME_ID).explain()
    scan_line, *rest = plan.splitlines()
    assert scan_line.lstrip().startswith("Parquet SCAN")
    assert any("SELECTION:" in line and "game_id" in line for line in rest)
    assert not any(line.strip().startswith("FILTER") for line in plan.splitlines())

    def eager_forbidden(*a, **k):
        raise AssertionError("eager pl.read_parquet must not be used after verification")

    monkeypatch.setattr(pl, "read_parquet", eager_forbidden)
    result = run(path, possession=mod.PossessionRequest(HOME, 2))
    assert result["status"] == "read"
    assert result["inventory"]["read_strategy"]["selection_pushed_into_scan"] is True
    assert result["inventory"]["keys"]["row_count"] == len(rows)
    assert "physical_io" in result["inventory"]["read_strategy"]


def test_f5_null_play_type_is_unknown_not_a_negative_no_play_assertion(tmp_path):
    rows = alternating_game(DEFAULT_POSSESSIONS)
    rows[3]["play_type"] = None
    rows[4]["play_type"] = "no_play"
    path = write_parquet(tmp_path, rows)
    result = run(path, possession=mod.PossessionRequest(HOME, 1))
    statuses = {r["play_id"]: r["event_status"]["no_play"] for r in result["events"]["rows"]}
    assert statuses[4.0] == "unknown_null_play_type"
    assert statuses[5.0] == "no_play"
    assert statuses[6.0] == "other_play_type"
    counts = result["inventory"]["fields"]["no_play_status_rows"]
    assert counts == {
        "no_play": 1, "other_play_type": len(rows) - 2,
        "unknown_null_play_type": 1, "unknown_absent_column": 0,
    }


def test_f5_absent_play_type_column_is_unknown_absent(tmp_path):
    rows = [
        {k: v for k, v in r.items() if k != "play_type"}
        for r in alternating_game(DEFAULT_POSSESSIONS)
    ]
    path = write_parquet(tmp_path, rows)
    result = run(path, possession=mod.PossessionRequest(HOME, 1))
    assert all(
        r["event_status"]["no_play"] == "unknown_absent_column" for r in result["events"]["rows"]
    )
    counts = result["inventory"]["fields"]["no_play_status_rows"]
    assert counts["unknown_absent_column"] == len(rows)


def test_classify_no_play_pure_states():
    assert mod.classify_no_play({}, set()) == "unknown_absent_column"
    assert mod.classify_no_play({"play_type": None}, {"play_type"}) == "unknown_null_play_type"
    assert mod.classify_no_play({"play_type": "no_play"}, {"play_type"}) == "no_play"
    assert mod.classify_no_play({"play_type": "pass"}, {"play_type"}) == "other_play_type"


def test_parse_failure_after_magic_check_is_a_bounded_rejection(tmp_path):
    path = tmp_path / "corrupt.parquet"
    path.write_bytes(b"PAR1" + b"\x00SYNTHETIC GARBAGE\x00" * 4 + b"PAR1")
    result = mod.read_one_game(**receipt_args(path), request=REQ)
    assert result["status"] == "rejected"
    assert result["rejection"]["reason"] == "parse_failure"
    assert result["rejection"]["parsed"] == "attempted_failed"
    assert result["rejection"]["detail"]
    assert result["receipt"]["source"]["receipt_status"] == "verified"
    assert result["receipt"]["source"]["format_detected"] == "parquet"
    assert result["game"] is None
    proc = _cli(_cli_args(path, tmp_path / "out.json"))
    assert proc.returncode == 2
    assert not (tmp_path / "out.json").exists()


# ---------------------------------------------------------------------------
# R1: parse_failure is bounded to parquet engine stages; reader defects are distinct
# ---------------------------------------------------------------------------


def test_r1_corrupt_parquet_is_parse_failure_at_schema_stage(tmp_path):
    path = tmp_path / "corrupt.parquet"
    path.write_bytes(b"PAR1" + b"\x00SYNTHETIC GARBAGE\x00" * 4 + b"PAR1")
    result = mod.read_one_game(**receipt_args(path), request=REQ)
    assert result["status"] == "rejected"
    assert result["rejection"]["reason"] == "parse_failure"
    assert result["rejection"]["read_stage"] == "inspect_schema"
    assert result["failure"] is None


def test_r1_engine_failure_after_schema_is_parse_failure_with_its_stage(tmp_path, monkeypatch):
    path = write_parquet(tmp_path, alternating_game(DEFAULT_POSSESSIONS))

    def broken_scan(*a, **k):
        raise OSError("SYNTHETIC engine failure")

    monkeypatch.setattr(mod, "game_scan", broken_scan)
    result = run(path)
    assert result["status"] == "rejected"
    assert result["rejection"]["reason"] == "parse_failure"
    assert result["rejection"]["read_stage"] == "describe_game_descriptors"
    assert result["rejection"]["parsed"] == "attempted_failed"


@pytest.mark.parametrize(
    "function, stage",
    [
        ("inventory_duplicates", "inventory_duplicates"),
        ("inventory_fields", "inventory_fields"),
        ("build_possession_sequence", "build_possession_sequence"),
        ("select_possession", "select_possession"),
        ("select_events", "select_events"),
    ],
)
def test_r1_post_parse_processing_error_is_not_a_parse_failure(
    tmp_path, monkeypatch, function, stage
):
    path = write_parquet(tmp_path, alternating_game(DEFAULT_POSSESSIONS))

    def broken(*a, **k):
        raise RuntimeError("SYNTHETIC reader defect")

    monkeypatch.setattr(mod, function, broken)
    result = run(path, possession=mod.PossessionRequest(HOME, 2))
    assert result["status"] == "processing_failed"
    assert result["rejection"] is None
    failure = result["failure"]
    assert failure["kind"] == "reader_processing_failure"
    assert failure["stage"] == stage
    assert failure["parsed"] == "succeeded"
    assert "SYNTHETIC reader defect" in failure["detail"]
    assert "parse" not in failure["kind"]
    # Verified receipt and the already-matched game are retained; nothing else is claimed.
    assert result["receipt"]["source"]["receipt_status"] == "verified"
    assert result["game"]["status"] == "matched"
    assert result["inventory"] is None and result["events"] is None


def test_r1_matching_logic_error_is_processing_failure_not_parse_failure(tmp_path, monkeypatch):
    path = write_parquet(tmp_path, alternating_game(DEFAULT_POSSESSIONS))

    def broken(*a, **k):
        raise KeyError("SYNTHETIC matching defect")

    monkeypatch.setattr(mod, "_normalize_date_value", broken)
    result = run(path)
    assert result["status"] == "processing_failed"
    assert result["failure"]["stage"] == "locate_game_matching"
    assert result["game"] is None  # location never completed


def test_r1_engine_and_processing_stage_vocabularies_are_disjoint_and_asserted():
    assert not set(mod.ENGINE_STAGES) & set(mod.PROCESSING_STAGES)
    with pytest.raises(AssertionError):
        with mod._engine_stage("inventory_duplicates"):
            pass
    with pytest.raises(AssertionError):
        with mod._processing_stage("inspect_schema"):
            pass


def test_r1_cli_exit_5_for_processing_failure_and_writes_nothing(tmp_path, monkeypatch):
    from importlib.util import module_from_spec, spec_from_file_location

    spec = spec_from_file_location(
        "read_pbp_one_game_offline", REPO_ROOT / "scripts" / "read_pbp_one_game_offline.py"
    )
    assert spec is not None and spec.loader is not None
    cli = module_from_spec(spec)
    spec.loader.exec_module(cli)
    path = write_parquet(tmp_path, alternating_game(DEFAULT_POSSESSIONS))
    monkeypatch.setattr(mod, "inventory_fields", lambda *a, **k: (_ for _ in ()).throw(
        RuntimeError("SYNTHETIC")
    ))
    out = tmp_path / "out.json"
    code = cli.main(_cli_args(path, out)[:-2] + ["--out", str(out)])
    assert code == 5
    assert not out.exists()


# ---------------------------------------------------------------------------
# Codex exact-head review of 0ae4208 (PR #269): C1 null game_id, C2 argparse exit code
# ---------------------------------------------------------------------------


def test_c1_matching_identity_with_null_game_id_is_never_certified(tmp_path):
    rows = [dict(r, game_id=None) for r in alternating_game(DEFAULT_POSSESSIONS)]
    path = write_parquet(tmp_path, rows)
    result = run(path, possession=mod.PossessionRequest(HOME, 2))
    assert result["status"] == "unresolved"
    assert result["game"]["status"] == "unresolved"
    assert result["game"]["reason"] == "matching_identity_without_game_id"
    assert result["game"]["observed"] is None
    assert result["game"]["diagnostics"]["matching_tuples_without_game_id"] == 1
    assert result["inventory"] is None and result["events"] is None


@pytest.mark.parametrize("bad_id", [None, "", "   "])
def test_c1_mixed_null_and_real_game_id_withholds_the_real_match_too(tmp_path, bad_id):
    rows = alternating_game(DEFAULT_POSSESSIONS)
    rows.append(play(99.0, HOME, 9.0, game_id=bad_id))
    path = write_parquet(tmp_path, rows)
    result = run(path)
    assert result["status"] == "unresolved"
    assert result["game"]["reason"] == "matching_identity_without_game_id"
    assert result["game"]["diagnostics"]["matching_tuples_without_game_id"] == 1


def test_c2_argparse_usage_errors_exit_3_not_2(tmp_path):
    base = [
        "--path", "x", "--expected-bytes", "1", "--expected-sha256", "00" * 32,
        "--date", SYN_DATE, "--away", AWAY,
    ]
    missing_required = _cli(base + ["--season", "1999"])  # no --home
    assert missing_required.returncode == 3
    assert "error" in missing_required.stderr
    non_integer = _cli(base + ["--season", "abc", "--home", HOME])
    assert non_integer.returncode == 3
    unknown_flag = _cli(base + ["--season", "1999", "--home", HOME, "--bogus"])
    assert unknown_flag.returncode == 3
    helped = _cli(["--help"])
    assert helped.returncode == 0


# ---------------------------------------------------------------------------
# Codex exact-head re-review of 9b88311 (PR #269): D1 ordinal, D2 season, D3 bytes
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("ordinal", ["0", "-1"])
def test_d1_non_positive_possession_ordinal_is_a_usage_error(tmp_path, ordinal):
    path = write_parquet(tmp_path, alternating_game(DEFAULT_POSSESSIONS))
    args = _cli_args(path, tmp_path / "out.json")[:-2]
    proc = _cli(args + ["--possession-team", HOME, "--possession-ordinal", ordinal])
    assert proc.returncode == 3
    assert "positive integer" in proc.stderr
    assert not (tmp_path / "out.json").exists()


def test_d1_library_rejects_non_positive_ordinal_before_reading(tmp_path, monkeypatch):
    path = write_parquet(tmp_path, alternating_game(DEFAULT_POSSESSIONS))
    monkeypatch.setattr(mod, "verify_source_bytes", lambda *a, **k: pytest.fail("read"))
    for bad in (0, -3, True):
        with pytest.raises(ValueError):
            run(path, possession=mod.PossessionRequest(HOME, bad))


@pytest.mark.parametrize(
    "season_value, expected",
    [
        (1999, "matched"), (1999.0, "matched"), ("1999", "matched"),
        (1999.5, "unresolved"), (1998.999, "unresolved"), ("1999.0", "unresolved"),
        (" 1999", "unresolved"), (True, "unresolved"), (None, "unresolved"),
    ],
)
def test_d2_season_matches_only_exact_integral_values(tmp_path, season_value, expected):
    rows = [dict(r, season=season_value) for r in alternating_game(DEFAULT_POSSESSIONS)]
    path = write_parquet(tmp_path, rows)
    result = run(path)
    assert result["game"]["status"] == expected
    if expected == "unresolved":
        assert result["game"]["reason"] == "no_matching_game"


def test_d2_season_matches_pure_states():
    assert mod.season_matches(1999, 1999)
    assert mod.season_matches(1999.0, 1999)
    assert not mod.season_matches(1999.5, 1999)
    assert not mod.season_matches(True, 1)
    assert not mod.season_matches(float("nan"), 1999)
    assert not mod.season_matches(object(), 1999)


def test_d3_bytes_in_emitted_field_serialize_as_explicit_hex_envelope(tmp_path):
    rows = alternating_game(DEFAULT_POSSESSIONS)
    for r in rows:
        r["desc"] = b"\x00\xffSYNTHETIC"
    path = write_parquet(tmp_path, rows)
    result = run(path, possession=mod.PossessionRequest(HOME, 1))
    assert result["status"] == "read"
    text = mod.dumps(result)  # must not raise
    # Raw bytes stay raw internally; the hex envelope is applied at the output boundary.
    assert result["events"]["rows"][0]["fields"]["desc"] == b"\x00\xffSYNTHETIC"
    desc = json.loads(text)["events"]["rows"][0]["fields"]["desc"]
    assert desc == {"bytes_hex": b"\x00\xffSYNTHETIC".hex(), "byte_length": 11}


def test_d3_jsonable_normalizes_every_supported_scalar():
    import datetime as dt
    from decimal import Decimal

    out = mod._jsonable(
        {
            "b": b"\x01", "t": dt.time(1, 2, 3), "td": dt.timedelta(seconds=90),
            "dec": Decimal("1.50"), "nan": float("nan"), "obj": object(),
        }
    )
    assert out["b"] == {"bytes_hex": "01", "byte_length": 1}
    assert out["t"] == "01:02:03"
    assert out["td"] == {"timedelta_seconds": 90.0}
    assert out["dec"] == {"decimal": "1.50"}
    assert out["nan"] == {"float_nan": True}
    assert out["obj"]["unsupported_type"] == "object"
    json.dumps(out)


def test_d3_serialization_failure_is_bounded_processing_failure_exit_5(tmp_path, monkeypatch):
    from importlib.util import module_from_spec, spec_from_file_location

    spec = spec_from_file_location(
        "read_pbp_one_game_offline", REPO_ROOT / "scripts" / "read_pbp_one_game_offline.py"
    )
    assert spec is not None and spec.loader is not None
    cli = module_from_spec(spec)
    spec.loader.exec_module(cli)
    rows = alternating_game(DEFAULT_POSSESSIONS)
    for r in rows:
        r["desc"] = b"\x00\xffSYNTHETIC"
    path = write_parquet(tmp_path, rows)
    monkeypatch.setattr(mod, "_jsonable", lambda v: v)  # simulate an unnormalized scalar
    out = tmp_path / "out.json"
    possession_args = ["--possession-team", HOME, "--possession-ordinal", "1"]
    code = cli.main(_cli_args(path, out) + possession_args)
    assert code == 5
    assert not out.exists()
    result = run(path, possession=mod.PossessionRequest(HOME, 1))
    text, bounded = mod.dumps_bounded(result)
    assert bounded["status"] == "processing_failed"
    assert bounded["failure"]["stage"] == "serialize_result"
    assert bounded["failure"]["kind"] == "reader_processing_failure"
    assert json.loads(text)["failure"]["stage"] == "serialize_result"


# ---------------------------------------------------------------------------
# Codex exact-head review of e3b5c6b (PR #269): E1 alias same-team request, E2 infinities
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("away, home", [("LA", "LAR"), ("LAR", "LA"), ("LA", "LA")])
def test_e1_alias_pair_that_canonicalizes_to_one_team_is_rejected_before_reading(
    tmp_path, monkeypatch, away, home
):
    rows = [
        dict(r, home_team=home, away_team=away) for r in alternating_game(DEFAULT_POSSESSIONS)
    ]
    path = write_parquet(tmp_path, rows)
    monkeypatch.setattr(mod, "verify_source_bytes", lambda *a, **k: pytest.fail("read"))
    request = mod.GameRequest(
        season=SYN_SEASON, game_date=SYN_DATE, away_team=away, home_team=home
    )
    with pytest.raises(ValueError, match="canonicalization"):
        run(path, request=request)


def test_e1_cli_alias_pair_is_a_usage_error(tmp_path):
    path = write_parquet(tmp_path, alternating_game(DEFAULT_POSSESSIONS))
    args = _cli_args(path, tmp_path / "out.json")
    args[args.index("--away") + 1] = "LA"
    args[args.index("--home") + 1] = "LAR"
    proc = _cli(args)
    assert proc.returncode == 3
    assert "canonicalization" in proc.stderr
    assert not (tmp_path / "out.json").exists()


def test_e1_distinct_teams_through_alias_still_match(tmp_path):
    rows = [dict(r, home_team="LA") for r in alternating_game(DEFAULT_POSSESSIONS)]
    for r in rows:
        if r["posteam"] == HOME:
            r["posteam"] = "LA"
    path = write_parquet(tmp_path, rows)
    request = mod.GameRequest(
        season=SYN_SEASON, game_date=SYN_DATE, away_team=AWAY, home_team="LAR"
    )
    assert run(path, request=request)["game"]["status"] == "matched"


@pytest.mark.parametrize("value, sign", [(float("inf"), "+"), (float("-inf"), "-")])
def test_e2_infinite_floats_serialize_as_signed_envelopes(tmp_path, value, sign):
    rows = alternating_game(DEFAULT_POSSESSIONS)
    rows[3]["yards_gained"] = value
    path = write_parquet(tmp_path, rows)
    result = run(path, possession=mod.PossessionRequest(HOME, 1))
    assert result["status"] == "read"
    text, bounded = mod.dumps_bounded(result)
    assert bounded["status"] == "read"
    raw_by_id = {r["play_id"]: r["fields"]["yards_gained"] for r in result["events"]["rows"]}
    assert raw_by_id[4.0] == value  # raw float kept internally
    emitted = json.loads(text)["events"]["rows"]
    by_id = {r["play_id"]: r["fields"]["yards_gained"] for r in emitted}
    assert by_id[4.0] == {"float_infinity": sign}
    assert by_id[5.0] == 3.0


def test_e2_jsonable_keeps_infinity_nan_null_and_finite_distinct():
    out = mod._jsonable(
        {"p": float("inf"), "n": float("-inf"), "nan": float("nan"), "z": 0.0, "none": None}
    )
    assert out == {
        "p": {"float_infinity": "+"},
        "n": {"float_infinity": "-"},
        "nan": {"float_nan": True},
        "z": 0.0,
        "none": None,
    }
    json.dumps(out, allow_nan=False)


# ---------------------------------------------------------------------------
# Codex exact-head review of 752dce2 (PR #269): G1 infinity keys, G2 receipt args, G3 dates
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("column, value", [
    ("play_id", float("inf")), ("play_id", float("-inf")),
    ("drive", float("inf")), ("drive", float("-inf")),
])
def test_g1_infinite_key_values_are_processed_then_enveloped_at_output(tmp_path, column, value):
    rows = alternating_game(DEFAULT_POSSESSIONS)
    rows.append(play(99.0, HOME, 9.0))
    rows[-1][column] = value
    rows.append(dict(rows[-1]))  # identical duplicate of the infinite-keyed row
    if column == "drive":
        rows[-1]["fixed_drive"] = value
        rows[-2]["fixed_drive"] = value
    path = write_parquet(tmp_path, rows)
    result = run(path, possession=mod.PossessionRequest(HOME, 2))
    assert result["status"] == "read", result.get("failure")
    keys = result["inventory"]["keys"]
    assert keys["row_count"] == len(rows)
    assert len(keys["identical_duplicate_keys"]) == 1
    text, bounded = mod.dumps_bounded(result)
    assert bounded["status"] == "read"
    sign = "+" if value > 0 else "-"
    dup = json.loads(text)["inventory"]["keys"]["identical_duplicate_keys"][0]
    if column == "play_id":
        assert dup["play_id"] == {"float_infinity": sign}
    else:
        runs = json.loads(text)["possession"]["runs"]
        assert runs[-1]["provider_drive"] == {"float_infinity": sign}


def test_g1_internal_rows_keep_raw_scalars_including_nan(tmp_path):
    rows = alternating_game(DEFAULT_POSSESSIONS)
    rows[0]["yards_gained"] = float("nan")
    rows[1]["yards_gained"] = float("inf")
    rows[2]["desc"] = b"\x01SYNTHETIC"
    path = write_parquet(tmp_path, rows)
    content = path.read_bytes()
    loaded, _ = mod.load_game_rows(content, SYN_GAME_ID)
    nan_value = loaded[0]["yards_gained"]
    assert isinstance(nan_value, float) and nan_value != nan_value  # raw NaN, not null
    assert loaded[1]["yards_gained"] == float("inf")
    assert loaded[2]["desc"] == b"\x01SYNTHETIC"
    assert all(isinstance(r["play_id"], float) for r in loaded)


def test_g1_identical_rows_with_nan_are_identical_duplicates_not_conflicts(tmp_path):
    rows = alternating_game(DEFAULT_POSSESSIONS)
    rows[0]["yards_gained"] = float("nan")
    rows.append(dict(rows[0]))
    path = write_parquet(tmp_path, rows)
    keys = run(path)["inventory"]["keys"]
    assert len(keys["identical_duplicate_keys"]) == 1
    assert keys["conflicting_duplicate_keys"] == []


@pytest.mark.parametrize("expected_bytes, sha", [
    (-1, "0" * 64), (10, "not-a-sha256"), (10, "0" * 63), (10, "0" * 65), (10, "g" * 64),
])
def test_g2_malformed_receipt_expectations_are_usage_errors_before_file_access(
    tmp_path, monkeypatch, expected_bytes, sha
):
    path = write_parquet(tmp_path, alternating_game(DEFAULT_POSSESSIONS))
    monkeypatch.setattr(mod, "verify_source_bytes", lambda *a, **k: pytest.fail("read"))
    with pytest.raises(ValueError):
        mod.read_one_game(
            path=path, expected_bytes=expected_bytes, expected_sha256=sha, request=REQ
        )
    args = _cli_args(path, tmp_path / "out.json")
    args[args.index("--expected-bytes") + 1] = str(expected_bytes)
    args[args.index("--expected-sha256") + 1] = sha
    proc = _cli(args)
    assert proc.returncode == 3, proc.stderr
    assert not (tmp_path / "out.json").exists()


def test_g2_uppercase_hex_digest_is_accepted_and_compared_case_insensitively(tmp_path):
    path = write_parquet(tmp_path, alternating_game(DEFAULT_POSSESSIONS))
    args = receipt_args(path)
    result = mod.read_one_game(
        path=path, expected_bytes=args["expected_bytes"],
        expected_sha256=args["expected_sha256"].upper(), request=REQ,
    )
    assert result["receipt"]["source"]["receipt_status"] == "verified"


def test_g2_wrong_but_well_formed_expectations_still_exit_2(tmp_path):
    path = write_parquet(tmp_path, alternating_game(DEFAULT_POSSESSIONS))
    args = _cli_args(path, tmp_path / "out.json")
    args[args.index("--expected-sha256") + 1] = "0" * 64
    assert _cli(args).returncode == 2


@pytest.mark.parametrize("bad_date", ["1999-99-99", "2026-02-30", "1999-00-01", "1999-1-1"])
def test_g3_non_calendar_dates_are_usage_errors_before_file_access(tmp_path, monkeypatch, bad_date):
    path = write_parquet(tmp_path, alternating_game(DEFAULT_POSSESSIONS))
    monkeypatch.setattr(mod, "verify_source_bytes", lambda *a, **k: pytest.fail("read"))
    request = mod.GameRequest(
        season=SYN_SEASON, game_date=bad_date, away_team=AWAY, home_team=HOME
    )
    with pytest.raises(ValueError):
        run(path, request=request)
    args = _cli_args(path, tmp_path / "out.json")
    args[args.index("--date") + 1] = bad_date
    proc = _cli(args)
    assert proc.returncode == 3, proc.stderr


def test_g3_leap_day_is_a_valid_calendar_date():
    mod.GameRequest(season=2024, game_date="2024-02-29", away_team=AWAY, home_team=HOME).validate()
    with pytest.raises(ValueError):
        mod.GameRequest(
            season=2023, game_date="2023-02-29", away_team=AWAY, home_team=HOME
        ).validate()


# ---------------------------------------------------------------------------
# Codex exact-head review of d77facb (PR #269): H1 non-finite play_id, H2 non-finite
# drive, H3 NaN versus null, H4 trailing-newline digest
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("value", [float("inf"), float("-inf")])
def test_h1_non_finite_play_id_withholds_selection_and_events(tmp_path, value):
    # Codex's case: the infinite play ID belongs to the requested team's second drive.
    rows = alternating_game(DEFAULT_POSSESSIONS)
    rows[10]["play_id"] = value  # a play inside HOME drive 4
    path = write_parquet(tmp_path, rows)
    result = run(path, possession=mod.PossessionRequest(HOME, 2))
    assert result["status"] == "read"
    assert result["possession"]["play_id_non_finite_rows"] == 1
    selection = result["possession"]["selection"]
    assert selection["status"] == "unresolved"
    assert selection["reason"] == "non_finite_play_id_breaks_play_order"
    assert result["events"]["status"] == "withheld"
    assert result["events"]["rows"] == []
    text, bounded = mod.dumps_bounded(result)
    assert bounded["status"] == "read"


@pytest.mark.parametrize("value", [float("inf"), float("-inf")])
def test_h2_non_finite_drive_in_prefix_withholds_selection(tmp_path, value):
    rows = alternating_game(DEFAULT_POSSESSIONS)
    for r in rows:
        if r["drive"] == 2.0:
            r["drive"] = value
            r["fixed_drive"] = value
    path = write_parquet(tmp_path, rows)
    for ordinal in (1, 2):
        result = run(path, possession=mod.PossessionRequest(HOME, ordinal))
        selection = result["possession"]["selection"]
        assert selection["status"] == "unresolved", ordinal
        assert selection["reason"] == "non_finite_provider_drive_in_prefix"
        assert selection["affected_runs"] == [2]
        assert result["events"]["status"] == "withheld"
    # An away possession before the infinite drive is still evidenced.
    assert run(path, possession=mod.PossessionRequest(AWAY, 1))["possession"]["selection"][
        "status"
    ] == "resolved"


def test_h2_nan_drive_is_treated_as_missing_not_as_a_drive(tmp_path):
    rows = alternating_game(DEFAULT_POSSESSIONS)
    for r in rows:
        if r["drive"] == 4.0:
            r["drive"] = float("nan")
            r["fixed_drive"] = float("nan")
    path = write_parquet(tmp_path, rows)
    result = run(path, possession=mod.PossessionRequest(HOME, 2))
    assert result["possession"]["selection"]["reason"] == "null_provider_drive_in_possession"
    assert len(result["possession"]["runs"]) == 5  # NaN rows did not each become a run


def test_h3_nan_versus_null_in_a_duplicate_is_a_conflict_not_identical(tmp_path):
    rows = alternating_game(DEFAULT_POSSESSIONS)
    rows[0]["yards_gained"] = float("nan")
    rows.append(dict(rows[0], yards_gained=None))
    path = write_parquet(tmp_path, rows)
    keys = run(path)["inventory"]["keys"]
    assert keys["identical_duplicate_keys"] == []
    assert len(keys["conflicting_duplicate_keys"]) == 1
    assert keys["conflicting_duplicate_keys"][0]["differing_columns"] == ["yards_gained"]


def test_h3_nan_is_counted_and_emitted_distinct_from_null(tmp_path):
    rows = alternating_game(DEFAULT_POSSESSIONS)
    rows[0]["yards_gained"] = float("nan")
    rows[1]["yards_gained"] = None
    path = write_parquet(tmp_path, rows)
    result = run(path, possession=mod.PossessionRequest(AWAY, 1))
    field = result["inventory"]["fields"]["inventoried_families"]["event_outcome"]["yards_gained"]
    assert field["nan_rows"] == 1 and field["null_rows"] == 1
    emitted = json.loads(mod.dumps(result))["events"]["rows"]
    by_id = {r["play_id"]: r["fields"]["yards_gained"] for r in emitted}
    assert by_id[1.0] == {"float_nan": True}
    assert by_id[2.0] is None


def test_h3_values_equal_is_nan_aware():
    nan = float("nan")
    assert mod._values_equal(nan, nan)
    assert not mod._values_equal(nan, None)
    assert not mod._values_equal(None, nan)
    assert not mod._values_equal(nan, 0.0)
    assert mod._values_equal(None, None)
    assert mod._values_equal(1.0, 1.0)


def test_h3_nan_play_id_is_a_null_key(tmp_path):
    rows = alternating_game(DEFAULT_POSSESSIONS)
    rows[3]["play_id"] = float("nan")
    path = write_parquet(tmp_path, rows)
    result = run(path, possession=mod.PossessionRequest(HOME, 1))
    assert result["inventory"]["keys"]["null_key_rows"] == 1
    assert result["possession"]["selection"]["reason"] == "null_play_id_breaks_play_order"


@pytest.mark.parametrize("digest", ["0" * 64 + "\n", "0" * 64 + "\r\n", "\n" + "0" * 64])
def test_h4_digest_with_newline_is_a_usage_error_before_file_access(
    tmp_path, monkeypatch, digest
):
    path = write_parquet(tmp_path, alternating_game(DEFAULT_POSSESSIONS))
    monkeypatch.setattr(mod, "verify_source_bytes", lambda *a, **k: pytest.fail("read"))
    with pytest.raises(ValueError):
        mod.read_one_game(path=path, expected_bytes=10, expected_sha256=digest, request=REQ)
    with pytest.raises(ValueError):
        mod.GameRequest(
            season=SYN_SEASON, game_date=SYN_DATE + "\n", away_team=AWAY, home_team=HOME
        ).validate()


# ---------------------------------------------------------------------------
# Codex exact-head review of b8ee0fd (PR #269): I1 NaN play_id grouping, I2 non-numeric IDs
# ---------------------------------------------------------------------------


def test_i1_two_nan_play_ids_group_together_and_compare_identical(tmp_path):
    rows = alternating_game(DEFAULT_POSSESSIONS)
    rows[3]["play_id"] = float("nan")
    rows.append(dict(rows[3]))
    path = write_parquet(tmp_path, rows)
    result = run(path)
    keys = result["inventory"]["keys"]
    assert keys["null_key_rows"] == 2
    assert keys["distinct_game_play_key_count"] == len(rows) - 1
    assert len(keys["identical_duplicate_keys"]) == 1
    assert keys["conflicting_duplicate_keys"] == []
    emitted = json.loads(mod.dumps(result))["inventory"]["keys"]["identical_duplicate_keys"][0]
    assert emitted["play_id"] == {"float_nan": True}  # raw NaN reported, not the internal key


def test_i1_nan_play_id_pair_with_differing_content_is_a_conflict(tmp_path):
    rows = alternating_game(DEFAULT_POSSESSIONS)
    rows[3]["play_id"] = float("nan")
    rows.append(dict(rows[3], yards_gained=99.0))
    path = write_parquet(tmp_path, rows)
    keys = run(path)["inventory"]["keys"]
    assert keys["identical_duplicate_keys"] == []
    assert len(keys["conflicting_duplicate_keys"]) == 1
    assert keys["conflicting_duplicate_keys"][0]["differing_columns"] == ["yards_gained"]


def test_i1_nan_and_null_play_ids_are_distinct_missing_keys(tmp_path):
    rows = alternating_game(DEFAULT_POSSESSIONS)
    rows[3]["play_id"] = float("nan")
    rows.append(dict(rows[3], play_id=None))
    path = write_parquet(tmp_path, rows)
    keys = run(path)["inventory"]["keys"]
    assert keys["null_key_rows"] == 2
    assert keys["distinct_game_play_key_count"] == len(rows)  # NaN key and null key differ
    assert keys["identical_duplicate_keys"] == [] and keys["conflicting_duplicate_keys"] == []


def test_i1_grouping_key_canonicalizes_nan_only():
    nan_a, nan_b = float("nan"), float("nan")
    assert mod._grouping_key({"game_id": "g", "play_id": nan_a}) == mod._grouping_key(
        {"game_id": "g", "play_id": nan_b}
    )
    assert mod._grouping_key({"game_id": "g", "play_id": None}) != mod._grouping_key(
        {"game_id": "g", "play_id": nan_a}
    )
    assert mod._grouping_key({"game_id": "g", "play_id": 1.0}) == ("g", 1.0)


@pytest.mark.parametrize("bad_id", ["oops", "", "1e400x"])
def test_i2_non_numeric_play_id_withholds_selection(tmp_path, bad_id):
    rows = [dict(r, play_id=str(r["play_id"])) for r in alternating_game(DEFAULT_POSSESSIONS)]
    extra = play(99.0, HOME, 9.0)
    extra["play_id"] = bad_id
    rows.append(extra)
    path = write_parquet(tmp_path, rows)
    result = run(path, possession=mod.PossessionRequest(HOME, 2))
    assert result["status"] == "read"
    assert result["possession"]["play_id_non_numeric_rows"] == 1
    assert result["possession"]["selection"]["reason"] == "non_numeric_play_id_breaks_play_order"
    assert result["events"]["status"] == "withheld"
    assert result["events"]["rows"] == []


def test_i2_parseable_string_play_ids_still_order_and_resolve(tmp_path):
    rows = [dict(r, play_id=str(r["play_id"])) for r in alternating_game(DEFAULT_POSSESSIONS)]
    path = write_parquet(tmp_path, rows)
    result = run(path, possession=mod.PossessionRequest(HOME, 2))
    assert result["possession"]["play_id_non_numeric_rows"] == 0
    assert result["possession"]["selection"]["status"] == "resolved"
    assert result["possession"]["selection"]["selected_run"]["provider_drive"] == 4.0


def test_i2_play_id_order_class_pure_states():
    c = mod.play_id_order_class
    assert c(1.0) == "finite" and c(7) == "finite" and c("30") == "finite"
    assert c(None) == "null" and c(float("nan")) == "null"
    assert c(float("inf")) == "non_finite" and c(float("-inf")) == "non_finite"
    assert c("inf") == "non_finite"
    assert c("oops") == "non_numeric" and c("") == "non_numeric" and c(True) == "non_numeric"
    assert c(b"1") == "non_numeric" and c([1]) == "non_numeric"


# ---------------------------------------------------------------------------
# Codex exact-head review of 84eabe9 (PR #269): J1 non-scalar play IDs must reach the
# unresolved path, never a grouping crash
# ---------------------------------------------------------------------------


def _non_scalar_game(kind: str) -> list[dict[str, Any]]:
    ids = [[1], [2], [3], [3]] if kind == "list" else [{"a": 1}, {"a": 2}, {"a": 3}, {"a": 3}]
    teams = [AWAY, HOME, HOME, HOME]
    drives = [1.0, 2.0, 2.0, 2.0]
    rows = []
    for pid, team, drive in zip(ids, teams, drives, strict=True):
        row = play(0.0, team, drive)
        row["play_id"] = pid
        rows.append(row)
    return rows


@pytest.mark.parametrize("kind", ["list", "struct"])
def test_j1_non_scalar_play_ids_group_hashably_and_withhold_selection(tmp_path, kind):
    rows = _non_scalar_game(kind)
    path = write_parquet(tmp_path, rows)
    result = run(path, possession=mod.PossessionRequest(HOME, 1))
    assert result["status"] == "read", result.get("failure")
    assert result["failure"] is None
    keys = result["inventory"]["keys"]
    assert keys["row_count"] == 4
    assert keys["distinct_game_play_key_count"] == 3  # the two [3] / {"a": 3} rows group
    assert len(keys["identical_duplicate_keys"]) == 1
    assert keys["identical_duplicate_keys"][0]["play_id"] == rows[2]["play_id"]  # raw value
    assert result["possession"]["play_id_non_numeric_rows"] == 4
    selection = result["possession"]["selection"]
    assert selection["status"] == "unresolved"
    assert selection["reason"] == "non_numeric_play_id_breaks_play_order"
    assert result["events"]["status"] == "withheld"
    text, bounded = mod.dumps_bounded(result)
    assert bounded["status"] == "read"
    emitted = json.loads(text)["inventory"]["keys"]["identical_duplicate_keys"][0]["play_id"]
    assert emitted == rows[2]["play_id"]


def test_j1_non_scalar_play_id_conflict_is_detected_by_content(tmp_path):
    rows = _non_scalar_game("list")
    rows[3]["yards_gained"] = 99.0
    path = write_parquet(tmp_path, rows)
    keys = run(path)["inventory"]["keys"]
    assert keys["identical_duplicate_keys"] == []
    assert len(keys["conflicting_duplicate_keys"]) == 1
    assert keys["conflicting_duplicate_keys"][0]["differing_columns"] == ["yards_gained"]


def test_j1_hashable_key_part_pure_states():
    h = mod._hashable_key_part
    assert h(1.0) == 1.0 and h("x") == "x" and h(None) is None
    assert h(float("nan")) is mod._NAN_KEY
    assert h([1, 2]) == h([1, 2]) and h([1, 2]) != h([2, 1])
    assert h({"a": 1}) == h({"a": 1})
    assert h([1]) != h((1,))  # type is part of the key
    hash(h([1])), hash(h({"a": 1}))  # both hashable


# ---------------------------------------------------------------------------
# Codex exact-head review of 874a96b (PR #269): K1 equality-consistent keys, K2 nested
# NaN equality, K3 non-scalar drives, K4 exact integer ordering
# ---------------------------------------------------------------------------


def _nested_id_game(ids: list[Any]) -> list[dict[str, Any]]:
    rows = []
    for pid in ids:
        row = play(0.0, AWAY, 1.0)
        row["play_id"] = pid
        rows.append(row)
    return rows


def test_k1_value_equal_lists_share_a_key_and_are_identical_duplicates(tmp_path):
    path = write_parquet(tmp_path, _nested_id_game([[0.0], [-0.0]]))
    keys = run(path)["inventory"]["keys"]
    assert keys["distinct_game_play_key_count"] == 1
    assert len(keys["identical_duplicate_keys"]) == 1
    assert keys["conflicting_duplicate_keys"] == []


def test_k1_value_equal_structs_share_a_key(tmp_path):
    path = write_parquet(tmp_path, _nested_id_game([{"a": 0.0}, {"a": -0.0}]))
    keys = run(path)["inventory"]["keys"]
    assert keys["distinct_game_play_key_count"] == 1
    assert len(keys["identical_duplicate_keys"]) == 1


def test_k1_freeze_is_consistent_with_values_equal():
    nan = float("nan")
    cases = [
        ([0.0], [-0.0], True), ([nan], [nan], True), ([nan], [None], False),
        ([1, 2], [2, 1], False), ({"a": 1}, {"a": 1}, True), ({"a": nan}, {"a": nan}, True),
        ({"a": [nan, 1.0]}, {"a": [nan, 1.0]}, True), ([1], (1,), False), (1, 1.0, True),
    ]
    for left, right, expected in cases:
        assert mod._values_equal(left, right) is expected, (left, right)
        assert (mod._freeze(left) == mod._freeze(right)) is expected, (left, right)
        hash(mod._freeze(left)), hash(mod._freeze(right))


def test_k2_nested_nan_rows_are_identical_duplicates(tmp_path):
    nan = float("nan")
    path = write_parquet(tmp_path, _nested_id_game([[nan, 1.0], [nan, 1.0]]))
    keys = run(path)["inventory"]["keys"]
    assert len(keys["identical_duplicate_keys"]) == 1
    assert keys["conflicting_duplicate_keys"] == []


def test_k2_nested_nan_versus_nested_null_is_a_conflict(tmp_path):
    nan = float("nan")
    path = write_parquet(tmp_path, _nested_id_game([[nan], [None]]))
    keys = run(path)["inventory"]["keys"]
    assert keys["identical_duplicate_keys"] == []
    assert keys["distinct_game_play_key_count"] == 2  # different keys, so no group to conflict


def test_k2_nested_nan_in_a_non_key_field_compares_recursively(tmp_path):
    nan = float("nan")
    rows = alternating_game(DEFAULT_POSSESSIONS)
    rows[0]["offense_players"] = [nan, 1.0]
    rows.append(dict(rows[0]))
    rows.append(dict(rows[0], offense_players=[nan, 2.0]))
    path = write_parquet(tmp_path, rows)
    keys = run(path)["inventory"]["keys"]
    assert keys["identical_duplicate_keys"] == []
    assert len(keys["conflicting_duplicate_keys"]) == 1
    assert keys["conflicting_duplicate_keys"][0]["differing_columns"] == ["offense_players"]
    assert keys["conflicting_duplicate_keys"][0]["occurrences"] == 3


@pytest.mark.parametrize("kind", ["list", "struct"])
def test_k3_non_scalar_drive_reaches_unresolved_path_with_inventory(tmp_path, kind):
    # A parquet column has one type, so every drive is non-scalar in this fixture.
    rows = alternating_game(DEFAULT_POSSESSIONS)
    for r in rows:
        n = int(r["drive"])
        r["drive"] = [n] if kind == "list" else {"n": n}
        r["fixed_drive"] = None
    path = write_parquet(tmp_path, rows)
    result = run(path, possession=mod.PossessionRequest(HOME, 1))
    assert result["status"] == "read", result.get("failure")
    assert result["failure"] is None
    assert result["inventory"]["keys"]["row_count"] == len(rows)
    assert len(result["possession"]["runs"]) == 5  # non-scalar drives still bound runs
    assert result["possession"]["selection"]["status"] == "unresolved"
    assert result["possession"]["selection"]["reason"] == "provider_drive_not_orderable"
    assert result["events"]["status"] == "withheld"
    assert mod.dumps_bounded(result)[1]["status"] == "read"


def test_k3_non_scalar_drive_occurrences_are_counted_by_frozen_key(tmp_path):
    rows = alternating_game(DEFAULT_POSSESSIONS)
    for r in rows:
        r["drive"] = [int(r["drive"])]
        r["fixed_drive"] = None
    path = write_parquet(tmp_path, rows)
    counts = mod.build_possession_sequence(
        mod.load_game_rows(path.read_bytes(), SYN_GAME_ID)[0],
        mod.inspect_schema(path.read_bytes()),
    )["drive_occurrence_counts"]
    assert all(v == 1 for v in counts.values()) and len(counts) == 5


def test_k4_large_int64_play_ids_order_exactly(tmp_path):
    rows = [
        play(0.0, HOME, 2.0), play(0.0, AWAY, 1.0),
    ]
    rows[0]["play_id"] = 9007199254740993
    rows[1]["play_id"] = 9007199254740992
    path = write_parquet(tmp_path, rows)
    result = run(path, possession=mod.PossessionRequest(HOME, 1))
    ordered = [r["posteam"] for r in result["possession"]["runs"]]
    assert ordered == [AWAY, HOME]  # 9007199254740992 (AWAY) sorts before ...993 (HOME)
    assert result["possession"]["selection"]["status"] == "resolved"
    assert result["events"]["rows"][0]["play_id"] == 9007199254740993


def test_k4_large_integer_strings_order_exactly(tmp_path):
    rows = [play(0.0, HOME, 2.0), play(0.0, AWAY, 1.0)]
    rows[0]["play_id"] = "9007199254740993"
    rows[1]["play_id"] = "9007199254740992"
    path = write_parquet(tmp_path, rows)
    result = run(path)
    assert [r["posteam"] for r in result["possession"]["runs"]] == [AWAY, HOME]


def test_k4_play_id_numeric_pure_states():
    n = mod._play_id_numeric
    assert n(9007199254740993) == 9007199254740993 and isinstance(n(9007199254740993), int)
    assert n("9007199254740993") == 9007199254740993 and isinstance(n("9007199254740993"), int)
    assert n(1.5) == 1.5 and n("1.5") == 1.5
    assert n(True) is None and n(None) is None and n(float("nan")) is None
    assert n(float("inf")) is None and n("inf") is None and n("nan") is None
    assert n("oops") is None and n(b"1") is None and n([1]) is None
    assert mod.play_id_order_class("nan") == "non_numeric"
    assert mod.play_id_order_class("inf") == "non_finite"
    assert mod.play_id_order_class("9007199254740993") == "finite"


# ---------------------------------------------------------------------------
# Codex exact-head review of 91710f3 (PR #269): L1 exact numeric strings, L2 run
# extension equality, plus the cross-stage consistency invariant they share
# ---------------------------------------------------------------------------


def test_l1_decimal_spelled_integral_strings_order_exactly(tmp_path):
    rows = [play(0.0, HOME, 2.0), play(0.0, AWAY, 1.0)]
    rows[0]["play_id"] = "9007199254740993.0"
    rows[1]["play_id"] = "9007199254740992.0"
    path = write_parquet(tmp_path, rows)
    result = run(path, possession=mod.PossessionRequest(HOME, 1))
    assert [r["posteam"] for r in result["possession"]["runs"]] == [AWAY, HOME]
    assert result["events"]["rows"][0]["play_id"] == "9007199254740993.0"


def test_l1_exponent_spelled_strings_order_exactly(tmp_path):
    rows = [play(0.0, HOME, 2.0), play(0.0, AWAY, 1.0)]
    rows[0]["play_id"] = "9007199254740993e0"
    rows[1]["play_id"] = "90071992547409920e-1"
    path = write_parquet(tmp_path, rows)
    result = run(path)
    assert [r["posteam"] for r in result["possession"]["runs"]] == [AWAY, HOME]


def test_l1_order_affecting_conflict_check_uses_exact_strings(tmp_path):
    rows = [play(0.0, AWAY, 1.0), play(0.0, HOME, 2.0), play(0.0, HOME, 2.0)]
    rows[0]["play_id"] = "9007199254740992.0"
    rows[1]["play_id"] = "9007199254740993.0"
    rows[2]["play_id"] = "9007199254740994.0"
    rows.append(dict(rows[2], posteam=AWAY, defteam=HOME))  # conflicting dup on the last play
    path = write_parquet(tmp_path, rows)
    result = run(path, possession=mod.PossessionRequest(AWAY, 1))
    # The conflict is on play ...994, after AWAY's first possession (...992): still resolved.
    assert result["possession"]["selection"]["status"] == "resolved"
    result = run(path, possession=mod.PossessionRequest(HOME, 1))
    assert result["possession"]["selection"]["reason"] == "conflicting_duplicate_in_prefix"


def test_l1_play_id_numeric_is_lossless_and_strict():
    n = mod._play_id_numeric
    assert n("9007199254740993.0") == 9007199254740993 and isinstance(n("9007199254740993.0"), int)
    assert n("9007199254740993e0") == 9007199254740993
    assert n("1e400") == 10**400
    assert n("0.1") == mod.Fraction(1, 10) and n(0.1) == mod.Fraction(0.1)
    assert n("0.1") != n(0.1)  # decimal 0.1 is not the binary float 0.1: exact, not rounded
    assert n("-3") == -3 and n("+3") == 3 and n(".5") == mod.Fraction(1, 2) and n("5.") == 5
    for bad in (" 1", "1 ", "1_000", "0x10", "1e", "e1", "1.2.3", "nan", "inf", "", "1/2"):
        assert n(bad) is None, bad
    assert mod.play_id_order_class("1e400") == "finite"
    assert mod.play_id_order_class("inf") == "non_finite"
    assert mod.play_id_order_class(" 1") == "non_numeric"


def test_l2_equivalent_nested_nan_drives_extend_one_run(tmp_path):
    nan = float("nan")
    rows = alternating_game(DEFAULT_POSSESSIONS)
    for r in rows:
        r["drive"] = [nan] if r["drive"] == 1.0 else [float(r["drive"])]
        r["fixed_drive"] = None
    path = write_parquet(tmp_path, rows)
    result = run(path, possession=mod.PossessionRequest(AWAY, 1))
    assert len(result["possession"]["runs"]) == 5  # the [nan] rows formed ONE run
    assert result["possession"]["runs"][0]["attributed_row_count"] == 3
    assert result["possession"]["selection"]["reason"] == "provider_drive_not_orderable"


# One shared case set, every stage: the invariant behind H, I, J, K, and L.
_SHARED_VALUES: list[Any] = [
    None, float("nan"), float("inf"), float("-inf"), True, 0, 0.0, -0.0, 1, 1.0, 2,
    9007199254740992, 9007199254740993, "9007199254740993", "9007199254740993.0",
    "9007199254740993e0", "0.1", 0.1, "inf", "nan", "oops", "", " 1", b"1",
    [1], [1.0], (1,), [0.0], [-0.0], [float("nan")], [None], {"a": 1}, {"a": 1.0},
    {"a": float("nan")}, {"a": [float("nan"), 1.0]},
]


def test_cross_stage_equivalence_and_order_are_consistent():
    values = _SHARED_VALUES
    for left in values:
        for right in values:
            eq = mod._values_equal(left, right)
            assert eq is mod._values_equal(right, left), (left, right)  # symmetric
            assert (mod._freeze(left) == mod._freeze(right)) is eq, (left, right)
            hash(mod._freeze(left))
        assert mod._values_equal(left, left)  # reflexive, NaN included
    # Order evidence: exactly the "finite" class has a numeric value, and ordering by the
    # sort key equals ordering by that exact numeric value.
    finite = [v for v in values if mod.play_id_order_class(v) == "finite"]
    assert all(mod._play_id_numeric(v) is not None for v in finite)
    assert all(
        mod._play_id_numeric(v) is None for v in values if mod.play_id_order_class(v) != "finite"
    )
    by_key = sorted(finite, key=lambda v: mod._play_sort_key({"play_id": v}))
    by_exact = sorted(finite, key=lambda v: mod._play_id_numeric(v))
    assert [mod._play_id_numeric(v) for v in by_key] == [mod._play_id_numeric(v) for v in by_exact]
    assert mod._play_id_numeric("9007199254740993.0") > mod._play_id_numeric(9007199254740992)
    assert mod._play_id_numeric(9007199254740993) == mod._play_id_numeric("9007199254740993e0")


def test_cross_stage_run_extension_grouping_and_counts_share_one_relation(tmp_path):
    # Every pair of equivalent drive values must extend a run, group under one key, and
    # count once; every non-equivalent pair must split.
    nan = float("nan")
    pairs = [
        # scalar drives (M1: the scalar NaN/null pair must split exactly like the nested one)
        (nan, nan, True), (0.0, -0.0, True), (1.0, 2.0, False), (nan, None, False),
        (None, None, True),
        # nested drives
        ([nan], [nan], True), ([0.0], [-0.0], True), ([1.0], [2.0], False), ([nan], [None], False),
    ]
    for left, right, same in pairs:
        rows = [play(1.0, HOME, 9.0), play(2.0, HOME, 9.0)]
        rows[0]["drive"], rows[1]["drive"] = left, right
        rows[0]["fixed_drive"] = rows[1]["fixed_drive"] = None
        path = write_parquet(tmp_path, rows, name=f"pair_{abs(hash(repr((left, right))))}.parquet")
        content = path.read_bytes()
        loaded, _ = mod.load_game_rows(content, SYN_GAME_ID)
        seq = mod.build_possession_sequence(loaded, mod.inspect_schema(content))
        assert (len(seq["runs"]) == 1) is same, (left, right)
        assert (len(seq["drive_occurrence_counts"]) == 1) is same, (left, right)
        assert (mod._freeze(left) == mod._freeze(right)) is same, (left, right)


# ---------------------------------------------------------------------------
# Codex exact-head review of cf9afee (PR #269): M1 scalar NaN drive collapsed into null
# before run extension
# ---------------------------------------------------------------------------


def test_m1_scalar_nan_and_null_drives_are_distinct_runs_with_raw_values(tmp_path):
    # Codex's case: consecutive same-team rows with drive NaN then drive null.
    rows = [play(1.0, HOME, float("nan")), play(2.0, HOME, None), play(3.0, HOME, None)]
    path = write_parquet(tmp_path, rows)
    content = path.read_bytes()
    loaded, _ = mod.load_game_rows(content, SYN_GAME_ID)
    seq = mod.build_possession_sequence(loaded, mod.inspect_schema(content))
    runs = seq["runs"]
    assert len(runs) == 2  # NaN versus null is not equivalent: two runs, not one
    assert mod._is_nan(runs[0]["provider_drive"])  # raw NaN kept, not collapsed to None
    assert runs[1]["provider_drive"] is None and runs[1]["attributed_row_count"] == 2
    assert seq["drive_occurrence_counts"] == {"<nan>": 1, "None": 1}
    # Selection treats both as a missing drive number; neither certifies a possession.
    for ordinal in (1, 2):
        selection = mod.select_possession(seq, mod.PossessionRequest(HOME, ordinal))
        assert selection["status"] == "unresolved"
        assert selection["reason"] == "null_provider_drive_in_possession"
    # The NaN envelope is applied only at the output boundary.
    result = run(path, possession=mod.PossessionRequest(HOME, 2))
    text, _ = mod.dumps_bounded(result)
    emitted = [r["provider_drive"] for r in json.loads(text)["possession"]["runs"]]
    assert emitted == [{"float_nan": True}, None]
    assert result["events"]["status"] == "withheld"


def test_m1_nan_drive_earlier_in_prefix_withholds_like_a_null_drive(tmp_path):
    rows = alternating_game(DEFAULT_POSSESSIONS)
    for r in rows:
        if r["drive"] == 1.0:
            r["drive"] = float("nan")
            r["fixed_drive"] = float("nan")
    path = write_parquet(tmp_path, rows)
    result = run(path, possession=mod.PossessionRequest(HOME, 1))
    selection = result["possession"]["selection"]
    assert selection["reason"] == "null_provider_drive_in_prefix"
    assert selection["affected_runs"] == [1]
    assert mod._is_nan(result["possession"]["runs"][0]["provider_drive"])
    assert result["events"]["status"] == "withheld"


def test_m1_unattributed_row_with_nan_drive_is_neutral_like_a_null_drive(tmp_path):
    rows = alternating_game(DEFAULT_POSSESSIONS)
    rows.insert(4, play(4.5, None, float("nan"), desc="SYNTHETIC timeout, NaN drive"))
    path = write_parquet(tmp_path, rows)
    result = run(path, possession=mod.PossessionRequest(HOME, 2))
    assert result["possession"]["selection"]["status"] == "resolved"
    assert result["possession"]["unattributed_rows"] == 1
    content = path.read_bytes()
    loaded, _ = mod.load_game_rows(content, SYN_GAME_ID)
    seq = mod.build_possession_sequence(loaded, mod.inspect_schema(content))
    assert mod._is_nan(seq["unattributed"][0]["drive"])  # raw value kept, not collapsed


# ---------------------------------------------------------------------------
# Codex exact-head review of bd87222 (PR #269): N1 numeric game_id predicate, N2 exact
# drive monotonicity
# ---------------------------------------------------------------------------


def test_n1_numeric_game_id_is_read_with_a_typed_predicate(tmp_path):
    # Codex's case: an Int64 game_id column. The match must stay typed so every game scan
    # compares like with like instead of failing on a string-versus-integer predicate.
    rows = alternating_game(DEFAULT_POSSESSIONS)
    for r in rows:
        r["game_id"] = 123
    path = write_parquet(tmp_path, rows)
    result = run(path, possession=mod.PossessionRequest(HOME, 2))
    assert result["status"] == "read", result.get("rejection") or result.get("failure")
    assert result["game"]["observed"]["game_id"] == 123
    assert result["game"]["game_id_predicate"]["python_type"] == "int"
    assert "_game_id_raw" not in result["game"]
    assert result["inventory"]["keys"]["row_count"] == len(rows)
    assert result["inventory"]["read_strategy"]["selection_pushed_into_scan"] is True
    assert result["possession"]["selection"]["status"] == "resolved"
    assert result["possession"]["selection"]["selected_run"]["provider_drive"] == 4.0
    assert result["events"]["status"] == "emitted"
    assert all(e["game_id"] == 123 for e in result["events"]["rows"])
    assert json.loads(mod.dumps_bounded(result)[0])["game"]["observed"]["game_id"] == 123


def test_n1_numeric_game_id_twins_and_neighbours_keep_typed_identity(tmp_path):
    rows = alternating_game(DEFAULT_POSSESSIONS)
    for r in rows:
        r["game_id"] = 123
    other = [dict(r, game_id=124, home_team="SYD", away_team="SYC") for r in rows]
    path = write_parquet(tmp_path, rows + other)
    result = run(path)
    assert result["status"] == "read"
    assert result["game"]["observed"]["game_id"] == 123
    assert result["inventory"]["keys"]["row_count"] == len(rows)  # no neighbour rows leaked
    twin = [dict(r, game_id=124) for r in rows]
    path = write_parquet(tmp_path, rows + twin, name="twins.parquet")
    result = run(path)
    assert result["game"]["reason"] == "multiple_matching_games"
    assert result["game"]["diagnostics"]["matching_game_ids"] == [123, 124]


def test_n2_large_int64_drives_compare_exactly_in_monotonicity_check(tmp_path):
    big, small = 9007199254740993, 9007199254740992  # float() collapses these onto one value
    # Codex's case: a decreasing Int64 drive prefix that float conversion would hide.
    rows = [play(1, AWAY, big), play(2, AWAY, big), play(3, HOME, small), play(4, HOME, small)]
    path = write_parquet(tmp_path, rows)
    result = run(path, possession=mod.PossessionRequest(HOME, 1))
    selection = result["possession"]["selection"]
    assert selection["status"] == "unresolved"
    assert selection["reason"] == "provider_drive_order_non_monotone"
    assert result["events"]["status"] == "withheld"
    # The exact ascending order still resolves.
    rows = [play(1, AWAY, small), play(2, AWAY, small), play(3, HOME, big), play(4, HOME, big)]
    path = write_parquet(tmp_path, rows, name="ascending.parquet")
    result = run(path, possession=mod.PossessionRequest(HOME, 1))
    assert result["possession"]["selection"]["status"] == "resolved"
    assert result["possession"]["selection"]["selected_run"]["provider_drive"] == big


def test_n2_drive_orderability_uses_the_shared_classifier(tmp_path):
    # bytes parse under float() but are never drive evidence; the shared classifier says so.
    rows = alternating_game(DEFAULT_POSSESSIONS)
    for r in rows:
        r["drive"] = str(int(r["drive"])).encode()
        r["fixed_drive"] = None
    path = write_parquet(tmp_path, rows)
    result = run(path, possession=mod.PossessionRequest(HOME, 1))
    assert result["possession"]["selection"]["reason"] == "provider_drive_not_orderable"
    assert result["events"]["status"] == "withheld"
    # Integer-valued numeric strings remain orderable and compare exactly.
    rows = alternating_game(DEFAULT_POSSESSIONS)
    for r in rows:
        r["drive"] = f"{int(r['drive']) + 9007199254740990}.0"
        r["fixed_drive"] = None
    path = write_parquet(tmp_path, rows, name="strings.parquet")
    result = run(path, possession=mod.PossessionRequest(HOME, 2))
    assert result["possession"]["selection"]["status"] == "resolved"
    for r in result["possession"]["runs"]:
        assert mod._play_id_numeric(r["provider_drive"]) == mod._play_id_numeric(
            f"{r['sequence_index'] + 9007199254740990}"
        )


# ---------------------------------------------------------------------------
# Codex exact-head review of 7d55214 (PR #269): O1 unbounded numeric-string exponent,
# O2 non-finite Float64 game_id certified as a match
# ---------------------------------------------------------------------------


def test_o1_numeric_strings_outside_the_bounded_domain_are_not_order_evidence():
    n = mod._play_id_numeric
    # Codex's case: a tiny string that would expand into a billion-digit integer.
    assert n("1e999999999") is None
    assert n("1e-999999999") is None
    assert n("-1E+999999999") is None
    assert n("0e999999999") == 0  # zero has no magnitude; it stays inside the domain
    # The edges of the bounded domain are exact and inclusive.
    assert n("1e4000") == 10**4000 and n("1e4001") is None
    assert n("1e-4000") == mod.Fraction(1, 10**4000) and n("1e-4001") is None
    assert n("9" * 4000) == int("9" * 4000) and n("9" * 4001) is None
    assert n("1." + "0" * 3999) == 1 and n("1." + "0" * 4000) is None
    # Outside the domain a numeric spelling is an unknown order position, never expanded.
    assert mod.play_id_order_class("1e999999999") == "non_numeric"
    assert mod.play_id_order_class("1e-999999999") == "non_numeric"
    assert mod.play_id_order_class("1e4000") == "finite"
    assert mod.play_id_order_class("inf") == "non_finite"  # not a numeric spelling


def test_o1_out_of_domain_play_id_string_withholds_selection_promptly(tmp_path):
    import time

    rows = alternating_game(DEFAULT_POSSESSIONS)
    for r in rows:
        r["play_id"] = str(int(r["play_id"]))
    rows[10]["play_id"] = "1e999999999"  # inside HOME drive 4
    path = write_parquet(tmp_path, rows)
    started = time.monotonic()
    result = run(path, possession=mod.PossessionRequest(HOME, 2))
    assert time.monotonic() - started < 10
    assert result["status"] == "read"
    assert result["possession"]["play_id_non_numeric_rows"] == 1
    selection = result["possession"]["selection"]
    assert selection["status"] == "unresolved"
    assert selection["reason"] == "non_numeric_play_id_breaks_play_order"
    assert result["events"]["status"] == "withheld"
    assert json.loads(mod.dumps_bounded(result)[0])["status"] == "read"


def test_o1_row_sort_is_a_bounded_processing_stage(tmp_path, monkeypatch):
    assert "sort_game_rows" in mod.PROCESSING_STAGES
    assert "sort_game_rows" not in mod.ENGINE_STAGES
    path = write_parquet(tmp_path, alternating_game(DEFAULT_POSSESSIONS))

    def broken(row):
        raise RuntimeError("SYNTHETIC sort defect")

    monkeypatch.setattr(mod, "_play_sort_key", broken)
    result = run(path, possession=mod.PossessionRequest(HOME, 2))
    assert result["status"] == "processing_failed"
    assert result["rejection"] is None
    assert result["failure"]["kind"] == "reader_processing_failure"
    assert result["failure"]["stage"] == "sort_game_rows"
    assert result["failure"]["parsed"] == "succeeded"
    assert result["game"]["status"] == "matched"


@pytest.mark.parametrize("bad_id", [float("nan"), float("inf"), float("-inf")])
def test_o2_non_finite_game_id_is_never_certified(tmp_path, bad_id):
    rows = alternating_game(DEFAULT_POSSESSIONS)
    for r in rows:
        r["game_id"] = bad_id
    path = write_parquet(tmp_path, rows)
    result = run(path, possession=mod.PossessionRequest(HOME, 2))
    assert result["status"] == "unresolved"
    assert result["game"]["status"] == "unresolved"
    assert result["game"]["reason"] == "matching_identity_without_game_id"
    assert result["game"]["diagnostics"]["matching_tuples_with_non_finite_game_id"] == 1
    assert result["game"]["diagnostics"]["matching_tuples_without_game_id"] == 0
    assert result["game"]["observed"] is None
    assert result["inventory"] is None and result["events"] is None
    assert "_game_id_raw" not in result["game"]
    json.loads(mod.dumps_bounded(result)[0])


def test_o2_non_finite_twin_withholds_the_real_finite_match_too(tmp_path):
    rows = alternating_game(DEFAULT_POSSESSIONS)
    for r in rows:
        r["game_id"] = 123.0
    rows.append(play(99.0, HOME, 9.0, game_id=float("nan")))
    path = write_parquet(tmp_path, rows)
    result = run(path)
    assert result["game"]["reason"] == "matching_identity_without_game_id"
    assert result["game"]["diagnostics"]["matching_tuples_with_non_finite_game_id"] == 1
    assert result["events"] is None
    # A finite Float64 ID alone still matches with a typed predicate.
    path = write_parquet(tmp_path, rows[:-1], name="finite.parquet")
    result = run(path)
    assert result["status"] == "read"
    assert result["game"]["observed"]["game_id"] == 123.0
    assert result["game"]["game_id_predicate"]["python_type"] == "float"


# ---------------------------------------------------------------------------
# Codex exact-head review of fd31ffd (PR #269): P1 exponent spelling overflowed Decimal,
# P2 magnitude ceiling enforced on the adjusted exponent instead of the exact value
# ---------------------------------------------------------------------------


def test_p1_absurd_exponent_spellings_are_bounded_before_decimal_construction():
    n = mod._play_id_numeric
    # Codex's case: passes the grammar, overflowed the decimal module's exponent range.
    for text in ("1e9999999999999999999", "1e-9999999999999999999", "0.5E+" + "9" * 40):
        assert n(text) is None, text
        assert mod.play_id_order_class(text) == "non_numeric", text
    assert n("0e9999999999999999999") == 0  # zero stays zero without touching Decimal
    assert n("1e000000000000000000004000") == 10**4000  # leading exponent zeros are harmless


@pytest.mark.parametrize("field", ["play_id", "drive"])
def test_p1_absurd_exponent_in_source_withholds_instead_of_processing_failure(tmp_path, field):
    rows = alternating_game(DEFAULT_POSSESSIONS)
    for r in rows:
        r[field] = str(int(r[field]))
        if field == "drive":
            r["fixed_drive"] = None
    for r in rows[:3]:
        r[field] = "1e9999999999999999999"
    path = write_parquet(tmp_path, rows)
    result = run(path, possession=mod.PossessionRequest(HOME, 1))
    assert result["status"] == "read", result.get("failure")
    assert result["failure"] is None
    selection = result["possession"]["selection"]
    assert selection["status"] == "unresolved"
    expected = (
        "non_numeric_play_id_breaks_play_order" if field == "play_id"
        else "provider_drive_not_orderable"
    )
    assert selection["reason"] == expected
    assert result["events"]["status"] == "withheld"


def test_p2_magnitude_ceiling_and_floor_are_exact_and_inclusive():
    n = mod._play_id_numeric
    # Above the ceiling with the same adjusted exponent as the ceiling itself.
    for text in ("1.1e4000", "9e4000", "9.99e4000", "10001e3996", "-1.1e4000"):
        assert n(text) is None, text
        assert mod.play_id_order_class(text) == "non_numeric", text
    # Exactly at the ceiling, however spelled, is inside.
    for text in ("1e4000", "0.1e4001", "10e3999", "10000e3996", "1.0e4000", "-1e4000"):
        assert abs(n(text)) == 10**4000, text
    # Below the floor with the same adjusted exponent as the floor itself.
    for text in ("0.9e-4000", "9e-4001", "1e-4001"):
        assert n(text) is None, text
    for text in ("1e-4000", "10e-4001", "0.1e-3999"):
        assert n(text) == mod.Fraction(1, 10**4000), text


@pytest.mark.parametrize("field", ["play_id", "drive"])
def test_p2_value_above_the_ceiling_withholds_selection(tmp_path, field):
    rows = alternating_game(DEFAULT_POSSESSIONS)
    for r in rows:
        r[field] = str(int(r[field]))
        if field == "drive":
            r["fixed_drive"] = None
    for r in rows[3:7]:  # HOME drive 2
        r[field] = "1.1e4000"
    path = write_parquet(tmp_path, rows)
    result = run(path, possession=mod.PossessionRequest(HOME, 1))
    assert result["status"] == "read"
    selection = result["possession"]["selection"]
    assert selection["status"] == "unresolved"
    assert result["events"]["status"] == "withheld"
    # The ceiling itself still orders exactly.
    for r in rows[3:7]:
        r[field] = "1e4000"
    if field == "play_id":
        return  # play IDs must stay unique and ascending; the drive case covers the ceiling
    path = write_parquet(tmp_path, rows, name="ceiling.parquet")
    result = run(path, possession=mod.PossessionRequest(HOME, 1))
    assert result["possession"]["selection"]["status"] == "resolved"
    assert mod._play_id_numeric(
        result["possession"]["selection"]["selected_run"]["provider_drive"]
    ) == 10**4000


# ---------------------------------------------------------------------------
# Codex exact-head review of 542593f (PR #269): Q1 raw game_id in the emitted-key set
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("kind", ["list", "struct"])
def test_q1_non_scalar_game_id_reads_and_emits_with_frozen_key_count(tmp_path, kind):
    # Codex's case: a List(Int64) or Struct game_id matched and loaded, then failed at
    # select_events because the raw ID went into a set. A parquet column has one type, so
    # every row carries the non-scalar ID.
    game_id = [1999, 1] if kind == "list" else {"season": 1999, "n": 1}
    rows = alternating_game(DEFAULT_POSSESSIONS)
    for r in rows:
        r["game_id"] = game_id
    path = write_parquet(tmp_path, rows)
    result = run(path, possession=mod.PossessionRequest(HOME, 2))
    assert result["status"] == "read", result.get("failure")
    assert result["failure"] is None
    assert result["game"]["status"] == "matched"
    assert result["game"]["observed"]["game_id"] == game_id
    expected_type = "list" if kind == "list" else "dict"
    assert result["game"]["game_id_predicate"]["python_type"] == expected_type
    assert result["inventory"]["keys"]["row_count"] == len(rows)
    assert result["inventory"]["keys"]["distinct_game_play_key_count"] == len(rows)
    selection = result["possession"]["selection"]
    assert selection["status"] == "resolved"
    assert selection["selected_run"]["provider_drive"] == 4.0
    events = result["events"]
    assert events["status"] == "emitted"
    assert events["row_count"] == 5
    assert events["distinct_game_play_key_count"] == 5  # frozen key, same as inventory
    assert all(e["game_id"] == game_id for e in events["rows"])
    assert json.loads(mod.dumps_bounded(result)[0])["events"]["distinct_game_play_key_count"] == 5


def test_q1_emitted_key_count_uses_the_shared_grouping_key():
    # Two rows with value-equal list game IDs and value-equal float play IDs are one key
    # under the shared rule, exactly as duplicate inventory counts them.
    rows = [play(0.0, HOME, 2.0), play(-0.0, HOME, 2.0)]
    rows[0]["game_id"], rows[1]["game_id"] = [0.0], [-0.0]
    selection = {
        "status": "resolved",
        "selected_run": {"first_index": 0, "last_index": 1},
    }
    events = mod.select_events(rows, selection, {k: "x" for k in rows[0]})
    assert events["row_count"] == 2
    assert events["distinct_game_play_key_count"] == 1
    assert events["distinct_game_play_key_count"] == len({mod._grouping_key(r) for r in rows})


# ---------------------------------------------------------------------------
# Codex exact-head review of 75797cb (PR #269): R1 empty/blank Binary game_id certified,
# R2 frozen game_id reported for duplicate keys
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("bad_id", [b"", b"   ", b"\t\n"])
def test_r1_empty_or_blank_binary_game_id_is_never_certified(tmp_path, bad_id):
    rows = alternating_game(DEFAULT_POSSESSIONS)
    for r in rows:
        r["game_id"] = bad_id
    path = write_parquet(tmp_path, rows)
    result = run(path, possession=mod.PossessionRequest(HOME, 2))
    assert result["status"] == "unresolved"
    assert result["game"]["status"] == "unresolved"
    assert result["game"]["reason"] == "matching_identity_without_game_id"
    assert result["game"]["diagnostics"]["matching_tuples_without_game_id"] == 1
    assert result["game"]["observed"] is None
    assert result["inventory"] is None and result["events"] is None


def test_r1_non_blank_binary_game_id_still_matches_with_a_typed_predicate(tmp_path):
    rows = alternating_game(DEFAULT_POSSESSIONS)
    for r in rows:
        r["game_id"] = b"SYN_1999_01"
    other = [dict(r, game_id=b"", home_team="SYD", away_team="SYC") for r in rows]
    path = write_parquet(tmp_path, rows + other)
    result = run(path, possession=mod.PossessionRequest(HOME, 2))
    assert result["status"] == "read", result.get("rejection") or result.get("failure")
    assert result["game"]["observed"]["game_id"] == {
        "bytes_hex": b"SYN_1999_01".hex(), "byte_length": 11
    }
    assert result["game"]["game_id_predicate"]["python_type"] == "bytes"
    assert result["inventory"]["keys"]["row_count"] == len(rows)  # the blank-ID game did not leak
    assert result["possession"]["selection"]["status"] == "resolved"
    assert result["events"]["status"] == "emitted"


def test_r1_blank_check_judges_content_not_rendering():
    blank = mod._game_id_blank
    assert blank(None) and blank("") and blank("   ") and blank(b"") and blank(b" \t ")
    assert blank(bytearray(b"  ")) and blank(memoryview(b""))
    assert not blank(b"x") and not blank("x") and not blank(0) and not blank([])
    assert not blank(b"b''")  # the literal text of a rendering is itself non-blank content


@pytest.mark.parametrize("kind", ["list", "struct"])
def test_r2_duplicate_key_reports_report_the_raw_game_id(tmp_path, kind):
    game_id = [1999, 1] if kind == "list" else {"season": 1999, "n": 1}
    rows = alternating_game(DEFAULT_POSSESSIONS)
    for r in rows:
        r["game_id"] = game_id
    rows.append(dict(rows[0]))  # identical duplicate of the first play
    rows.append(dict(rows[1], yards_gained=99.0))  # conflicting duplicate of the second
    path = write_parquet(tmp_path, rows)
    result = run(path)
    keys = result["inventory"]["keys"]
    assert keys["identical_duplicate_keys"] == [
        {"game_id": game_id, "play_id": 1.0, "occurrences": 2}
    ]
    assert len(keys["conflicting_duplicate_keys"]) == 1
    conflict = keys["conflicting_duplicate_keys"][0]
    assert conflict["game_id"] == game_id and conflict["play_id"] == 2.0
    assert conflict["differing_columns"] == ["yards_gained"]
    # No frozen-key sentinel or type tag reaches the output.
    text = mod.dumps_bounded(result)[0]
    assert "<seq>" not in text and "<map>" not in text and "<nan>" not in text
    assert result["game"]["observed"]["game_id"] == game_id


# ---------------------------------------------------------------------------
# Codex exact-head review of c134a0e (PR #269): S1 numerically tied play-ID spellings,
# S2 numerically equal drive spellings, S3 whitespace-only team requests
# ---------------------------------------------------------------------------


def test_s1_distinct_spellings_of_one_play_id_withhold_selection(tmp_path):
    # Codex's case: consecutive HOME rows at "1" and "1.0" with drives 1 and 2 resolved
    # possession #2 on an arbitrary physical order.
    rows = [play("1", HOME, "1"), play("1.0", HOME, "2")]
    for r in rows:
        r["fixed_drive"] = None
    path = write_parquet(tmp_path, rows)
    result = run(path, possession=mod.PossessionRequest(HOME, 2))
    assert result["status"] == "read"
    assert result["possession"]["play_id_tied_rows"] == 2
    selection = result["possession"]["selection"]
    assert selection["status"] == "unresolved"
    assert selection["reason"] == "tied_play_id_breaks_play_order"
    assert result["events"]["status"] == "withheld"
    assert result["inventory"]["keys"]["identical_duplicate_keys"] == []  # a tie is not a duplicate


@pytest.mark.parametrize("spelling", ["01", "1e0", "+1", "1.00"])
def test_s1_every_alternate_spelling_ties_with_the_plain_one(tmp_path, spelling):
    rows = alternating_game(DEFAULT_POSSESSIONS)
    for r in rows:
        r["play_id"] = str(int(r["play_id"]))
    rows[1]["play_id"] = spelling  # numerically equal to rows[0]'s "1"
    path = write_parquet(tmp_path, rows)
    result = run(path, possession=mod.PossessionRequest(HOME, 2))
    assert result["possession"]["play_id_tied_rows"] == 2
    assert result["possession"]["selection"]["reason"] == "tied_play_id_breaks_play_order"
    assert result["events"]["status"] == "withheld"


def test_s1_identical_spellings_are_duplicates_not_ties_and_distinct_values_still_order(tmp_path):
    rows = alternating_game(DEFAULT_POSSESSIONS)
    for r in rows:
        r["play_id"] = str(int(r["play_id"]))
    rows.append(dict(rows[0]))  # identical duplicate of "1": inventory, not a tie
    path = write_parquet(tmp_path, rows)
    result = run(path, possession=mod.PossessionRequest(HOME, 2))
    assert result["possession"]["play_id_tied_rows"] == 0
    assert result["inventory"]["keys"]["identical_duplicate_keys"][0]["play_id"] == "1"
    assert result["possession"]["selection"]["status"] == "resolved"
    # Mixed spellings of DIFFERENT values are ordinary exact ordering, not ties.
    rows = alternating_game(DEFAULT_POSSESSIONS)
    for i, r in enumerate(rows):
        r["play_id"] = f"{int(r['play_id'])}.0" if i % 2 else str(int(r["play_id"]))
    path = write_parquet(tmp_path, rows, name="mixed.parquet")
    result = run(path, possession=mod.PossessionRequest(HOME, 2))
    assert result["possession"]["play_id_tied_rows"] == 0
    assert result["possession"]["selection"]["status"] == "resolved"
    assert result["possession"]["selection"]["selected_run"]["provider_drive"] == 4.0


def test_s2_distinct_spellings_of_one_drive_withhold_the_possession_whose_prefix_has_both(tmp_path):
    # Codex's case: HOME drive "2" continues as "2.0"; the ordinal never evidently advanced.
    rows = alternating_game(DEFAULT_POSSESSIONS)
    for r in rows:
        r["drive"] = str(int(r["drive"]))
        r["fixed_drive"] = None
    rows[5]["drive"] = rows[6]["drive"] = "2.0"  # last two plays of HOME drive 2
    path = write_parquet(tmp_path, rows)
    result = run(path, possession=mod.PossessionRequest(HOME, 2))
    assert len(result["possession"]["runs"]) == 6  # raw equality still splits the runs
    selection = result["possession"]["selection"]
    assert selection["status"] == "unresolved"
    assert selection["reason"] == "provider_drive_spelling_ambiguous"
    assert selection["affected_runs"] == [2, 3]
    assert result["events"]["status"] == "withheld"
    # HOME #1's prefix (AWAY "1", HOME "2") contains no ambiguity and still resolves.
    result = run(path, possession=mod.PossessionRequest(HOME, 1))
    assert result["possession"]["selection"]["status"] == "resolved"
    assert result["possession"]["selection"]["selected_run"]["provider_drive"] == "2"
    # Every later possession carries the ambiguity in its prefix.
    result = run(path, possession=mod.PossessionRequest(AWAY, 2))
    assert result["possession"]["selection"]["reason"] == "provider_drive_spelling_ambiguous"


def test_s2_consistent_numeric_string_drives_still_resolve(tmp_path):
    rows = alternating_game(DEFAULT_POSSESSIONS)
    for r in rows:
        r["drive"] = f"{int(r['drive'])}.0"
        r["fixed_drive"] = None
    path = write_parquet(tmp_path, rows)
    result = run(path, possession=mod.PossessionRequest(HOME, 2))
    assert result["possession"]["selection"]["status"] == "resolved"
    assert result["possession"]["selection"]["selected_run"]["provider_drive"] == "4.0"


@pytest.mark.parametrize("blank", ["", " ", "   ", "\t\n"])
def test_s3_blank_team_codes_are_usage_errors_before_file_access(tmp_path, blank, monkeypatch):
    monkeypatch.setattr(pl, "scan_parquet", lambda *a, **k: pytest.fail("file accessed"))
    monkeypatch.setattr(pl, "read_parquet_schema", lambda *a, **k: pytest.fail("file accessed"))
    for away, home in ((blank, HOME), (AWAY, blank)):
        request = mod.GameRequest(
            season=SYN_SEASON, game_date=SYN_DATE, away_team=away, home_team=home
        )
        with pytest.raises(ValueError, match="must not be blank"):
            request.validate()
    with pytest.raises(ValueError, match="must not be blank"):
        mod.PossessionRequest(team=blank, ordinal=1).validate()
    assert not mod._team_code_present(blank) and mod._team_code_present("SYA")
    assert not mod._team_code_present(None) and not mod._team_code_present(3)


def test_s3_blank_team_request_never_matches_a_blank_source_identity(tmp_path):
    rows = alternating_game(DEFAULT_POSSESSIONS)
    for r in rows:
        r["home_team"] = "   "
    path = write_parquet(tmp_path, rows)
    out = tmp_path / "out.json"
    args = _cli_args(path, out)
    args[args.index("--home") + 1] = "   "
    completed = _cli(args)
    assert completed.returncode == 3, completed.stderr
    assert "must not be blank" in completed.stderr
    assert not out.exists()
    # The same blank request through the library is rejected before verification.
    request = mod.GameRequest(
        season=SYN_SEASON, game_date=SYN_DATE, away_team=AWAY, home_team="   "
    )
    with pytest.raises(ValueError):
        request.validate()


@pytest.mark.parametrize("unknown_team", [None, "", "   ", "\t\n"])
def test_t1_unknown_source_team_on_its_own_drive_withholds_ordinal(tmp_path, unknown_team):
    rows = [play(1, HOME, 1), play(2, unknown_team, 2), play(3, HOME, 3)]
    path = write_parquet(tmp_path, rows)
    result = run(path, possession=mod.PossessionRequest(HOME, 2))
    assert result["game"]["status"] == "matched"
    assert result["possession"]["unattributed_rows"] == 1
    assert [r["posteam"] for r in result["possession"]["runs"]] == [HOME, HOME]
    selection = result["possession"]["selection"]
    assert selection["status"] == "unresolved"
    assert selection["reason"] == "unattributed_drive_value_in_prefix"
    assert selection["affected_play_ids"] == [2]
    assert result["events"]["status"] == "withheld"
    assert result["events"]["rows"] == []


@pytest.mark.parametrize("unknown_team", [None, "", "   ", "\t\n"])
def test_t1_unknown_source_team_inside_known_drive_preserves_raw_value(tmp_path, unknown_team):
    rows = [play(1, HOME, 1), play(2, unknown_team, 1), play(3, HOME, 1)]
    path = write_parquet(tmp_path, rows)
    result = run(path, possession=mod.PossessionRequest(HOME, 1))
    assert result["possession"]["selection"]["status"] == "resolved"
    assert result["possession"]["unattributed_rows"] == 1
    assert len(result["possession"]["runs"]) == 1
    assert result["events"]["unattributed_rows_in_window"] == 1
    assert result["events"]["row_count"] == 3
    serialized = json.loads(mod.dumps(result))
    assert serialized["events"]["rows"][1]["fields"]["posteam"] == unknown_team

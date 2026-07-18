"""Offline test matrix for the bounded 2015-2020 player-season candidate builder.

Implements the normative matrix from SS14 of
docs/design/player-season-coverage-v0-2015-2020-candidate-build-spec.md
(TIBER-Data #220 design, #222 G2 implementation activation): positive tests
P-1..P-8, fail-closed tests N-*, boundary-acceptance tests B-1..B-4, and
invariant/guard tests G-1..G-8. All tests use injected fixtures; no network
access occurs, and publication logic is exercised only inside isolated
temporary directories.
"""

from __future__ import annotations

import hashlib
import json
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
GEN_AT = "2026-07-18T00:00:00+00:00"

BASE_PLAYERS = [
    ("00-1", "QB"),
    ("00-2", "RB"),
    ("00-3", "WR"),
    ("00-4", "TE"),
]

_REG_STAT_FIELDS = {
    "completions": 0,
    "attempts": 0,
    "passing_yards": 0,
    "passing_tds": 0,
    "passing_interceptions": 0,
    "carries": 0,
    "rushing_yards": 0,
    "rushing_tds": 0,
    "receptions": 0,
    "targets": 0,
    "receiving_yards": 0,
    "receiving_tds": 0,
    "receiving_air_yards": 0,
    "target_share": 0.0,
    "air_yards_share": 0.0,
    "wopr": 0.0,
    "racr": 0.0,
    "fantasy_points_ppr": 0.0,
}


def _load_module():
    module_path = REPO_ROOT / "scripts" / "build_player_season_coverage_2015_2020_candidate.py"
    spec = spec_from_file_location("build_player_season_coverage_2015_2020_candidate", module_path)
    assert spec is not None and spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _FakeFrame:
    def __init__(self, rows: list[dict], columns: list[str] | None = None) -> None:
        self.columns = columns if columns is not None else (list(rows[0].keys()) if rows else [])
        self._rows = rows

    def to_dicts(self) -> list[dict]:
        return self._rows


def _week_row(season: int, week: int, pid: str, team: str = "KC", season_type: str = "REG") -> dict:
    return {"season": season, "week": week, "player_id": pid, "team": team, "season_type": season_type}


def _season_week_rows(season: int, players=BASE_PLAYERS, weeks=range(1, 18), team: str = "KC") -> list[dict]:
    return [_week_row(season, week, pid, team) for pid, _pos in players for week in weeks]


def _reg_row(season: int, pid: str, pos: str, games: int = 16, **overrides) -> dict:
    row = {
        "season": season,
        "player_id": pid,
        "player_display_name": f"Player {pid}",
        "position": pos,
        "games": games,
        "season_type": "REG",
        **_REG_STAT_FIELDS,
    }
    row.update(overrides)
    return row


def _season_reg_rows(season: int, players=BASE_PLAYERS, games: int = 16) -> list[dict]:
    return [_reg_row(season, pid, pos, games=games) for pid, pos in players]


def _players_rows(players=BASE_PLAYERS, null_draft: bool = False) -> list[dict]:
    return [
        {
            "gsis_id": pid,
            "birth_date": "1992-01-01",
            "rookie_season": 2014,
            "draft_year": None if null_draft else 2014,
            "draft_round": None if null_draft else 1,
            "draft_pick": None if null_draft else 10,
            "draft_team": None if null_draft else "KC",
            "espn_id": 100,
        }
        for pid, _pos in players
    ]


def _frames(module, custom: dict | None = None) -> dict:
    frames: dict[int, dict] = {}
    for season in module.SEASONS:
        override = (custom or {}).get(season, {})
        frames[season] = {
            "week": _FakeFrame(override.get("week", _season_week_rows(season))),
            "reg": _FakeFrame(override.get("reg", _season_reg_rows(season))),
        }
    return frames


def _accepted_fp(module, frames: dict, players_frame: _FakeFrame) -> dict:
    index = module._load_players_index(players_frame)
    return {
        season: module.compute_observed_season_fingerprint(
            season, frames[season]["week"], frames[season]["reg"], index
        )
        for season in module.SEASONS
    }


def _build(
    module,
    frames: dict | None = None,
    players_rows: list[dict] | None = None,
    accepted_fp: dict | None = None,
    accepted_hashes: dict | None = None,
    fp_players_rows: list[dict] | None = None,
):
    frames = frames if frames is not None else _frames(module)
    players_frame = _FakeFrame(players_rows if players_rows is not None else _players_rows())
    if accepted_fp is None:
        fp_frame = _FakeFrame(fp_players_rows) if fp_players_rows is not None else players_frame
        accepted_fp = _accepted_fp(module, frames, fp_frame)
    return module.build_candidate_payload(
        frames,
        players_frame,
        GEN_AT,
        accepted_fingerprint=accepted_fp,
        accepted_source_content_hashes=accepted_hashes,
    )


_TEST_ENVIRONMENT = {
    "python_version": "3.x-test",
    "nflreadpy_version": "0.1.5",
    "polars_version": "test",
    "os_platform": "test-platform",
    "build_timestamp_utc": GEN_AT,
    "evidence_lock": {
        "accepted_main_sha": "251f2369bd5700d9a3afe66269aaae4a60d61fa8",
        "accepted_audit_script_blob": "529f832b050dba494146f4b133c202072f587c0e",
        "required_nflreadpy_version": "0.1.5",
    },
}


def _output_set(module, tmp_path: Path):
    payload, evidence = _build(module)
    return module.build_output_set(payload, evidence, _TEST_ENVIRONMENT, base_dir=tmp_path)


def _publish_contents(module, tmp_path: Path, tag: str) -> dict:
    paths = module.candidate_output_paths(tmp_path)
    return {path: f"{name}-{tag}\n" for name, path in paths.items()}


def _tree_files(base: Path) -> list[Path]:
    return sorted(p for p in base.rglob("*") if p.is_file())


# ---------------------------------------------------------------------------
# Positive tests P-1 .. P-8
# ---------------------------------------------------------------------------


def test_p1_six_clean_seasons_build_sorted_with_correct_counts() -> None:
    module = _load_module()
    payload, evidence = _build(module)
    assert payload["status"] == "candidate_evidence_artifact_not_promoted"
    assert payload["seasons"] == [2015, 2016, 2017, 2018, 2019, 2020]
    assert payload["season_type_scope"] == ["REG"]
    assert len(payload["records"]) == 24
    assert payload["row_counts_by_position"] == {"QB": 6, "RB": 6, "TE": 6, "WR": 6}
    assert payload["row_counts_by_season"] == {str(s): 4 for s in module.SEASONS}
    keys = [(r["season"], r["player_id"]) for r in payload["records"]]
    assert keys == sorted(keys)
    assert payload["identity_join_rate"] == 1.0
    assert evidence["accepted_fingerprint"][2015]["unique_players_all_positions"] == 4


def test_p2_per_season_isolation_observable_in_source_refs_and_calls() -> None:
    module = _load_module()
    payload, evidence = _build(module)
    for record in payload["records"]:
        season = record["season"]
        names = [ref["source_name"] for ref in record["source_refs"]]
        assert f"nflreadpy.load_player_stats(seasons=[{season}], summary_level='reg')" in names
        assert f"nflreadpy.load_player_stats(seasons=[{season}], summary_level='week')" in names
        assert "nflreadpy.load_players()" in names
    assert len(evidence["source_calls_executed"]) == 13  # 6 week + 6 reg + 1 players
    for season in module.SEASONS:
        assert (
            f"nflreadpy.load_player_stats(seasons=[{season}], summary_level='week')"
            in evidence["source_calls_executed"]
        )


def test_p3_exact_weeks_1_17_accepted_for_every_season_independently() -> None:
    module = _load_module()
    payload, _ = _build(module)
    for record in payload["records"]:
        assert record["weeks_observed"] == 17
        assert "of up to 17 REG week numbers" in record["coverage_notes"]


def test_p4_historical_coverage_status_thresholds() -> None:
    module = _load_module()
    extras = [("00-5", "WR"), ("00-6", "WR"), ("00-7", "TE")]
    week_rows = (
        _season_week_rows(2015)
        + [_week_row(2015, w, "00-5") for w in range(1, 15)]
        + [_week_row(2015, w, "00-6") for w in range(1, 14)]
        + [_week_row(2015, 1, "00-7")]
    )
    reg_rows = _season_reg_rows(2015) + [
        _reg_row(2015, "00-5", "WR", games=14),
        _reg_row(2015, "00-6", "WR", games=13),
        _reg_row(2015, "00-7", "TE", games=1),
    ]
    players = _players_rows(BASE_PLAYERS + extras)
    payload, _ = _build(
        module,
        frames=_frames(module, {2015: {"week": week_rows, "reg": reg_rows}}),
        players_rows=players,
    )
    by_id = {(r["season"], r["player_id"]): r for r in payload["records"]}
    assert by_id[(2015, "00-5")]["coverage_status"] == "full_season"
    assert by_id[(2015, "00-6")]["coverage_status"] == "partial_season"
    assert by_id[(2015, "00-7")]["coverage_status"] == "single_week"


def test_p5_b3_multi_team_disjoint_weeks_17_games_accepted() -> None:
    module = _load_module()
    week_rows = (
        _season_week_rows(2019)
        + [_week_row(2019, w, "00-8", team="KC") for w in range(1, 9)]
        + [_week_row(2019, w, "00-8", team="SF") for w in range(9, 18)]
    )
    reg_rows = _season_reg_rows(2019) + [_reg_row(2019, "00-8", "WR", games=17)]
    players = _players_rows(BASE_PLAYERS + [("00-8", "WR")])
    payload, _ = _build(
        module,
        frames=_frames(module, {2019: {"week": week_rows, "reg": reg_rows}}),
        players_rows=players,
    )
    record = next(r for r in payload["records"] if r["player_id"] == "00-8")
    assert record["games_played"] == 17
    assert record["teams"] == ["KC", "SF"]
    assert record["primary_team_rule"] is not None
    assert record["weeks_observed"] == 17


def test_p6_b2_joined_identity_with_null_draft_fields_stays_null() -> None:
    module = _load_module()
    payload, _ = _build(module, players_rows=_players_rows(null_draft=True))
    for record in payload["records"]:
        assert record["identity_confidence"] == "source_verified"
        for field in ("draft_year", "draft_round", "draft_pick", "draft_team"):
            assert record[field] is None
            assert field in record["missing_fields"]
        assert record["birth_date"] == "1992-01-01"
        assert record["season_age"] is not None
    validator = module._load_validator_module()
    assert validator.validate_payload(payload) == []


def test_p7_payload_passes_schema_and_unchanged_validator() -> None:
    module = _load_module()
    payload, _ = _build(module)
    validator = module._load_validator_module()
    assert validator.validate_payload(payload) == []


def test_p8_g2_repeat_build_with_pinned_timestamp_is_byte_identical(tmp_path: Path) -> None:
    module = _load_module()
    first = _output_set(module, tmp_path / "run1")
    second = _output_set(module, tmp_path / "run2")
    assert [p.name for p in first] == [p.name for p in second]
    for (path_a, text_a), (path_b, text_b) in zip(first.items(), second.items()):
        assert path_a.name == path_b.name
        assert text_a == text_b
    module.publish_output_set(first)
    module.publish_output_set(second)
    for path_a, path_b in zip(first, second):
        assert path_a.read_bytes() == path_b.read_bytes()


# ---------------------------------------------------------------------------
# Fail-closed negative tests N-*
# ---------------------------------------------------------------------------


def test_n1_missing_week_aborts_naming_season_and_week() -> None:
    module = _load_module()
    week_rows = [r for r in _season_week_rows(2017) if r["week"] != 5]
    with pytest.raises(module.SourceFeasibilityError, match=r"Season 2017.*missing_weeks=\[5\]"):
        _build(module, frames=_frames(module, {2017: {"week": week_rows}}))


def test_n2_unexpected_week_18_aborts_historical_span() -> None:
    module = _load_module()
    week_rows = _season_week_rows(2015) + [_week_row(2015, 18, "00-1")]
    with pytest.raises(module.SourceFeasibilityError, match=r"Season 2015.*unexpected_weeks=\[18\]"):
        _build(module, frames=_frames(module, {2015: {"week": week_rows}}))


def test_n4_wrong_season_rows_abort_naming_counts_and_values() -> None:
    module = _load_module()
    week_rows = _season_week_rows(2016) + [_week_row(2015, 1, "00-1")]
    with pytest.raises(module.SourceFeasibilityError, match=r"Season 2016.*1 row\(s\).*differs from the requested"):
        _build(module, frames=_frames(module, {2016: {"week": week_rows}}))


def test_n5_mixed_season_reg_response_never_filtered_into_subset() -> None:
    module = _load_module()
    reg_rows = _season_reg_rows(2018) + [_reg_row(2017, "00-9", "WR")]
    with pytest.raises(module.SourceFeasibilityError, match="never filters drifted responses"):
        _build(module, frames=_frames(module, {2018: {"reg": reg_rows}}))


def test_n6_duplicate_grain_aborts() -> None:
    module = _load_module()
    reg_rows = _season_reg_rows(2015) + [_reg_row(2015, "00-1", "QB")]
    with pytest.raises(module.SourceFeasibilityError, match="Duplicate player-season-season_type grain"):
        _build(module, frames=_frames(module, {2015: {"reg": reg_rows}}))


def test_n7_legacy_identity_floor_binds_as_defense_in_depth() -> None:
    """Even if the accepted fingerprint itself carried a degraded join rate, the family
    floor 0.95 must still abort (it cannot be bypassed by the exact-agreement gate)."""
    module = _load_module()
    extras = [(f"00-1{i}", "WR") for i in range(6)]
    players = BASE_PLAYERS + extras  # 10 included players in 2015
    week_rows = _season_week_rows(2015, players=players)
    reg_rows = _season_reg_rows(2015, players=players)
    joined_only = _players_rows(players[:-1])  # 9 of 10 joined -> 0.90
    other_seasons_ok = _players_rows(players)
    frames = _frames(module, {2015: {"week": week_rows, "reg": reg_rows}})
    accepted = _accepted_fp(module, frames, _FakeFrame(joined_only))
    assert accepted[2015]["identity_join_rate_gsis_id"] == 0.9
    del other_seasons_ok  # base seasons only use the four base players, all joined
    with pytest.raises(module.SourceFeasibilityError, match="below.*family floor"):
        _build(module, frames=frames, players_rows=joined_only, accepted_fp=accepted)


def test_n9_contradictory_duplicate_identity_rows_abort_with_count_only() -> None:
    module = _load_module()
    players = _players_rows()
    players.append(dict(players[0], birth_date="1990-05-05"))
    with pytest.raises(module.SourceFeasibilityError, match="contradictory duplicate identity rows for 1 gsis_id"):
        _build(module, players_rows=players)


def test_n10_load_players_failure_aborts_build(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    module = _load_module()
    monkeypatch.setattr(module, "OUTPUT_BASE_DIR", tmp_path)
    monkeypatch.setattr(module, "_installed_nflreadpy_version", lambda: "0.1.5")
    monkeypatch.setattr(module, "_load_week_frame", lambda season: _FakeFrame(_season_week_rows(season)))
    monkeypatch.setattr(module, "_load_reg_frame", lambda season: _FakeFrame(_season_reg_rows(season)))

    def _fail_players():
        raise RuntimeError("players endpoint down")

    monkeypatch.setattr(module, "_load_players_frame", _fail_players)
    with pytest.raises(module.SourceFeasibilityError, match="load_players.*Identity is required"):
        module.main(["--generated-at", GEN_AT])
    assert _tree_files(tmp_path) == []


def test_n11_single_season_source_failure_fails_whole_build(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    module = _load_module()
    monkeypatch.setattr(module, "OUTPUT_BASE_DIR", tmp_path)
    monkeypatch.setattr(module, "_installed_nflreadpy_version", lambda: "0.1.5")

    def _week(season: int):
        if season == 2019:
            raise RuntimeError("nflverse 2019 outage")
        return _FakeFrame(_season_week_rows(season))

    monkeypatch.setattr(module, "_load_week_frame", _week)
    monkeypatch.setattr(module, "_load_reg_frame", lambda season: _FakeFrame(_season_reg_rows(season)))
    monkeypatch.setattr(module, "_load_players_frame", lambda: _FakeFrame(_players_rows()))
    with pytest.raises(module.SourceFeasibilityError, match="Season 2019 source call failed"):
        module.main(["--generated-at", GEN_AT])
    assert _tree_files(tmp_path) == []


def test_n12b_seventeen_games_single_team_is_unexplained_overage() -> None:
    module = _load_module()
    week_rows = _season_week_rows(2019) + [_week_row(2019, w, "00-8", team="KC") for w in range(1, 18)]
    reg_rows = _season_reg_rows(2019) + [_reg_row(2019, "00-8", "WR", games=17)]
    players = _players_rows(BASE_PLAYERS + [("00-8", "WR")])
    with pytest.raises(module.SourceFeasibilityError, match="ordinary single-team\ncap|ordinary single-team"):
        _build(
            module,
            frames=_frames(module, {2019: {"week": week_rows, "reg": reg_rows}}),
            players_rows=players,
        )


def test_n14_games_above_absolute_cap_aborts() -> None:
    module = _load_module()
    week_rows = (
        _season_week_rows(2019)
        + [_week_row(2019, w, "00-8", team="KC") for w in range(1, 9)]
        + [_week_row(2019, w, "00-8", team="SF") for w in range(9, 18)]
    )
    reg_rows = _season_reg_rows(2019) + [_reg_row(2019, "00-8", "WR", games=18)]
    players = _players_rows(BASE_PLAYERS + [("00-8", "WR")])
    with pytest.raises(module.SourceFeasibilityError, match="exceeds the absolute 2015-2020 cap"):
        _build(
            module,
            frames=_frames(module, {2019: {"week": week_rows, "reg": reg_rows}}),
            players_rows=players,
        )


def test_games_exceeding_weeks_observed_reconciliation_aborts() -> None:
    module = _load_module()
    week_rows = _season_week_rows(2016) + [_week_row(2016, w, "00-8") for w in range(1, 16)]
    reg_rows = _season_reg_rows(2016) + [_reg_row(2016, "00-8", "WR", games=16)]
    players = _players_rows(BASE_PLAYERS + [("00-8", "WR")])
    with pytest.raises(module.SourceFeasibilityError, match="exceeds weeks_observed"):
        _build(
            module,
            frames=_frames(module, {2016: {"week": week_rows, "reg": reg_rows}}),
            players_rows=players,
        )


def test_n16_phase1_failure_publishes_nothing_and_leaves_no_residue(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    module = _load_module()
    contents = _publish_contents(module, tmp_path, "v1")
    calls = {"n": 0}
    original = module._write_bytes

    def _failing_write(path: Path, data: bytes) -> None:
        calls["n"] += 1
        if calls["n"] == 3:
            raise OSError("disk full")
        original(path, data)

    monkeypatch.setattr(module, "_write_bytes", _failing_write)
    with pytest.raises(module.PublicationError, match="phase-1 staging failed"):
        module.publish_output_set(contents)
    assert _tree_files(tmp_path) == []


def test_n16b_first_run_rollback_leaves_every_final_absent(tmp_path: Path) -> None:
    module = _load_module()
    for failure_point in range(1, 6):
        base = tmp_path / f"point-{failure_point}"
        contents = _publish_contents(module, base, "v1")
        count = {"n": 0}

        def _fail_at(path: Path) -> None:
            count["n"] += 1
            if count["n"] == failure_point:
                raise RuntimeError(f"injected failure after install {failure_point}")

        with pytest.raises(module.PublicationError, match="rollback restored the exact pre-run state"):
            module.publish_output_set(contents, after_install=_fail_at)
        assert _tree_files(base) == [], f"failure point {failure_point} left files behind"


def test_n16c_rerun_rollback_restores_prior_bytes_exactly(tmp_path: Path) -> None:
    module = _load_module()
    for failure_point in range(1, 6):
        base = tmp_path / f"point-{failure_point}"
        prior = _publish_contents(module, base, "v1")
        module.publish_output_set(prior)
        prior_bytes = {path: path.read_bytes() for path in prior}

        replacement = _publish_contents(module, base, "v2")
        count = {"n": 0}

        def _fail_at(path: Path) -> None:
            count["n"] += 1
            if count["n"] == failure_point:
                raise RuntimeError("injected failure")

        with pytest.raises(module.PublicationError, match="rollback restored the exact pre-run state"):
            module.publish_output_set(replacement, after_install=_fail_at)
        for path, data in prior_bytes.items():
            assert path.read_bytes() == data, f"prior bytes lost at failure point {failure_point}"
        assert _tree_files(base) == sorted(prior_bytes.keys())


def test_n16d_rollback_failure_retains_backups_and_names_journal_state(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    module = _load_module()
    prior = _publish_contents(module, tmp_path, "v1")
    module.publish_output_set(prior)

    def _broken_restore(backup_path: Path, final_path: Path) -> None:
        raise OSError("filesystem refused rename")

    monkeypatch.setattr(module, "_restore_backup", _broken_restore)
    count = {"n": 0}

    def _fail_at(path: Path) -> None:
        count["n"] += 1
        if count["n"] == 2:
            raise RuntimeError("injected failure")

    replacement = _publish_contents(module, tmp_path, "v2")
    with pytest.raises(module.RollbackFailureError, match="Per-path journal state"):
        module.publish_output_set(replacement, after_install=_fail_at)
    backups = [p for p in _tree_files(tmp_path) if ".prev-" in p.name]
    assert backups, "recoverable backups must be retained on disk after a rollback failure"
    for backup in backups:
        assert backup.read_bytes().endswith(b"-v1\n")


def test_n16e_pre_existing_residue_aborts_before_staging_untouched(tmp_path: Path) -> None:
    module = _load_module()
    contents = _publish_contents(module, tmp_path, "v1")
    artifact_path = next(iter(contents))
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    residue = artifact_path.parent / f"{artifact_path.name}.tmp-999"
    residue.write_bytes(b"crash leftovers, possibly the only recoverable prior copy")
    with pytest.raises(module.ResidueError, match="residue preflight failed"):
        module.publish_output_set(contents)
    assert _tree_files(tmp_path) == [residue]
    assert residue.read_bytes() == b"crash leftovers, possibly the only recoverable prior copy"


def test_n17_exports_path_guard_fires_before_any_source_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_module()
    monkeypatch.setattr(module, "OUTPUT_BASE_DIR", module.REPO_ROOT / "exports")

    def _no_call(*args, **kwargs):
        raise AssertionError("no source call may happen once the exports path guard fires")

    monkeypatch.setattr(module, "_load_week_frame", _no_call)
    monkeypatch.setattr(module, "_load_reg_frame", _no_call)
    monkeypatch.setattr(module, "_load_players_frame", _no_call)
    monkeypatch.setattr(module, "_installed_nflreadpy_version", lambda: "0.1.5")
    with pytest.raises(module.SourceFeasibilityError, match="promoted path"):
        module.main(["--generated-at", GEN_AT])


def test_default_output_paths_are_not_under_exports() -> None:
    module = _load_module()
    module.assert_paths_not_under_exports(module.candidate_output_paths())


def test_n21_nflreadpy_version_gate_requires_exactly_0_1_5(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    module = _load_module()
    module.verify_nflreadpy_version("0.1.5")  # exact pin passes
    for wrong in ("0.1.6", "0.1.4", "0.2.0", None):
        with pytest.raises(module.SourceEvidenceDriftError, match="0.1.5"):
            module.verify_nflreadpy_version(wrong)

    monkeypatch.setattr(module, "OUTPUT_BASE_DIR", tmp_path)
    monkeypatch.setattr(module, "_installed_nflreadpy_version", lambda: "0.2.0")

    def _no_call(*args, **kwargs):
        raise AssertionError("no source call may happen on a dependency-pin mismatch")

    monkeypatch.setattr(module, "_load_week_frame", _no_call)
    monkeypatch.setattr(module, "_load_reg_frame", _no_call)
    monkeypatch.setattr(module, "_load_players_frame", _no_call)
    with pytest.raises(module.SourceEvidenceDriftError, match="source-evidence drift"):
        module.main(["--generated-at", GEN_AT])
    assert _tree_files(tmp_path) == []


def test_n22_fingerprint_count_mismatch_aborts_with_bounded_diagnostic() -> None:
    module = _load_module()
    frames = _frames(module)
    accepted = _accepted_fp(module, frames, _FakeFrame(_players_rows()))
    accepted[2017]["week_level_rows_reg"] += 1
    with pytest.raises(
        module.SourceEvidenceDriftError, match=r"season=2017 field=week_level_rows_reg"
    ) as excinfo:
        _build(module, frames=frames, accepted_fp=accepted)
    assert "00-1" not in str(excinfo.value)  # aggregates only, never player rows


def test_n23_max_games_fingerprint_mismatch_aborts() -> None:
    module = _load_module()
    frames = _frames(module)
    accepted = _accepted_fp(module, frames, _FakeFrame(_players_rows()))
    accepted[2018]["max_games_reg_level"] = 17
    with pytest.raises(module.SourceEvidenceDriftError, match=r"season=2018 field=max_games_reg_level"):
        _build(module, frames=frames, accepted_fp=accepted)


def test_n24_g8_identity_join_below_one_aborts_before_staging_no_provisional_row() -> None:
    module = _load_module()
    partial_players = _players_rows(BASE_PLAYERS[:-1])  # one included player unjoined
    with pytest.raises(module.SourceEvidenceDriftError, match="identity_join_rate_gsis_id"):
        _build(
            module,
            players_rows=partial_players,
            fp_players_rows=_players_rows(),  # accepted evidence: join rate exactly 1.0
        )


def test_n25_value_drift_inside_unchanged_aggregates_aborts() -> None:
    module = _load_module()
    clean_frames = _frames(module)
    _, clean_evidence = _build(module, frames=clean_frames)
    accepted_hashes = clean_evidence["source_content_hashes"]

    # REG-summary value drift: one stat value changes, every aggregate still matches.
    reg_rows = _season_reg_rows(2016)
    reg_rows[0] = dict(reg_rows[0], passing_yards=7)
    drifted = _frames(module, {2016: {"reg": reg_rows}})
    with pytest.raises(module.SourceEvidenceDriftError, match=r"reg_summary_by_season\[2016\]"):
        _build(module, frames=drifted, accepted_hashes=accepted_hashes)

    # Week-level value drift: one team-of-record changes, aggregates still match.
    week_rows = [dict(r) for r in _season_week_rows(2015)]
    week_rows[0] = dict(week_rows[0], team="SF")
    drifted_week = _frames(module, {2015: {"week": week_rows}})
    with pytest.raises(module.SourceEvidenceDriftError, match=r"week_level_by_season\[2015\]"):
        _build(module, frames=drifted_week, accepted_hashes=accepted_hashes)


# ---------------------------------------------------------------------------
# Boundary-acceptance tests B-1 .. B-4
# ---------------------------------------------------------------------------


def test_b1_post_rows_are_excluded_but_never_abort() -> None:
    module = _load_module()
    week_rows = _season_week_rows(2015) + [
        _week_row(2015, 18, "00-1", season_type="POST"),
        _week_row(2015, 19, "00-2", season_type="POST"),
    ]
    payload, evidence = _build(module, frames=_frames(module, {2015: {"week": week_rows}}))
    assert evidence["observed_fingerprints"][2015]["week_level_rows_total"] == 70
    assert evidence["observed_fingerprints"][2015]["week_level_rows_reg"] == 68
    for record in payload["records"]:
        if record["season"] == 2015:
            assert record["weeks_observed"] == 17  # POST weeks never contribute to REG evidence


def test_b4_ordinary_sixteen_games_single_team_accepted() -> None:
    module = _load_module()
    payload, _ = _build(module)
    for record in payload["records"]:
        assert record["games_played"] == 16
        assert record["coverage_status"] == "full_season"


# B-2 is covered by test_p6_b2_joined_identity_with_null_draft_fields_stays_null.
# B-3 is covered by test_p5_b3_multi_team_disjoint_weeks_17_games_accepted.


# ---------------------------------------------------------------------------
# Invariant / guard tests G-1 .. G-8
# ---------------------------------------------------------------------------


def test_g1_era_constants_guard_against_silent_2021_reuse() -> None:
    module = _load_module()
    assert module.FULL_SEASON_MIN_WEEKS_2015_2020 == 14
    assert module.EXPECTED_REG_WEEKS_2015_2020 == set(range(1, 18))
    assert module.ORDINARY_GAMES_CAP_2015_2020 == 16
    assert module.ABSOLUTE_GAMES_CAP_2015_2020 == 17
    assert module.REQUIRED_NFLREADPY_VERSION == "0.1.5"
    assert module._coverage_status(14) == "full_season"
    # Under the mechanically copied 2021+ constant (15), a 14-week row would flip
    # status -- proving silent 2021+ calibration reuse cannot pass this suite.
    assert 14 < 15
    assert module._coverage_status(13) == "partial_season"


def test_g1_accepted_fingerprint_constant_matches_committed_218_evidence() -> None:
    module = _load_module()
    evidence = json.loads(
        (REPO_ROOT / "docs/reports/player-season-coverage-v0-2015-2020-source-availability.json").read_text(
            encoding="utf-8"
        )
    )
    by_season = {entry["season"]: entry for entry in evidence["seasons"]}
    for season in module.SEASONS:
        accepted = module.ACCEPTED_SOURCE_FINGERPRINT_2015_2020[season]
        availability = by_season[season]["availability"]
        identity = by_season[season]["identity_age_draft"]
        assert accepted["week_level_rows_total"] == availability["week_level_rows_total"]
        assert accepted["week_level_rows_reg"] == availability["week_level_rows_reg"]
        assert accepted["reg_level_rows_total"] == availability["reg_level_rows_total"]
        assert accepted["reg_level_rows_reg_qb_rb_wr_te"] == availability["reg_level_rows_reg_qb_rb_wr_te"]
        assert accepted["row_counts_by_position_reg_level"] == availability["row_counts_by_position_reg_level"]
        assert accepted["player_counts_by_position"] == availability["player_counts_by_position"]
        assert accepted["unique_players_all_positions"] == availability["unique_players_all_positions"]
        assert accepted["reg_week_numbers_observed"] == availability["reg_week_numbers_observed"]
        assert accepted["wrong_season_week_row_count"] == availability["wrong_season_week_row_count"]
        assert accepted["wrong_season_reg_row_count"] == availability["wrong_season_reg_row_count"]
        assert accepted["duplicate_grain_pairs"] == availability["duplicate_grain_pairs"]
        assert accepted["max_games_reg_level"] == availability["max_games_reg_level"]
        assert accepted["identity_join_rate_gsis_id"] == identity["identity_join_rate_gsis_id"]


def _git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(b"blob %d\x00" % len(data) + data).hexdigest()


def test_g3_accepted_files_unchanged_by_this_implementation() -> None:
    pins = {
        "scripts/audit_player_season_coverage_2015_2020_source_availability.py": (
            "529f832b050dba494146f4b133c202072f587c0e"
        ),
        "scripts/build_player_season_coverage_2021_candidate.py": "6e438405c4bab0d9f66e7446f14516c53331d222",
        "scripts/build_player_season_coverage_2022_2025.py": "aac8d0a1083d53dff2edfdf3dd77051b91992641",
        "scripts/build_player_season_coverage_2021_2025_merged_candidate.py": (
            "7cc5b3cfe0cdbbaf118fb9ee7f13c499e00a9336"
        ),
        "scripts/validate_player_season_coverage_v0.py": "90bf7a51415cbf8a3e63eea50b0eb0ad4c11bf2c",
        "schemas/player_season_coverage_v0.schema.json": "ff1f413800b2c178ccd66d5440faa78de9ac2076",
        "docs/design/player-season-coverage-v0-2015-2020-candidate-build-spec.md": (
            "27aae171cb7b4138b272af32e42e06bb147900b2"
        ),
    }
    for relpath, expected in pins.items():
        assert _git_blob_sha(REPO_ROOT / relpath) == expected, f"accepted file changed: {relpath}"


def test_g4_no_support_claim_widening_in_any_output(tmp_path: Path) -> None:
    module = _load_module()
    contents = _output_set(module, tmp_path)
    for text in contents.values():
        for variant in ("2015-2025 is available", "2015–2025 is available"):
            assert variant not in text
    manifest = json.loads(contents[module.candidate_output_paths(tmp_path)["manifest"]])
    assert manifest["status"] == "candidate_evidence_artifact_not_promoted"

    # The guard itself must fire fail-closed if the phrase were ever introduced.
    payload, evidence = _build(module)
    payload["non_goals"] = list(payload["non_goals"]) + ["2015-2025 is available"]
    with pytest.raises(module.CandidateValidationError, match="support-claim guard"):
        module.build_output_set(payload, evidence, _TEST_ENVIRONMENT, base_dir=tmp_path / "guard")


def test_g5_manifest_is_never_a_promotion_manifest(tmp_path: Path) -> None:
    module = _load_module()
    contents = _output_set(module, tmp_path)
    manifest = json.loads(contents[module.candidate_output_paths(tmp_path)["manifest"]])
    promoted_schema = json.loads(
        (REPO_ROOT / "schemas/player_season_coverage_v0_promoted.schema.json").read_text(encoding="utf-8")
    )
    missing_promoted_fields = [field for field in promoted_schema["required"] if field not in manifest]
    assert "promoted_at" in missing_promoted_fields
    assert "promotion_review" in missing_promoted_fields
    assert manifest["status"] == "candidate_evidence_artifact_not_promoted"
    import jsonschema

    errors = list(jsonschema.Draft202012Validator(promoted_schema).iter_errors(manifest))
    assert errors, "the promoted schema must reject the candidate manifest"


def test_g6_successful_run_leaves_zero_residue(tmp_path: Path) -> None:
    module = _load_module()
    contents = _output_set(module, tmp_path)
    module.publish_output_set(contents)
    module.verify_published_set(tmp_path)
    residue = [p for p in _tree_files(tmp_path) if ".tmp-" in p.name or ".prev-" in p.name]
    assert residue == []
    assert len(_tree_files(tmp_path)) == 5


def test_g7_thirteen_deterministic_source_content_hashes_recorded(tmp_path: Path) -> None:
    module = _load_module()
    _, evidence_a = _build(module)
    _, evidence_b = _build(module)
    hashes_a = evidence_a["source_content_hashes"]
    assert len(hashes_a["week_level_by_season"]) == 6
    assert len(hashes_a["reg_summary_by_season"]) == 6
    assert isinstance(hashes_a["joined_identity_fields"], str)
    assert hashes_a == evidence_b["source_content_hashes"]
    contents = _output_set(module, tmp_path)
    manifest = json.loads(contents[module.candidate_output_paths(tmp_path)["manifest"]])
    assert manifest["source_content_hashes"] == hashes_a
    report = json.loads(contents[module.candidate_output_paths(tmp_path)["report_json"]])
    assert report["source_content_hashes"] == hashes_a


def test_g8_every_record_is_source_verified_never_provisional() -> None:
    module = _load_module()
    payload, _ = _build(module)
    assert all(record["identity_confidence"] == "source_verified" for record in payload["records"])
    assert not any(record["identity_confidence"] == "provisional" for record in payload["records"])


# ---------------------------------------------------------------------------
# Torn-state rejection and offline end-to-end
# ---------------------------------------------------------------------------


def test_torn_state_rejected_after_publication(tmp_path: Path) -> None:
    module = _load_module()
    contents = _output_set(module, tmp_path)
    module.publish_output_set(contents)
    paths = module.candidate_output_paths(tmp_path)

    artifact = paths["artifact"]
    original = artifact.read_bytes()
    artifact.write_bytes(original + b"tampered\n")
    with pytest.raises(module.TornStateError, match="artifact_sha256 does not match"):
        module.verify_published_set(tmp_path)
    artifact.write_bytes(original)
    module.verify_published_set(tmp_path)

    paths["report_md"].unlink()
    with pytest.raises(module.TornStateError, match="missing published output"):
        module.verify_published_set(tmp_path)


def test_main_offline_end_to_end_with_injected_fixtures(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    module = _load_module()
    frames = _frames(module)
    players_frame = _FakeFrame(_players_rows())
    accepted = _accepted_fp(module, frames, players_frame)

    monkeypatch.setattr(module, "OUTPUT_BASE_DIR", tmp_path)
    monkeypatch.setattr(module, "_installed_nflreadpy_version", lambda: "0.1.5")
    monkeypatch.setattr(module, "ACCEPTED_SOURCE_FINGERPRINT_2015_2020", accepted)
    monkeypatch.setattr(module, "_load_week_frame", lambda season: frames[season]["week"])
    monkeypatch.setattr(module, "_load_reg_frame", lambda season: frames[season]["reg"])
    monkeypatch.setattr(module, "_load_players_frame", lambda: players_frame)

    assert module.main(["--generated-at", GEN_AT]) == 0
    module.verify_published_set(tmp_path)
    paths = module.candidate_output_paths(tmp_path)
    artifact = json.loads(paths["artifact"].read_text(encoding="utf-8"))
    assert artifact["status"] == "candidate_evidence_artifact_not_promoted"
    assert len(artifact["records"]) == 24
    validation = json.loads(paths["validation"].read_text(encoding="utf-8"))
    assert validation["status"] == "pass"
    out = capsys.readouterr().out
    assert "Record count: 24" in out

"""Synthetic probes of unchanged producers, bound to inspection descriptor source pins.

These are not observations, source admissions, event qualification, or scoring tests.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import polars as pl
import pytest

import src.derive.gold as gold_module
from src.derive.gold import (
    build_player_role_inputs_weekly,
    build_player_role_profile_compatibility_weekly,
)

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = json.loads((ROOT / "data/semantics/projection_input_semantics.json").read_text())
DEFINITIONS = {d["id"]: d for d in REGISTRY["definition_inspection"]["definitions"]}


@pytest.fixture
def players():
    return pl.DataFrame(
        {
            "player_id": ["synthetic_a", "synthetic_b"],
            "full_name": ["Synthetic A", "Synthetic B"],
            "position": ["WR", "WR"],
            "team": ["DEMO", "DEMO"],
            "season": [2000, 2000],
            "week": [1, 1],
            "targets": [6.0, 16.0],
            "receptions": [4.0, 10.0],
            "receiving_yards": [40.0, 100.0],
            "receiving_tds": [0.0, 0.0],
            "red_zone_targets": [None, None],
            "air_yards": [40.0, 80.0],
            "routes_run": [21.0, 84.0],
            "snap_share": [None, None],
        }
    )


def team(targets=22.0):
    return pl.DataFrame(
        {"team": ["DEMO"], "season": [2000], "week": [1],
         "team_targets": [targets], "team_air_yards": [120.0]},
        schema_overrides={"team_targets": pl.Float64},
    )


def test_inspected_implementation_files_match_descriptor_hashes():
    for definition in DEFINITIONS.values():
        for binding in definition["source_bindings"]:
            actual = hashlib.sha256((ROOT / binding["path"]).read_bytes()).hexdigest()
            assert actual == binding["sha256"]


def test_route_share_formula_and_tprr_match_unchanged_gold(players):
    row = build_player_role_inputs_weekly(players, team()).to_dicts()[0]
    assert row["route_share"] == pytest.approx(21 / 105)
    assert row["tprr"] == pytest.approx(6 / 21)
    assert row["target_share"] == pytest.approx(6 / 22)
    route = DEFINITIONS["inspection.route_share.sum_player_routes.v0"]
    participation = DEFINITIONS["inspection.route_participation.team_dropbacks.proposed.v0"]
    assert route["numerator"] == "actual_player_routes_run"
    assert route["denominator"] == "sum_player_routes_in_input_team_week"
    assert route["formula"] == "player_routes / sum(input_player_routes for team, season, week)"
    target = DEFINITIONS["inspection.target_share.gold_team_targets.v0"]
    assert target["numerator"] == "player_targets"
    assert target["denominator"] == "sum_player_targets_in_silver_team_week"
    assert target["formula"] == "player_targets / team_targets when team_targets > 0; otherwise 0.0"
    tprr = DEFINITIONS["inspection.targets_per_route.actual_routes.v0"]
    assert tprr["numerator"] == "player_targets"
    assert tprr["denominator"] == "actual_player_routes_run"
    assert tprr["formula"] == (
        "player_targets / actual_player_routes_run when routes_run > 0; otherwise null"
    )
    assert participation["denominator"] == "eligible_team_dropbacks"
    # Arithmetic contrast only; no real dropback source or event ledger is introduced.
    assert 21 / 30 == pytest.approx(0.70)
    assert row["route_share"] != 21 / 30


def test_compatibility_alias_preserves_original_denominator(players, monkeypatch):
    gold = build_player_role_inputs_weekly(players, team())
    roster = players.select(["team", "season", "player_id"])
    # Isolate the mapping from unrelated historical vacated-target joins. That helper
    # uses legacy how='outer', which Polars 2 rejects; this is not pipeline signoff.
    monkeypatch.setattr(
        gold_module,
        "_build_team_vacated_target_share",
        lambda *_: pl.DataFrame(
            {"team": ["DEMO"], "season": [2000], "vacated_target_share": [None]},
            schema_overrides={"vacated_target_share": pl.Float64},
        ),
    )
    compatibility = build_player_role_profile_compatibility_weekly(gold, roster)
    assert compatibility["route_participation"].to_list() == gold["route_share"].to_list()
    alias = DEFINITIONS["inspection.route_participation.gold_compatibility_alias.v0"]
    assert alias["alias_of"] == "inspection.route_share.sum_player_routes.v0"
    assert alias["denominator"] == "sum_player_routes_in_input_team_week"


def test_partial_player_population_changes_share_without_role_change(players):
    complete = build_player_role_inputs_weekly(players, team()).to_dicts()[0]
    partial = build_player_role_inputs_weekly(players.head(1), team()).to_dicts()[0]
    assert complete["routes_run"] == partial["routes_run"] == 21
    assert complete["route_share"] == pytest.approx(0.2)
    assert partial["route_share"] == 1


@pytest.mark.parametrize("targets", [None, 0.0, -1.0])
def test_legacy_target_zero_fallback_is_preserved_and_disclosed(players, targets):
    rows = build_player_role_inputs_weekly(players, team(targets)).to_dicts()
    assert all(row["target_share"] == 0 for row in rows)
    descriptor = DEFINITIONS["inspection.target_share.gold_team_targets.v0"]
    assert "null, zero or negative" in descriptor["missing_behavior"]


def test_absent_route_column_does_not_become_zero(players):
    rows = build_player_role_inputs_weekly(players.drop("routes_run"), team()).to_dicts()
    for row in rows:
        assert all(row[field] is None for field in ("routes_run", "route_share", "tprr"))


@pytest.mark.parametrize("routes", [None, 0.0])
def test_unavailable_or_zero_denominator_produces_no_route_rate(players, routes):
    players = players.with_columns(pl.lit(routes).cast(pl.Float64).alias("routes_run"))
    rows = build_player_role_inputs_weekly(players, team()).to_dicts()
    assert all(row["route_share"] is None and row["tprr"] is None for row in rows)


def test_measured_zero_is_distinct_from_missing(players):
    players = players.with_columns(pl.lit(0.0).alias("targets"))
    row = build_player_role_inputs_weekly(players, team()).to_dicts()[0]
    assert row["tprr"] == 0
    players = players.with_columns(pl.lit(None).cast(pl.Float64).alias("targets"))
    row = build_player_role_inputs_weekly(players, team()).to_dicts()[0]
    assert row["tprr"] is None


def test_aggregation_requires_a_separate_policy(players):
    # Two independent synthetic games; this inspector deliberately selects no rolling rule.
    rates = []
    for targets, routes in [(1.0, 2.0), (9.0, 30.0)]:
        game = players.head(1).with_columns(
            pl.lit(targets).alias("targets"), pl.lit(routes).alias("routes_run")
        )
        rates.append(build_player_role_inputs_weekly(game, team()).to_dicts()[0]["tprr"])
    assert sum(rates) / 2 == pytest.approx(0.40)
    assert (1 + 9) / (2 + 30) == pytest.approx(0.3125)
    assert DEFINITIONS["inspection.targets_per_route.actual_routes.v0"]["aggregation"][
        "status"
    ] == "not_selected"

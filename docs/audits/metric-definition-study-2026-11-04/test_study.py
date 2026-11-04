"""Behavioral checks for the bounded study, not a production certification."""

import json
import math
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import study


class DefinitionStudyTests(unittest.TestCase):
    def test_route_alias_requires_a_denominator_choice(self):
        result = study.get_definition("route %")
        self.assertEqual(result["status"], "ambiguous")
        self.assertEqual(
            {c["family"] for c in result["matches"]}, {"route_share", "route_participation"}
        )
        self.assertNotIn("value", result)

    def test_target_share_requires_a_source_choice(self):
        result = study.get_definition("target_share")
        self.assertEqual(result["status"], "ambiguous")
        self.assertEqual(len(result["matches"]), 2)

    def test_unknown_metric_is_not_guessed(self):
        result = study.get_definition("elusiveness_score")
        self.assertEqual(result["status"], "not_indexed")
        self.assertEqual(result["matches"], [])

    def test_exact_variant_resolves_without_adding_a_value(self):
        result = study.get_definition("study.route_share.sum_player_routes.v0")
        self.assertEqual(result["status"], "definition_view")
        self.assertNotIn("value", result)
        self.assertFalse(result["consumer_authorized"])

    def test_tprr_alias_does_not_resolve_to_a_proxy(self):
        result = study.get_definition("TPRR")
        self.assertEqual(result["definition"]["denominator"], "actual_player_routes_run")

    def test_source_passthrough_does_not_inherit_gold_formula(self):
        card = study.get_definition("study.target_share.weekly_source_passthrough.v0")["definition"]
        self.assertIsNone(card["formula"])
        self.assertIsNone(card["denominator"])

    def test_gold_zero_behavior_remains_visible(self):
        card = study.get_definition("study.target_share.gold_team_targets.v0")["definition"]
        self.assertIn("0.0", card["missing_behavior"])
        self.assertIn("Policy concern", card["missing_behavior"])

    def test_same_routes_different_denominators_change_the_answer(self):
        rows = {e["label"]: e["value"] for e in study.demo()["examples"]}
        self.assertAlmostEqual(rows["route_share"], 0.20)
        self.assertAlmostEqual(rows["proposed_route_participation"], 0.70)
        self.assertAlmostEqual(rows["pass_attempt_denominator_counterexample"], 0.875)

    def test_proxy_and_tprr_remain_distinct(self):
        rows = {e["label"]: e["value"] for e in study.demo()["examples"]}
        self.assertAlmostEqual(rows["pass_play_participation_proxy"], 0.80)
        self.assertAlmostEqual(rows["targets_per_route"], 6 / 21)

    def test_demo_has_no_player_identity_or_evidence_authority(self):
        result = study.demo()
        self.assertIsNone(result["player_identity"])
        self.assertFalse(result["consumer_authorized"])
        self.assertTrue(all(e["evidence_kind"] == "synthetic_demo" for e in result["examples"]))

    def test_observed_zero_is_distinct_from_missing(self):
        self.assertEqual(study.synthetic_ratio(0, 10)["value"], 0)
        self.assertIsNone(study.synthetic_ratio(None, 10)["value"])
        self.assertIsNone(study.synthetic_ratio(6, None)["value"])

    def test_zero_denominator_does_not_produce_zero_or_infinity(self):
        result = study.synthetic_ratio(6, 0)
        self.assertEqual(result["status"], "undefined_denominator")
        self.assertIsNone(result["value"])

    def test_invalid_synthetic_counts_are_rejected(self):
        for invalid in (-1, True, "21", math.nan, math.inf):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                study.synthetic_ratio(invalid, 30)

    def test_aggregation_policies_are_not_interchangeable(self):
        result = study.demo()["aggregation_example"]
        self.assertAlmostEqual(result["ratio_of_sums"], 0.3125)
        self.assertAlmostEqual(result["mean_of_game_ratios"], 0.4)

    def test_route_share_and_route_participation_are_not_interchangeable(self):
        result = study.compare(
            "study.route_share.sum_player_routes.v0", "study.route_participation.team_dropbacks.v0"
        )
        self.assertFalse(result["interchangeable"])
        self.assertIn("denominator", result["differing_dimensions"])

    def test_comparison_requires_exact_identifiers(self):
        self.assertEqual(
            study.compare("route_share", "route_participation")["status"], "not_indexed"
        )

    def test_even_same_definition_does_not_certify_observation_comparability(self):
        key = "study.targets_per_route.actual_routes.v0"
        result = study.compare(key, key)
        self.assertTrue(result["interchangeable"])
        self.assertIn("not_assessed", result["observation_comparability"])

    def test_catalog_identifiers_are_unique_and_study_scoped(self):
        cards = study.definitions()
        self.assertEqual(len(cards), len({c["id"] for c in cards}))
        self.assertTrue(
            all(c["id"].startswith("study.") and c["runtime_binding"] is None for c in cards)
        )

    def test_sources_are_immutable_Data_references(self):
        for card in study.definitions():
            self.assertTrue(all(study.DATA_REF in url for url in card["sources"]))

    def test_current_artifact_census_and_fixture_boundary(self):
        report = study.audit()
        weekly, fixture, seasons = report["artifact_coverage"]
        self.assertEqual(weekly["rows"], 6326)
        self.assertEqual(weekly["non_null"]["target_share"], 6326)
        self.assertEqual(weekly["non_null"]["routes_run"], 0)
        self.assertEqual(weekly["non_null"]["route_participation"], 0)
        self.assertEqual(fixture["rows"], 6)
        self.assertEqual(fixture["non_null"]["routes_run"], 6)
        self.assertTrue(all(s.startswith("offline_fixture:") for s in fixture["source_labels"]))
        self.assertEqual(seasons["WR_rows"], 1191)
        self.assertEqual(seasons["WR_non_null"]["route_participation"], 0)

    def test_retained_generated_outputs_match_their_producer(self):
        here = Path(__file__).resolve().parent
        for name, output in (
            ("inspection.json", study.audit()),
            ("catalog.json", study.catalog()),
            ("examples.json", study.demo()),
        ):
            self.assertEqual(json.loads((here / name).read_text()), output)

    def test_cli_ambiguity_and_missing_ids_return_nonzero(self):
        for query in ("route %", "unknown_metric"):
            result = subprocess.run(
                [sys.executable, str(Path(study.__file__)), "get", query],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 2)
            self.assertFalse(json.loads(result.stdout)["consumer_authorized"])


if __name__ == "__main__":
    unittest.main()

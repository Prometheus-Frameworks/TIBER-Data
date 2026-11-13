"""Reproduce inspected gold-transform behavior with explicitly synthetic inputs."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import study

try:
    import polars as pl
except ImportError:
    pl = None


@unittest.skipIf(
    pl is None, "Install the repository Python dependencies for source-behavior probes"
)
class PinnedGoldBehaviorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for path in ("src/derive/gold.py", "src/utils/frames.py"):
            if (study.ROOT / path).read_bytes() != study.git_bytes(path):
                raise AssertionError(f"Source probe requires unchanged pinned file: {path}")
        sys.path.insert(0, str(study.ROOT))
        from src.derive.gold import build_player_role_inputs_weekly

        cls.transform = staticmethod(build_player_role_inputs_weekly)

    def players(self):
        return pl.DataFrame(
            {
                "player_id": ["synthetic_demo_a", "synthetic_demo_b"],
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

    def team(self, targets=22.0):
        return pl.DataFrame(
            {
                "team": ["DEMO"],
                "season": [2000],
                "week": [1],
                "team_targets": [targets],
                "team_air_yards": [120.0],
            },
            schema_overrides={"team_targets": pl.Float64},
        )

    def test_actual_route_share_uses_sum_of_input_player_routes(self):
        row = self.transform(self.players(), self.team()).to_dicts()[0]
        self.assertAlmostEqual(row["route_share"], 21 / 105)
        self.assertAlmostEqual(row["tprr"], 6 / 21)
        self.assertAlmostEqual(row["target_share"], 6 / 22)
        self.assertNotIn("route_participation", row)

    def test_actual_missing_or_nonpositive_team_denominator_returns_zero(self):
        for total in (None, 0.0, -1.0):
            with self.subTest(total=total):
                rows = self.transform(self.players(), self.team(total)).to_dicts()
                self.assertTrue(all(row["target_share"] == 0 for row in rows))

    def test_actual_absent_route_column_keeps_route_metrics_null(self):
        rows = self.transform(self.players().drop("routes_run"), self.team()).to_dicts()
        for row in rows:
            self.assertTrue(
                all(
                    row[k] is None
                    for k in ("routes_run", "route_share", "tprr", "yprr", "snap_share")
                )
            )

    def test_partial_input_population_changes_the_existing_denominator(self):
        rows = self.transform(self.players().head(1), self.team()).to_dicts()
        self.assertEqual(rows[0]["route_share"], 1.0)
        # This proves why input-population completeness is a separate gate.

    def test_actual_zero_routes_keeps_tprr_null(self):
        players = self.players().with_columns(pl.lit(0.0).alias("routes_run"))
        rows = self.transform(players, self.team()).to_dicts()
        self.assertTrue(all(row["tprr"] is None and row["route_share"] is None for row in rows))


if __name__ == "__main__":
    unittest.main()

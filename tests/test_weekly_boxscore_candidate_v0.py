"""Synthetic inputs only; no provider calls or real-player assertions."""
import copy
import csv
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import unittest

SPEC = importlib.util.spec_from_file_location(
    "weekly_box", Path(__file__).resolve().parents[1] / "scripts/build_weekly_boxscore_candidate_v0.py")
box = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(box)


def encode(rows, missing=()):
    headers = [k for k in rows[0] if k not in missing]
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=headers, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode()


def fixtures():
    players, teams = [], []
    for ordinal, (team, opponent) in enumerate((("AAA", "BBB"), ("BBB", "AAA")), 1):
        row = {"season": "2026", "week": "1", "season_type": "REG",
            "game_id": "SYNTHETIC_GAME", "team": team, "opponent_team": opponent,
            **{field: "0" for field in box.FIELDS}}
        row.update(targets="4", receptions="2", receiving_yards="30", carries="3")
        teams.append(dict(row))
        players.append({**row, "player_id": f"00-999000{ordinal}",
            "player_display_name": f"Synthetic player {ordinal}", "position": "WR"})
    return players, teams


def receipt(player, team):
    return {"status": "unadmitted_candidate_source_snapshot",
        "requested_scope": {"season": 2026, "season_type": "REG", "week": 1},
        "snapshot_compiled_at": "2026-09-14T00:00:00Z",
        "test_fixture": True,
        "sources": {kind: {"byte_count": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
            for kind, raw in (("player", player), ("team", team))}}


class WeeklyBoxCandidateTests(unittest.TestCase):
    def build(self, players=None, teams=None, missing=()):
        default_p, default_t = fixtures()
        pr = encode(default_p if players is None else players, missing)
        tr = encode(default_t if teams is None else teams)
        return box.build_candidate(pr, tr, receipt(pr, tr))

    def test_exact_observations_and_explicit_denominators(self):
        artifact = self.build()
        self.assertFalse(artifact["consumer_admitted"])
        row = artifact["players"][0]
        self.assertEqual(row["derived"]["carries_plus_targets"], 7)
        self.assertEqual(row["derived"]["target_share_credited_team_targets"]["value"], 1)
        self.assertEqual(artifact["coverage"]["full_week_completeness"], "unverified")
        self.assertEqual(artifact["validation"]["metric_conflicts"], [])

    def test_repeat_is_deterministic(self):
        self.assertEqual(json.dumps(self.build(), sort_keys=True), json.dumps(self.build(), sort_keys=True))

    def test_byte_tampering_fails(self):
        p, t = map(encode, fixtures())
        with self.assertRaisesRegex(ValueError, "source bytes"):
            box.build_candidate(p + b"\n", t, receipt(p, t))

    def test_fixture_receipt_cannot_enter_cli_source_lane(self):
        p, t = map(encode, fixtures())
        r = receipt(p, t)
        r["status"] = "offline_fixture"
        with self.assertRaisesRegex(ValueError, "receipt status"):
            box.build_candidate(p, t, r)

    def test_missing_column_stays_unknown(self):
        artifact = self.build(missing=("targets",))
        row = artifact["players"][0]
        self.assertIsNone(row["observed"]["targets"])
        self.assertIsNone(row["derived"]["carries_plus_targets"])
        self.assertIsNone(row["derived"]["target_share_credited_team_targets"]["value"])
        self.assertIn("targets", artifact["validation"]["missing_columns"]["player"])

    def test_null_row_prevents_false_complete_subtotal(self):
        p, t = fixtures()
        p[0]["targets"] = ""
        artifact = self.build(p, t)
        self.assertEqual(artifact["teams"][0]["reconciliation"]["targets"]["status"], "unknown")

    def test_disagreement_preserves_counts_and_withholds_share(self):
        p, t = fixtures()
        t[0]["targets"] = "5"
        row = self.build(p, t)["players"][0]
        self.assertEqual(row["observed"]["targets"], 4)
        share = row["derived"]["target_share_credited_team_targets"]
        self.assertEqual(share["denominator"], 5)
        self.assertIsNone(share["value"])
        self.assertEqual(share["reason"], "conflict")

    def test_zero_denominator_is_not_zero_share(self):
        p, t = fixtures()
        p[0]["targets"] = t[0]["targets"] = "0"
        share = self.build(p, t)["players"][0]["derived"]["target_share_credited_team_targets"]
        self.assertIsNone(share["value"])

    def test_duplicate_player_key_is_rejected(self):
        p, t = fixtures()
        p.append(copy.deepcopy(p[0]))
        with self.assertRaisesRegex(ValueError, "Duplicate source key"):
            self.build(p, t)

    def test_duplicate_team_key_is_rejected(self):
        p, t = fixtures()
        t.append(copy.deepcopy(t[0]))
        with self.assertRaisesRegex(ValueError, "Duplicate source key"):
            self.build(p, t)

    def test_mismatched_game_team_join_is_rejected(self):
        p, t = fixtures()
        p[0]["opponent_team"] = "CCC"
        with self.assertRaisesRegex(ValueError, "identity disagreement"):
            self.build(p, t)

    def test_missing_opponent_pair_is_rejected(self):
        p, t = fixtures()
        with self.assertRaisesRegex(ValueError, "opponent pair"):
            self.build(p[:1], t[:1])

    def test_missing_id_cannot_be_replaced_by_name(self):
        p, t = fixtures()
        p[0]["player_id"] = ""
        artifact = self.build(p, t)
        self.assertEqual(artifact["coverage"]["player_rows"], 1)
        self.assertEqual(artifact["coverage"]["unattributed_player_rows"], 1)
        unknown = artifact["unattributed_source_observations"][0]
        self.assertEqual(unknown["raw_player_id"], "")
        self.assertNotIn("player_id", unknown["identity"])
        self.assertEqual(artifact["teams"][0]["reconciliation"]["targets"]["status"], "matched")

    def test_out_of_scope_rows_do_not_expand_week(self):
        p, t = fixtures()
        extra = copy.deepcopy(p[0])
        extra["week"] = "2"
        p.append(extra)
        artifact = self.build(p, t)
        self.assertEqual(artifact["coverage"]["player_rows"], 2)
        self.assertEqual(artifact["coverage"]["excluded_out_of_scope_rows"]["player"], 1)

    def test_empty_requested_scope_fails(self):
        p, t = fixtures()
        for row in p:
            row["week"] = "2"
        with self.assertRaisesRegex(ValueError, "no source rows"):
            self.build(p, t)

    def test_invalid_numbers_never_become_zero(self):
        for value in ("false", "1.5", "inf", "-1", "1000001"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                box.integer(value, "targets")
        self.assertEqual(box.integer("-7", "rushing_yards"), -7)
        self.assertIsNone(box.integer("NA", "targets"))

    def test_all_source_positions_retained(self):
        p, t = fixtures()
        p[0]["position"] = "DB"
        self.assertEqual(self.build(p, t)["coverage"]["player_rows"], 2)

    def test_no_scoring_or_route_inference(self):
        row = self.build()["players"][0]
        self.assertNotIn("fantasy_points", row["derived"])
        self.assertNotIn("routes", row["derived"])


if __name__ == "__main__":
    unittest.main()

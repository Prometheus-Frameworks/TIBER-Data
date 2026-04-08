from __future__ import annotations

import ast
import json
from pathlib import Path


def _fixture_data() -> dict[str, list[dict]]:
    source = Path("src/ingest/public.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.target.id == "FIXTURE_DATA" and node.value is not None:
                return ast.literal_eval(node.value)
    raise AssertionError("FIXTURE_DATA definition not found in src/ingest/public.py")


def _raw_records(path: str) -> list[dict]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return payload["records"]


def test_w2_to_w6_offline_support_is_not_claimed_reproducible_from_fixture_data() -> None:
    fixture_data = _fixture_data()

    fixture_player_weeks = {
        int(record["week"])
        for record in fixture_data["weekly_player_stats"]
        if int(record["season"]) == 2024
    }
    fixture_team_weeks = {
        int(record["week"])
        for record in fixture_data["team_week_context"]
        if int(record["season"]) == 2024
    }

    raw_player_weeks = {
        int(record["week"])
        for record in _raw_records("data/raw/forge/weekly_player_stats.offline_fixture.json")
        if int(record["season"]) == 2024
    }
    raw_team_weeks = {
        int(record["week"])
        for record in _raw_records("data/raw/forge/team_week_context.offline_fixture.json")
        if int(record["season"]) == 2024
    }

    assert fixture_player_weeks == {1}
    assert fixture_team_weeks == {1}
    assert raw_player_weeks == {1, 2, 3, 4, 5, 6}
    assert raw_team_weeks == {1, 2, 3, 4, 5, 6}

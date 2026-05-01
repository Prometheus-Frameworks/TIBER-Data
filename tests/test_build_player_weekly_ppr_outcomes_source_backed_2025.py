from importlib.util import module_from_spec, spec_from_file_location
import json
import math
from pathlib import Path


def _load_module():
    module_path = Path(__file__).resolve().parents[1] / "scripts" / "build_player_weekly_ppr_outcomes_source_backed_2025.py"
    spec = spec_from_file_location("build_player_weekly_ppr_outcomes_source_backed_2025", module_path)
    assert spec is not None and spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _PolarsLikeFrame:
    def __init__(self) -> None:
        self.to_dicts_called = False

    def to_dicts(self) -> list[dict]:
        self.to_dicts_called = True
        return [{"season": 2025, "week": 1, "player_id": "00-1"}]


class _PandasLikeFrame:
    def __init__(self) -> None:
        self.to_dict_args = None

    def to_dict(self, orient: str) -> list[dict]:
        self.to_dict_args = orient
        return [{"season": 2025, "week": 1, "player_id": "00-2"}]


def test_records_from_dataframe_prefers_polars_to_dicts() -> None:
    module = _load_module()
    frame = _PolarsLikeFrame()

    records = module._records_from_dataframe(frame)

    assert frame.to_dicts_called is True
    assert records == [{"season": 2025, "week": 1, "player_id": "00-1"}]


def test_records_from_dataframe_falls_back_to_pandas_records_orient() -> None:
    module = _load_module()
    frame = _PandasLikeFrame()

    records = module._records_from_dataframe(frame)

    assert frame.to_dict_args == "records"
    assert records == [{"season": 2025, "week": 1, "player_id": "00-2"}]


class _FakeFrame:
    def __init__(self, rows: list[dict]) -> None:
        self.columns = list(rows[0].keys()) if rows else []
        self._rows = rows

    def to_dict(self, orient: str) -> list[dict]:
        assert orient == "records"
        return self._rows


def test_json_safe_value_normalizes_nan_non_finite() -> None:
    module = _load_module()
    assert module._json_safe_value(math.nan) is None
    assert module._json_safe_value(float("inf")) is None
    assert module._json_safe_value(float("-inf")) is None
    assert module._json_safe_value(3.5) == 3.5


def test_build_payload_sanitizes_nan_and_serializes_with_allow_nan_false(tmp_path, monkeypatch) -> None:
    module = _load_module()
    roster_path = tmp_path / "roster.json"
    roster_path.write_text(
        json.dumps(
            {
                "provenance": "test",
                "source_path": "test",
                "records": [
                    {"season": 2025, "week": 1, "player_id": "00-1", "position": "WR"},
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(module, "ROSTER_SOURCE_PATH", roster_path)
    monkeypatch.setattr(
        module.nfl,
        "load_player_stats",
        lambda _: _FakeFrame(
            [
                {
                    "season": 2025,
                    "week": 1,
                    "player_id": "00-1",
                    "player_name": "Player One",
                    "recent_team": "PHI",
                    "position": "WR",
                    "receptions": math.nan,
                }
            ]
        ),
    )
    payload = module.build_source_backed_payload()
    assert payload["records"][0]["receptions"] is None
    json.dumps(payload, indent=2, allow_nan=False)


def test_build_payload_uses_roster_position_fallback_per_row(tmp_path, monkeypatch) -> None:
    module = _load_module()
    roster_path = tmp_path / "roster.json"
    roster_path.write_text(
        json.dumps(
            {
                "provenance": "test",
                "source_path": "test",
                "records": [
                    {"season": 2025, "week": 1, "player_id": "00-1", "position": "WR"},
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(module, "ROSTER_SOURCE_PATH", roster_path)
    monkeypatch.setattr(
        module.nfl,
        "load_player_stats",
        lambda _: _FakeFrame(
            [
                {
                    "season": 2025,
                    "week": 1,
                    "player_id": "00-1",
                    "player_name": "Player One",
                    "recent_team": "PHI",
                    "position": None,
                },
                {
                    "season": 2025,
                    "week": 1,
                    "player_id": "00-2",
                    "player_name": "Player Two",
                    "recent_team": "PHI",
                    "position": "",
                },
            ]
        ),
    )
    payload = module.build_source_backed_payload()
    ids = [row["player_id"] for row in payload["records"]]
    assert "00-1" in ids
    assert "00-2" not in ids

from importlib.util import module_from_spec, spec_from_file_location
import json
import math
from pathlib import Path


def _load_module():
    module_path = Path(__file__).resolve().parents[1] / "scripts" / "build_player_weekly_usage_source_backed_2025.py"
    spec = spec_from_file_location("build_player_weekly_usage_source_backed_2025", module_path)
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


def test_json_safe_value_normalizes_nan_non_finite() -> None:
    module = _load_module()
    assert module._json_safe_value(math.nan) is None
    assert module._json_safe_value(float("inf")) is None
    assert module._json_safe_value(float("-inf")) is None


class _FakeFrame:
    def __init__(self, rows: list[dict]) -> None:
        self.columns = list(rows[0].keys())
        self._rows = rows

    def to_dict(self, orient: str) -> list[dict]:
        assert orient == "records"
        return self._rows


def test_build_payload_drops_missing_and_sets_unsupported_none(monkeypatch) -> None:
    module = _load_module()
    monkeypatch.setattr(
        module.nfl,
        "load_player_stats",
        lambda _: _FakeFrame(
            [
                {"season": 2025, "week": 1, "player_id": "00-1", "player_name": "A", "team": "PHI", "position": "WR"},
                {"season": 2025, "week": 1, "player_id": None, "player_name": "B", "team": "PHI", "position": "WR"},
                {"season": 2025, "week": 1, "player_id": "00-2", "player_name": "C", "team": None, "position": "WR"},
            ]
        ),
    )
    payload = module.build_source_backed_payload()
    assert len(payload["records"]) == 1
    row = payload["records"][0]
    assert row["routes_run"] is None
    assert row["snap_share"] is None


def test_duplicate_season_week_player_id_fails_closed(monkeypatch) -> None:
    module = _load_module()
    monkeypatch.setattr(
        module.nfl,
        "load_player_stats",
        lambda _: _FakeFrame(
            [
                {"season": 2025, "week": 1, "player_id": "00-1", "player_name": "A", "team": "PHI", "position": "WR"},
                {"season": 2025, "week": 1, "player_id": "00-1", "player_name": "A", "team": "PHI", "position": "WR"},
            ]
        ),
    )
    try:
        module.build_source_backed_payload()
        assert False, "expected duplicate failure"
    except ValueError as exc:
        assert "Duplicate player weekly usage row" in str(exc)


def test_payload_serializes_allow_nan_false(monkeypatch) -> None:
    module = _load_module()
    monkeypatch.setattr(
        module.nfl,
        "load_player_stats",
        lambda _: _FakeFrame(
            [
                {
                    "season": 2025,
                    "week": 1,
                    "player_id": "00-1",
                    "player_name": "A",
                    "team": "PHI",
                    "position": "WR",
                    "target_share": math.nan,
                }
            ]
        ),
    )
    payload = module.build_source_backed_payload()
    json.dumps(payload, allow_nan=False)

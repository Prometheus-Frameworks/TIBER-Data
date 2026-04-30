from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


def _load_module():
    module_path = Path(__file__).resolve().parents[1] / "scripts" / "build_roster_player_team_map_source_backed_2025.py"
    spec = spec_from_file_location("build_roster_player_team_map_source_backed_2025", module_path)
    assert spec is not None and spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _PolarsLikeFrame:
    def __init__(self) -> None:
        self.to_dicts_called = False

    def to_dicts(self) -> list[dict]:
        self.to_dicts_called = True
        return [{"season": 2025, "week": 1, "gsis_id": "00-0000001"}]


class _PandasLikeFrame:
    def __init__(self) -> None:
        self.to_dict_args = None

    def to_dict(self, orient: str) -> list[dict]:
        self.to_dict_args = orient
        return [{"season": 2025, "week": 1, "gsis_id": "00-0000002"}]


def test_records_from_dataframe_prefers_polars_to_dicts() -> None:
    module = _load_module()
    frame = _PolarsLikeFrame()

    records = module._records_from_dataframe(frame)

    assert frame.to_dicts_called is True
    assert records == [{"season": 2025, "week": 1, "gsis_id": "00-0000001"}]


def test_records_from_dataframe_falls_back_to_pandas_records_orient() -> None:
    module = _load_module()
    frame = _PandasLikeFrame()

    records = module._records_from_dataframe(frame)

    assert frame.to_dict_args == "records"
    assert records == [{"season": 2025, "week": 1, "gsis_id": "00-0000002"}]

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config.settings import PipelineConfig
from src.ingest.public import PublicDataClient


def test_load_via_nflreadpy_ignores_unsupported_kwargs(monkeypatch) -> None:
    client = PublicDataClient(PipelineConfig(seasons=[2024], allow_offline_fallback=False))

    class FakeModule:
        @staticmethod
        def load_player_stats(seasons, summary_level):
            assert seasons == [2024]
            assert summary_level == "week"
            return [{"player_id": "p1", "season": 2024, "week": 1}]

    def _fake_import(_name: str):
        return FakeModule

    monkeypatch.setattr("src.ingest.public.importlib.import_module", _fake_import)

    rows = client._load_via_nflreadpy(
        method_name="load_player_stats",
        seasons=[2024],
        summary_level="week",
        file_type="parquet",
    )

    assert rows is not None
    assert len(rows) == 1
    assert rows[0]["player_id"] == "p1"

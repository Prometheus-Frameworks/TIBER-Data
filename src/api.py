from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from src.config.settings import build_config
from src.utils.frames import require_polars

app = FastAPI(title="TIBER-Data API", version="0.1.0")

DATASETS = {
    "teams": build_config().silver_dir / "teams.parquet",
    "players": build_config().silver_dir / "players.parquet",
    "team_context": build_config().gold_dir / "team_context_weekly.parquet",
    "player_role_inputs": build_config().gold_dir / "player_role_inputs_weekly.parquet",
}


def _missing_dataset_response(dataset: str, path: Path) -> HTTPException:
    return HTTPException(
        status_code=503,
        detail={
            "error": "parquet_output_missing",
            "dataset": dataset,
            "path": str(path),
            "message": f"Missing parquet output for '{dataset}'. Run the pipeline first.",
        },
    )


def _load_dataset(dataset: str) -> Any:
    path = DATASETS[dataset]
    if not path.exists():
        raise _missing_dataset_response(dataset, path)
    pl = require_polars()
    return pl.read_parquet(path)


def _records_response(dataset: str, records: list[dict[str, Any]]) -> JSONResponse:
    return JSONResponse(content={"dataset": dataset, "count": len(records), "data": records})


@app.get("/health")
def health() -> JSONResponse:
    missing = [
        {"dataset": dataset, "path": str(path)}
        for dataset, path in DATASETS.items()
        if not path.exists()
    ]
    if missing:
        return JSONResponse(
            status_code=503,
            content={
                "status": "error",
                "message": "One or more parquet outputs are missing. Run the pipeline first.",
                "missing": missing,
            },
        )
    return JSONResponse(
        content={
            "status": "ok",
            "datasets": {dataset: str(path) for dataset, path in DATASETS.items()},
        }
    )


@app.get("/api/teams")
def get_teams() -> JSONResponse:
    frame = _load_dataset("teams")
    return _records_response("teams", frame.to_dicts())


@app.get("/api/players")
def get_players() -> JSONResponse:
    frame = _load_dataset("players")
    return _records_response("players", frame.to_dicts())


@app.get("/api/team-context")
def get_team_context() -> JSONResponse:
    frame = _load_dataset("team_context")
    return _records_response("team_context", frame.to_dicts())


@app.get("/api/team-context/{team}")
def get_team_context_for_team(team: str) -> JSONResponse:
    pl = require_polars()
    frame = _load_dataset("team_context")
    filtered = frame.filter(pl.col("team").str.to_uppercase() == team.upper())
    if filtered.height == 0:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "team_not_found",
                "team": team,
                "message": f"No team context rows found for team '{team}'.",
            },
        )
    return _records_response("team_context", filtered.to_dicts())


@app.get("/api/player-role-inputs")
def get_player_role_inputs() -> JSONResponse:
    frame = _load_dataset("player_role_inputs")
    return _records_response("player_role_inputs", frame.to_dicts())


@app.get("/api/player-role-inputs/{player_id}")
def get_player_role_inputs_for_player(player_id: str) -> JSONResponse:
    pl = require_polars()
    frame = _load_dataset("player_role_inputs")
    filtered = frame.filter(pl.col("player_id") == player_id)
    if filtered.height == 0:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "player_not_found",
                "player_id": player_id,
                "message": f"No player role input rows found for player_id '{player_id}'.",
            },
        )
    return _records_response("player_role_inputs", filtered.to_dicts())

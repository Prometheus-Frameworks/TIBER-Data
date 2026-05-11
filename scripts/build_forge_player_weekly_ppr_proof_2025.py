from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

SEASON = 2025
PLAYER_ID = "00-0036900"
PLAYER_NAME = "Ja'Marr Chase"
SCORING_FORMAT = "PPR"
SCHEMA_VERSION = "proof.v1"
DEFAULT_AS_OF = "2026-04-27T00:00:00Z"
BUILD_ID = "forge-player-weekly-ppr-proof-2025:jamarr-chase:source-backed"

SOURCE_PATH = Path("data/processed/evidence/player_weekly_ppr_outcomes_2025.source_backed.json")
ROSTER_SOURCE_PATH = Path("data/processed/evidence/roster_player_team_map_2025.source_backed.json")
OUTPUT_PATH = Path(
    "data/gold/forge/proofs/forge_player_weekly_ppr_2025_jamarr_chase.proof.json"
)

SCORING_RULES = {
    "passingYards": "yards / 25 when applicable",
    "passingTds": "td * 4 when applicable",
    "interceptions": "interception * -2 when applicable",
    "rushingYards": "yards / 10",
    "rushingTds": "td * 6",
    "receivingYards": "yards / 10",
    "receivingTds": "td * 6",
    "receptions": "reception * 1",
    "fumblesLost": "fumble lost * -2 when available",
}

FORMULA = (
    "receptions + (receivingYards / 10) + (receivingTDs * 6) "
    "+ (rushingYards / 10) + (rushingTDs * 6) "
    "+ applicable passing scoring - (interceptions * 2) - (fumblesLost * 2)"
)


def _json_safe_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, float) and (math.isnan(value) or not math.isfinite(value)):
        return None
    return value


def _number_or_zero(value: Any) -> float:
    value = _json_safe_value(value)
    if value is None:
        return 0.0
    return float(value)


def _optional_int(value: Any) -> int | None:
    value = _json_safe_value(value)
    if value is None:
        return None
    return int(value)


def _optional_number(value: Any) -> float | int | None:
    value = _json_safe_value(value)
    if value is None:
        return None
    number = float(value)
    return int(number) if number.is_integer() else number


def _round(value: float, digits: int = 2) -> float:
    return round(value + 0, digits)


def calculate_ppr_points(row: dict[str, Any]) -> float:
    points = (
        _number_or_zero(row.get("passing_yards")) / 25
        + _number_or_zero(row.get("passing_tds")) * 4
        + _number_or_zero(row.get("interceptions")) * -2
        + _number_or_zero(row.get("rushing_yards")) / 10
        + _number_or_zero(row.get("rushing_tds")) * 6
        + _number_or_zero(row.get("receiving_yards")) / 10
        + _number_or_zero(row.get("receiving_tds")) * 6
        + _number_or_zero(row.get("receptions"))
        + _number_or_zero(row.get("fumbles_lost")) * -2
    )
    return _round(points, 2)


def _load_payload(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ValueError(
            "Missing source-backed 2025 player-week PPR input. "
            f"Expected {path}. This proof must fail closed rather than use fixtures, samples, "
            "or invented rows."
        )
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload.get("records"), list):
        raise ValueError(f"Source-backed payload at {path} must contain a records array.")
    return payload


def _canonical_player_name(roster_source_path: Path, player_id: str) -> str:
    if not roster_source_path.exists():
        return PLAYER_NAME
    payload = json.loads(roster_source_path.read_text(encoding="utf-8"))
    names = [
        str(row.get("player_name", "")).strip()
        for row in payload.get("records", [])
        if str(row.get("player_id", "")).strip() == player_id
        and str(row.get("player_name", "")).strip()
    ]
    return sorted(set(names))[0] if names else PLAYER_NAME


def _source_rows(payload: dict[str, Any], player_id: str) -> list[dict[str, Any]]:
    rows = [
        dict(row)
        for row in payload["records"]
        if int(row.get("season")) == SEASON
        and str(row.get("player_id", "")).strip() == player_id
    ]
    if not rows:
        raise ValueError(
            f"No source-backed {SEASON} rows are available for {player_id} ({PLAYER_NAME}). "
            "This proof cannot be generated from fixtures, samples, or representative rows."
        )

    seen: set[tuple[int, str]] = set()
    for row in rows:
        key = (int(row.get("week")), str(row.get("opponent", "")))
        if key in seen:
            raise ValueError(f"Duplicate source-backed player-week/game row detected: {key}")
        seen.add(key)
    return sorted(rows, key=lambda row: (int(row["week"]), str(row.get("opponent", ""))))


def _proof_row(
    row: dict[str, Any],
    player_name: str,
    source_payload: dict[str, Any],
    source_path: Path,
) -> dict[str, Any]:
    proof: dict[str, Any] = {
        "playerId": str(row.get("player_id", PLAYER_ID)).strip(),
        "playerName": player_name,
        "team": str(row.get("team", "")).strip(),
        "position": str(row.get("position", "")).strip().upper(),
        "season": int(row["season"]),
        "week": int(row["week"]),
        "opponent": _json_safe_value(row.get("opponent")),
        "gameId": _json_safe_value(row.get("game_id")),
        "receptions": _optional_int(row.get("receptions")),
        "receivingYards": _optional_number(row.get("receiving_yards")),
        "receivingTDs": _optional_int(row.get("receiving_tds")),
        "rushingAttempts": _optional_int(row.get("rushing_attempts")),
        "rushingYards": _optional_number(row.get("rushing_yards")),
        "rushingTDs": _optional_int(row.get("rushing_tds")),
        "fumblesLost": _optional_int(row.get("fumbles_lost")) if "fumbles_lost" in row else None,
        "pprPoints": calculate_ppr_points(row),
        "sourceProvider": "nflverse via nflreadpy",
        "sourceFile": str(source_path),
        "sourcePath": source_payload.get("source_path"),
        "sourceProvenance": source_payload.get("provenance"),
        "asOf": DEFAULT_AS_OF,
        "sourceUpdatedAt": DEFAULT_AS_OF,
        "buildId": BUILD_ID,
    }

    passing_values = {
        "passingYards": row.get("passing_yards"),
        "passingTDs": row.get("passing_tds"),
        "interceptions": row.get("interceptions"),
    }
    if any(_number_or_zero(value) != 0 for value in passing_values.values()):
        proof.update(
            {
                "passingYards": _optional_number(row.get("passing_yards")),
                "passingTDs": _optional_int(row.get("passing_tds")),
                "interceptions": _optional_int(row.get("interceptions")),
            }
        )
    return proof


def _season_totals(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "games": len(rows),
        "weeks": [int(row["week"]) for row in rows],
        "pprPoints": _round(sum(calculate_ppr_points(row) for row in rows), 2),
        "receptions": sum(_optional_int(row.get("receptions")) or 0 for row in rows),
        "receivingYards": sum(_optional_number(row.get("receiving_yards")) or 0 for row in rows),
        "receivingTDs": sum(_optional_int(row.get("receiving_tds")) or 0 for row in rows),
        "rushingAttempts": sum(_optional_int(row.get("rushing_attempts")) or 0 for row in rows),
        "rushingYards": sum(_optional_number(row.get("rushing_yards")) or 0 for row in rows),
        "rushingTDs": sum(_optional_int(row.get("rushing_tds")) or 0 for row in rows),
        "fumblesLost": None
        if all(
            "fumbles_lost" not in row
            or _json_safe_value(row.get("fumbles_lost")) is None
            for row in rows
        )
        else sum(_optional_int(row.get("fumbles_lost")) or 0 for row in rows),
    }


def build_proof(
    source_path: Path = SOURCE_PATH,
    roster_source_path: Path = ROSTER_SOURCE_PATH,
    player_id: str = PLAYER_ID,
) -> dict[str, Any]:
    source_payload = _load_payload(source_path)
    rows = _source_rows(source_payload, player_id)
    player_name = _canonical_player_name(roster_source_path, player_id)
    first = rows[0]
    weekly = [_proof_row(row, player_name, source_payload, source_path) for row in rows]
    weekly_sum = _round(sum(row["pprPoints"] for row in weekly), 2)
    totals = _season_totals(rows)
    if totals["pprPoints"] != weekly_sum:
        raise ValueError(
            f"Season PPR total {totals['pprPoints']} does not equal weekly sum {weekly_sum}."
        )

    return {
        "artifactId": "forge_player_weekly_ppr_2025_jamarr_chase.proof",
        "schemaVersion": SCHEMA_VERSION,
        "proofType": "one_player_source_backed_weekly_ppr_game_log",
        "playerId": player_id,
        "playerName": player_name,
        "team": str(first.get("team", "")).strip(),
        "position": str(first.get("position", "")).strip().upper(),
        "season": SEASON,
        "scoringFormat": SCORING_FORMAT,
        "scoringFormula": {
            "format": SCORING_FORMAT,
            "formula": FORMULA,
            "rules": SCORING_RULES,
            "rounding": (
                "round half even via Python round(..., 2), "
                "matching existing FORGE PPR artifacts"
            ),
        },
        "source": {
            "provider": "nflverse via nflreadpy",
            "file": str(source_path),
            "path": source_payload.get("source_path"),
            "provenance": source_payload.get("provenance"),
            "generatedFrom": source_payload.get("generated_from", []),
        },
        "asOf": DEFAULT_AS_OF,
        "sourceUpdatedAt": DEFAULT_AS_OF,
        "buildId": BUILD_ID,
        "seasonTotal": totals,
        "records": weekly,
    }


def validate_proof(proof: dict[str, Any]) -> None:
    if not proof.get("playerId") or not proof.get("playerName"):
        raise ValueError("Proof artifact must include player identity.")
    if (
        not proof.get("source")
        or not proof["source"].get("provider")
        or not proof["source"].get("file")
    ):
        raise ValueError("Proof artifact must include source metadata.")
    serialized = json.dumps(proof).lower()
    if "offline_fixture" in serialized or "sample" in serialized:
        raise ValueError("Proof artifact must not use fixture/sample flags or paths.")

    weekly_sum = _round(sum(float(row["pprPoints"]) for row in proof.get("records", [])), 2)
    if weekly_sum != proof.get("seasonTotal", {}).get("pprPoints"):
        raise ValueError("Proof artifact season total must equal sum of weekly PPR.")

    for row in proof.get("records", []):
        formula_points = _round(
            _number_or_zero(row.get("receptions"))
            + _number_or_zero(row.get("receivingYards")) / 10
            + _number_or_zero(row.get("receivingTDs")) * 6
            + _number_or_zero(row.get("rushingYards")) / 10
            + _number_or_zero(row.get("rushingTDs")) * 6
            + _number_or_zero(row.get("passingYards")) / 25
            + _number_or_zero(row.get("passingTDs")) * 4
            + _number_or_zero(row.get("interceptions")) * -2
            + _number_or_zero(row.get("fumblesLost")) * -2,
            2,
        )
        if formula_points != row["pprPoints"]:
            raise ValueError(
                f"Week {row.get('week')} PPR {row['pprPoints']} "
                f"does not match formula {formula_points}."
            )
        for required in ("sourceProvider", "sourceFile", "asOf", "sourceUpdatedAt", "buildId"):
            if not row.get(required):
                raise ValueError(
                    f"Week {row.get('week')} is missing source metadata field {required}."
                )


def write_proof(output_path: Path = OUTPUT_PATH) -> Path:
    proof = build_proof()
    validate_proof(proof)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(proof, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return output_path


def main() -> None:
    path = write_proof()
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()

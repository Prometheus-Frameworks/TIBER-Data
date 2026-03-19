from __future__ import annotations

from dataclasses import dataclass

from src.utils.frames import require_polars


@dataclass(slots=True)
class ValidationRule:
    table_name: str
    required_columns: list[str]
    unique_key: list[str]
    non_negative_columns: list[str]


class ValidationError(RuntimeError):
    pass


def validate_frame(frame, rule: ValidationRule) -> None:
    pl = require_polars()
    missing = [column for column in rule.required_columns if column not in frame.columns]
    if missing:
        raise ValidationError(f"{rule.table_name} is missing required columns: {missing}")

    duplicates = frame.group_by(rule.unique_key).len().filter(pl.col("len") > 1)
    if duplicates.height:
        raise ValidationError(
            f"{rule.table_name} has duplicate primary keys for columns {rule.unique_key}"
        )

    for column in rule.non_negative_columns:
        if column not in frame.columns:
            continue
        invalid = frame.filter(pl.col(column) < 0)
        if invalid.height:
            raise ValidationError(f"{rule.table_name} has negative values in {column}")

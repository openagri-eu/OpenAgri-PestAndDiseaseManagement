from __future__ import annotations

from datetime import datetime, time as _time
from typing import Any, Iterable

import numpy as np
import pandas as pd

from agstack_pnd.foundation.types import (
    ModelResult,
    ThreatDefinition,
    ThreatType,
    WeatherDataFrame,
)

FIELD_MAP: dict[str, str] = {
    "atmospheric_temperature": "air_temperature",
    "atmospheric_relative_humidity": "relative_humidity",
    "precipitation": "precipitation",
    "average_wind_speed": "wind_speed",
    "atmospheric_pressure": "atmospheric_pressure",
}

_BIOPARAM_RENAME: dict[str, str] = {"pheno_frac_ref_gdd5": "pheno_fraction_ref_gdd5"}

_TYPE_FROM_RULE: dict[str, ThreatType] = {
    "fungal": ThreatType.FUNGUS,
    "insect": ThreatType.INSECT,
}


def _to_float(value: Any, default: float) -> float:
    return default if value is None else float(value)


def _float_array(values: Iterable[Any]) -> np.ndarray | None:
    arr = [np.nan if v is None else float(v) for v in values]
    if all(np.isnan(x) for x in arr):
        return None
    return np.array(arr, dtype=float)


def _build_wdf(
    timestamps: Any, raw_fields: dict[str, Iterable[Any]]
) -> WeatherDataFrame:
    fields = {
        name: arr
        for name, values in raw_fields.items()
        if (arr := _float_array(values)) is not None
    }
    return WeatherDataFrame(timestamps=np.asarray(timestamps), fields=fields)


def _row_timestamp(row: Any) -> np.datetime64:
    clock = getattr(row, "time", None) or _time()
    return np.datetime64(datetime.combine(row.date, clock))


def _row_columns(rows: list[Any]) -> dict[str, list[Any]]:
    columns: dict[str, list[Any]] = {canonical: [] for canonical in FIELD_MAP.values()}
    for row in rows:
        for source_attr, canonical in FIELD_MAP.items():
            columns[canonical].append(getattr(row, source_attr, None))
    return columns


def _infer_threat_type(definition: dict) -> ThreatType:
    for rule in definition.get("fuzzy_rules") or []:
        rule_type = (rule.get("type") or "").lower()
        if rule_type in _TYPE_FROM_RULE:
            return _TYPE_FROM_RULE[rule_type]
    return ThreatType.FUNGUS


def _resolve_threat_type(tm: Any, definition: dict) -> ThreatType:
    explicit = getattr(tm, "threat_type", None)
    if explicit:
        try:
            return ThreatType(str(explicit).lower())
        except ValueError:
            pass
    return _infer_threat_type(definition)


def _crop_name(tm: Any) -> str:
    crop = getattr(tm, "crop", None)
    if crop is not None and getattr(crop, "name", None):
        return crop.name
    return getattr(tm, "crop_name", "")


_GATE_NEUTRAL: dict[str, Any] = {
    "t_lethal_min": -1.0e9,
    "t_lethal_max": 1.0e9,
    "min_streak": 1,
    "min_wetness_hours_critical": 0.0,
    "min_wetness_hours_high": 0.0,
}


def _package_bio_params(raw: dict) -> dict:
    raw = raw or {}
    cleaned: dict[str, Any] = {}
    for key, value in raw.items():
        if value is None:
            continue
        cleaned[_BIOPARAM_RENAME.get(key, key)] = value

    for key, neutral in _GATE_NEUTRAL.items():
        if raw.get(key) is None:
            cleaned[key] = neutral

    cleaned["pheno_lo"] = -1.0e9
    cleaned["pheno_hi"] = 1.0e9
    cleaned.pop("pheno_frac_lo", None)
    cleaned.pop("pheno_frac_hi", None)
    return cleaned


def _clean_rule(rule: dict) -> dict:
    return {
        "hum_lo": _to_float(rule.get("hum_lo"), 0.0),
        "hum_hi": _to_float(rule.get("hum_hi"), 100.0),
        "temp_lo": _to_float(rule.get("temp_lo"), -999.0),
        "temp_hi": _to_float(rule.get("temp_hi"), 999.0),
        "rain_min": _to_float(rule.get("rain_min"), 0.0),
        "risk_level": rule.get("risk_level") or "low",
    }


def daily_df_to_wdf(daily: pd.DataFrame) -> WeatherDataFrame:
    temp_avg = (daily["temp_max"].astype(float) + daily["temp_min"].astype(float)) / 2.0
    return _build_wdf(
        pd.to_datetime(daily["date"]).to_numpy(),
        {
            "air_temperature": temp_avg,
            "relative_humidity": daily["humidity"],
            "precipitation": daily["rainfall"],
        },
    )


def hourly_rows_to_wdf(rows: Iterable[Any]) -> WeatherDataFrame:
    rows = list(rows)
    timestamps = [_row_timestamp(r) for r in rows]
    return _build_wdf(timestamps, _row_columns(rows))


def threatmodel_to_definition(tm: Any) -> ThreatDefinition:
    definition = tm.definition or {}
    return ThreatDefinition.model_validate(
        {
            "scientific_name": tm.scientific_name,
            "common_name": tm.common_name,
            "crop": _crop_name(tm),
            "threat_type": _resolve_threat_type(tm, definition),
            "bio_params": _package_bio_params(definition.get("bio_params") or {}),
            "fuzzy_rules": [
                _clean_rule(r) for r in (definition.get("fuzzy_rules") or [])
            ],
        }
    )


def result_to_rows(result: ModelResult, tm: Any) -> list[dict]:
    return [
        {
            "date": score.date,
            "scientific_name": tm.scientific_name,
            "common_name": tm.common_name,
            "risk_score": score.value,
            "risk_class": score.risk_level.value.title() if score.risk_level else "Low",
            "detail": "",
        }
        for score in result.daily_scores
    ]

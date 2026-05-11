"""
Fuzzy risk calculation endpoints.
Replaces the rule-engine risk functions in data.py / tool.py.
"""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

import crud
from api import deps
from schemas.fuzzy_risk import (
    FuzzyRiskCalculateRequest,
    FuzzyRiskFetchRequest,
    FuzzyRiskForecastRequest,
)
from utils.data import (
    _dedupe_and_store_hourly,
    fetch_archive_hourly_for_range,
    fetch_forecast_hourly_for_range,
)
from utils.fuzzy_risk import (
    _format_results,
    _hourly_df_to_daily,
    _openmeteo_to_daily_df,
    _resolve_threat_models,
    _weather_rows_to_daily_df,
    calculate_fuzzy_risk,
)

router = APIRouter()


@router.post("/calculate/", dependencies=[Depends(deps.get_jwt)])
def calculate_risk(
    req: FuzzyRiskCalculateRequest,
    response_format: Literal["json", "json-ld"] = Query(default="json-ld", alias="format"),
    db: Session = Depends(deps.get_db),
):
    """Historical fuzzy risk from stored weather data."""
    parcel = crud.parcel.get(db=db, id=req.parcel_id)
    if not parcel:
        raise HTTPException(status_code=404, detail="Parcel not found")

    rows = crud.data.get_data_by_parcel_id_and_date_interval(
        db=db, parcel_id=req.parcel_id,
        start=req.from_date, end=req.to_date,
    )
    daily_df = _weather_rows_to_daily_df(rows)
    if daily_df.empty:
        raise HTTPException(status_code=404, detail="No weather data for this parcel and date range")

    threat_models = _resolve_threat_models(db, req.threat_model_ids)
    if not threat_models:
        raise HTTPException(status_code=404, detail="No threat models found")

    results = calculate_fuzzy_risk(daily_df, threat_models)
    return _format_results(results, parcel, response_format)


@router.post("/forecast/", dependencies=[Depends(deps.get_jwt)])
def forecast_risk(
    req: FuzzyRiskForecastRequest,
    response_format: Literal["json", "json-ld"] = Query(default="json-ld", alias="format"),
    db: Session = Depends(deps.get_db),
):
    """Forecast fuzzy risk via OpenMeteo."""
    parcel = crud.parcel.get(db=db, id=req.parcel_id)
    if not parcel:
        raise HTTPException(status_code=404, detail="Parcel not found")

    days = req.days_ahead or 7
    daily_df = _openmeteo_to_daily_df(parcel.latitude, parcel.longitude, days)
    if daily_df.empty:
        raise HTTPException(status_code=502, detail="No forecast data returned from OpenMeteo")

    threat_models = _resolve_threat_models(db, req.threat_model_ids)
    if not threat_models:
        raise HTTPException(status_code=404, detail="No threat models found")

    results = calculate_fuzzy_risk(daily_df, threat_models)
    return _format_results(results, parcel, response_format)


@router.post("/historical/", dependencies=[Depends(deps.get_jwt)])
def historical_fetch_and_calculate(
    req: FuzzyRiskFetchRequest,
    response_format: Literal["json", "json-ld"] = Query(default="json-ld", alias="format"),
    db: Session = Depends(deps.get_db),
):
    """Fetch historical weather from the OpenMeteo archive API for a date range,
    store new rows (dedupe on parcel+date+time), and calculate fuzzy risk."""
    if req.from_date > req.to_date:
        raise HTTPException(status_code=422, detail="from_date must be <= to_date")

    parcel = crud.parcel.get(db=db, id=req.parcel_id)
    if not parcel:
        raise HTTPException(status_code=404, detail="Parcel not found")

    threat_models = _resolve_threat_models(db, req.threat_model_ids)
    if not threat_models:
        raise HTTPException(status_code=404, detail="No threat models found")

    try:
        hourly_df = fetch_archive_hourly_for_range(
            parcel.latitude, parcel.longitude, req.from_date, req.to_date,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"OpenMeteo archive error: {e}")

    if hourly_df.empty:
        raise HTTPException(status_code=502, detail="No data returned from OpenMeteo archive")

    _dedupe_and_store_hourly(db, hourly_df, req.parcel_id, req.from_date, req.to_date)

    daily_df = _hourly_df_to_daily(hourly_df)
    results  = calculate_fuzzy_risk(daily_df, threat_models)
    return _format_results(results, parcel, response_format)


@router.post("/forecast-fetch/", dependencies=[Depends(deps.get_jwt)])
def forecast_fetch_and_calculate(
    req: FuzzyRiskFetchRequest,
    response_format: Literal["json", "json-ld"] = Query(default="json-ld", alias="format"),
    db: Session = Depends(deps.get_db),
):
    """Fetch weather from the OpenMeteo forecast API for a date range,
    store new rows (dedupe on parcel+date+time), and calculate fuzzy risk."""
    if req.from_date > req.to_date:
        raise HTTPException(status_code=422, detail="from_date must be <= to_date")

    parcel = crud.parcel.get(db=db, id=req.parcel_id)
    if not parcel:
        raise HTTPException(status_code=404, detail="Parcel not found")

    threat_models = _resolve_threat_models(db, req.threat_model_ids)
    if not threat_models:
        raise HTTPException(status_code=404, detail="No threat models found")

    try:
        hourly_df = fetch_forecast_hourly_for_range(
            parcel.latitude, parcel.longitude, req.from_date, req.to_date,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"OpenMeteo forecast error: {e}")

    if hourly_df.empty:
        raise HTTPException(status_code=502, detail="No data returned from OpenMeteo forecast")

    _dedupe_and_store_hourly(db, hourly_df, req.parcel_id, req.from_date, req.to_date)

    daily_df = _hourly_df_to_daily(hourly_df)
    results  = calculate_fuzzy_risk(daily_df, threat_models)
    return _format_results(results, parcel, response_format)

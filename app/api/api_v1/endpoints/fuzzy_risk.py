"""
Fuzzy risk calculation endpoints.
Replaces the rule-engine risk functions in data.py / tool.py.
"""

from __future__ import annotations

import datetime
import uuid
from typing import List, Literal, Optional

import openmeteo_requests
import pandas as pd
import requests_cache
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from retry_requests import retry
from sqlalchemy.orm import Session

import crud
from api import deps
from core.config import settings
from models import Data
from schemas import NewCreateData
from schemas.threat_model import ThreatModelDB
from utils.custom_schemas import context as OPENAGRI_CONTEXT
from utils.data import (
    fetch_archive_hourly_for_range,
    fetch_forecast_hourly_for_range,
)
from utils.fuzzy_risk import calculate_fuzzy_risk

router = APIRouter()


# ─── request bodies ──────────────────────────────────────────────────────────

class FuzzyRiskCalculateRequest(BaseModel):
    parcel_id:         int
    from_date:         datetime.date
    to_date:           datetime.date
    threat_model_ids:  Optional[List[uuid.UUID]] = None  # None = all


class FuzzyRiskForecastRequest(BaseModel):
    parcel_id:         int
    threat_model_ids:  Optional[List[uuid.UUID]] = None
    days_ahead:        Optional[int] = 7


class FuzzyRiskFetchRequest(BaseModel):
    parcel_id:         int
    from_date:         datetime.date
    to_date:           datetime.date
    threat_model_ids:  Optional[List[uuid.UUID]] = None
    format:            Literal["json", "json-ld"] = "json-ld"


# ─── helpers ─────────────────────────────────────────────────────────────────

def _weather_rows_to_daily_df(rows) -> pd.DataFrame:
    """Aggregate DB hourly rows to one row per calendar day."""
    if not rows:
        return pd.DataFrame(columns=["date", "temp_max", "temp_min", "humidity", "rainfall"])
    records = [
        {
            "date":     r.date,
            "temp":     r.atmospheric_temperature,
            "humidity": r.atmospheric_relative_humidity,
            "rainfall": r.precipitation or 0.0,
        }
        for r in rows
        if r.atmospheric_temperature is not None
    ]
    if not records:
        return pd.DataFrame(columns=["date", "temp_max", "temp_min", "humidity", "rainfall"])
    df = pd.DataFrame(records)
    daily = df.groupby("date").agg(
        temp_max=("temp", "max"),
        temp_min=("temp", "min"),
        humidity=("humidity", "mean"),
        rainfall=("rainfall", "sum"),
    ).reset_index()
    daily["date"] = pd.to_datetime(daily["date"])
    return daily.sort_values("date").reset_index(drop=True)


def _openmeteo_to_daily_df(latitude: float, longitude: float, days_ahead: int) -> pd.DataFrame:
    """Fetch hourly forecast from OpenMeteo and aggregate to daily."""
    if days_ahead < settings.OPEN_METEO_MIN_FORECAST_DAYS:
        days_ahead = settings.OPEN_METEO_MIN_FORECAST_DAYS
    if days_ahead > settings.OPEN_METEO_MAX_FORECAST_DAYS:
        days_ahead = settings.OPEN_METEO_MAX_FORECAST_DAYS

    cache_sess   = requests_cache.CachedSession(".cache", expire_after=3600)
    retry_sess   = retry(cache_sess, retries=3, backoff_factor=0.2)
    client       = openmeteo_requests.Client(session=retry_sess)

    try:
        responses = client.weather_api(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude":       latitude,
                "longitude":      longitude,
                "hourly":         ["temperature_2m", "relative_humidity_2m", "precipitation"],
                "forecast_days":  days_ahead,
            },
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"OpenMeteo error: {e}")
    finally:
        client.session.close()

    hourly  = responses[0].Hourly()
    dates   = pd.date_range(
        start=pd.to_datetime(hourly.Time(),    unit="s", utc=True),
        end=pd.to_datetime(hourly.TimeEnd(),   unit="s", utc=True),
        freq=pd.Timedelta(seconds=hourly.Interval()),
        inclusive="left",
    ).tz_localize(None)

    df = pd.DataFrame({
        "date":     dates.date,
        "temp":     hourly.Variables(0).ValuesAsNumpy(),
        "humidity": hourly.Variables(1).ValuesAsNumpy(),
        "rainfall": hourly.Variables(2).ValuesAsNumpy(),
    })

    daily = df.groupby("date").agg(
        temp_max=("temp", "max"),
        temp_min=("temp", "min"),
        humidity=("humidity", "mean"),
        rainfall=("rainfall", "sum"),
    ).reset_index()
    daily["date"] = pd.to_datetime(daily["date"])
    return daily.sort_values("date").reset_index(drop=True)


def _results_to_jsonld(results_df: pd.DataFrame, parcel, include_meta: bool = True) -> dict:
    """Convert calculate_fuzzy_risk output to OpenAGRI JSON-LD envelope."""
    graph = []
    for sci_name, grp in results_df.groupby("scientific_name"):
        common = grp["common_name"].iloc[0]
        observations = []
        for _, row in grp.iterrows():
            obs = {
                "@id":            f"urn:openagri:fuzzyRisk:obs:{uuid.uuid4()}",
                "@type":          ["Observation", "PestInfestationRisk"],
                "phenomenonTime": str(row["date"].date()),
                "hasSimpleResult": f"{row['risk_score']:.1f}",
                "riskClass":       row["risk_class"],
            }
            if include_meta and row.get("detail"):
                obs["meta"] = row["detail"]
            observations.append(obs)

        graph.append({
            "@id":   f"urn:openagri:fuzzyRisk:col:{uuid.uuid4()}",
            "@type": ["ObservationCollection"],
            "description": f"Fuzzy risk for {sci_name} ({common})",
            "observedProperty": {
                "@id":   f"urn:openagri:fuzzyRisk:op:{uuid.uuid4()}",
                "@type": ["ObservableProperty", "PestInfection"],
                "name":  sci_name,
                "commonName": common,
            },
            "madeBySensor": {
                "@id":   f"urn:openagri:fuzzyRisk:model:{uuid.uuid4()}",
                "@type": ["Sensor", "FuzzyRiskModel"],
                "name":  "Fuzzy Pest & Disease Risk Model v2.0",
            },
            "hasFeatureOfInterest": {
                "@id":   f"urn:openagri:fuzzyRisk:foi:{uuid.uuid4()}",
                "@type": ["FeatureOfInterest", "Point"],
                "long":  str(parcel.longitude),
                "lat":   str(parcel.latitude),
            },
            "resultTime":  datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "hasMember":   observations,
        })

    return {"@context": OPENAGRI_CONTEXT, "@graph": graph}


def _hourly_df_to_daily(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate an OpenMeteo hourly DataFrame (DB column names) to daily records
    suitable for calculate_fuzzy_risk."""
    if df.empty:
        return pd.DataFrame(columns=["date", "temp_max", "temp_min", "humidity", "rainfall"])

    work = pd.DataFrame({
        "date":     pd.to_datetime(df["date"]).dt.tz_localize(None).dt.date,
        "temp":     df["atmospheric_temperature"],
        "humidity": df["atmospheric_relative_humidity"],
        "rainfall": df["precipitation"].fillna(0.0),
    })
    daily = work.groupby("date").agg(
        temp_max=("temp",     "max"),
        temp_min=("temp",     "min"),
        humidity=("humidity", "mean"),
        rainfall=("rainfall", "sum"),
    ).reset_index()
    daily["date"] = pd.to_datetime(daily["date"])
    return daily.sort_values("date").reset_index(drop=True)


def _dedupe_and_store_hourly(
    db: Session,
    hourly_df: pd.DataFrame,
    parcel_id: int,
    from_date: datetime.date,
    to_date:   datetime.date,
) -> int:
    """Insert hourly rows for the parcel, skipping any that already exist for
    the same (date, time). Returns the count of rows inserted."""
    if hourly_df.empty:
        return 0

    existing = db.query(Data.date, Data.time).filter(
        Data.parcel_id == parcel_id,
        Data.date.between(from_date, to_date),
    ).all()
    existing_keys = {(row.date, row.time) for row in existing}

    records: list[NewCreateData] = []
    for row in hourly_df.itertuples(index=False):
        ts = row.date
        if hasattr(ts, "to_pydatetime"):
            ts = ts.to_pydatetime()
        d = ts.date()
        t = ts.time().replace(tzinfo=None)
        if (d, t) in existing_keys:
            continue

        def _f(v):
            return None if pd.isna(v) else float(v)

        records.append(NewCreateData(
            date=d,
            time=t,
            atmospheric_temperature       = _f(getattr(row, "atmospheric_temperature",       float("nan"))),
            atmospheric_relative_humidity = _f(getattr(row, "atmospheric_relative_humidity", float("nan"))),
            atmospheric_pressure          = _f(getattr(row, "atmospheric_pressure",          float("nan"))),
            precipitation                 = _f(getattr(row, "precipitation",                 float("nan"))),
            average_wind_speed            = _f(getattr(row, "average_wind_speed",            float("nan"))),
            soil_temperature_10cm         = _f(getattr(row, "soil_temperature_10cm",         float("nan"))),
            soil_temperature_20cm         = _f(getattr(row, "soil_temperature_20cm",         float("nan"))),
            soil_temperature_30cm         = _f(getattr(row, "soil_temperature_30cm",         float("nan"))),
            soil_temperature_40cm         = _f(getattr(row, "soil_temperature_40cm",         float("nan"))),
        ))

    if not records:
        return 0
    crud.data.batch_insert(db=db, list_of_data=records, parcel_id=parcel_id)
    return len(records)


def _format_results(results_df: pd.DataFrame, parcel, fmt: str) -> dict | list:
    """Return raw JSON records or OpenAGRI JSON-LD envelope, depending on fmt."""
    if fmt == "json":
        out = results_df.copy()
        out["date"] = pd.to_datetime(out["date"]).dt.strftime("%Y-%m-%d")
        return out.to_dict(orient="records")
    return _results_to_jsonld(results_df, parcel)


def _resolve_threat_models(
    db: Session, threat_model_ids: Optional[List[uuid.UUID]]
) -> List[ThreatModelDB]:
    if threat_model_ids:
        models = [crud.threat_model.get(db=db, id=tid) for tid in threat_model_ids]
        missing = [str(tid) for tm, tid in zip(models, threat_model_ids) if tm is None]
        if missing:
            raise HTTPException(status_code=404, detail=f"ThreatModels not found: {missing}")
    else:
        models = crud.threat_model.get_multi(db=db, limit=10000)

    return [ThreatModelDB.model_validate(tm) for tm in models]


# ─── endpoints ────────────────────────────────────────────────────────────────

@router.post("/calculate/", dependencies=[Depends(deps.get_jwt)])
def calculate_risk(
    req: FuzzyRiskCalculateRequest,
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
    return _results_to_jsonld(results, parcel)


@router.post("/forecast/", dependencies=[Depends(deps.get_jwt)])
def forecast_risk(
    req: FuzzyRiskForecastRequest,
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
    return _results_to_jsonld(results, parcel)


@router.post("/historical/", dependencies=[Depends(deps.get_jwt)])
def historical_fetch_and_calculate(
    req: FuzzyRiskFetchRequest,
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
    return _format_results(results, parcel, req.format)


@router.post("/forecast-fetch/", dependencies=[Depends(deps.get_jwt)])
def forecast_fetch_and_calculate(
    req: FuzzyRiskFetchRequest,
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
    return _format_results(results, parcel, req.format)

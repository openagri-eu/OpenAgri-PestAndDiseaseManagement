import datetime
from datetime import timedelta

import openmeteo_requests
import pandas as pd
import requests_cache
from retry_requests import retry
from sqlalchemy.orm import Session

import crud
from models import Data, Parcel
from schemas import NewCreateData


def fetch_historical_data_for_parcel(db: Session, parcel: Parcel):
    cache_session = requests_cache.CachedSession('.cache', expire_after=-1)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)

    start_date = (datetime.datetime.now() - timedelta(days=365)).date()
    end_date = (datetime.datetime.now() - timedelta(days=2)).date()

    try:
        responses = openmeteo.weather_api(
            "https://archive-api.open-meteo.com/v1/archive",
            params={
                "latitude": parcel.latitude,
                "longitude": parcel.longitude,
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "hourly": _FULL_HOURLY_FIELDS,
                "timezone": "auto",
                "elevation": "NaN",
            },
        )
    finally:
        openmeteo.session.close()

    hourly_dataframe = _openmeteo_response_to_dataframe(responses[0].Hourly(), _FULL_HOURLY_FIELDS)
    hourly_dataframe["date"] = hourly_dataframe["date"].astype(str)

    crud.data.batch_insert(
        db=db,
        list_of_data=[
            NewCreateData(
                date=x.date.split(" ")[0],
                time=x.date.split(" ")[1],
                atmospheric_temperature=x.atmospheric_temperature,
                atmospheric_relative_humidity=x.atmospheric_relative_humidity,
                precipitation=x.precipitation,
                atmospheric_pressure=x.atmospheric_pressure,
                average_wind_speed=x.average_wind_speed,
                soil_temperature_10cm=x.soil_temperature_10cm,
                soil_temperature_20cm=x.soil_temperature_20cm,
                soil_temperature_30cm=x.soil_temperature_30cm,
                soil_temperature_40cm=x.soil_temperature_40cm,
            ) for x in hourly_dataframe.itertuples(index=False)
        ],
        parcel_id=parcel.id
    )
    return


# Param values like past_days and forecast_days should be checked before calling this function
# Besides fetching the forecast data, this function also converts it into a pandas dataframe
def fetch_forecast_data_for_parcel(
    latitude: float,
    longitude: float,
    hourly_fields: list,
    past_days: int,
    forecast_days: int,
):
    cache_session = requests_cache.CachedSession(".cache", expire_after=3600)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)

    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": hourly_fields,
        "past_days": past_days,
        "forecast_days": forecast_days,
    }

    responses = openmeteo.weather_api(url, params=params)
    response = responses[0]
    hourly = response.Hourly()

    data_dict = {}
    field_count = 0
    for field in hourly_fields:
        data_dict[field] = hourly.Variables(field_count).ValuesAsNumpy()
        field_count += 1

    hourly_data = {
        "date": pd.date_range(
            start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
            end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
            freq=pd.Timedelta(seconds=hourly.Interval()),
            inclusive="left",
        )
    }

    for k, v in data_dict.items():
        hourly_data[k] = v

    hourly_dataframe = pd.DataFrame(data=hourly_data)

    return hourly_dataframe


# OpenMeteo variable name → DB Data column name
_OPENMETEO_TO_DB_COLUMNS = {
    "temperature_2m":                "atmospheric_temperature",
    "relative_humidity_2m":          "atmospheric_relative_humidity",
    "precipitation":                 "precipitation",
    "surface_pressure":              "atmospheric_pressure",
    "wind_speed_10m":                "average_wind_speed",
    "soil_temperature_0_to_7cm":     "soil_temperature_10cm",
    "soil_temperature_7_to_28cm":    "soil_temperature_20cm",
    "soil_temperature_28_to_100cm":  "soil_temperature_30cm",
    "soil_temperature_100_to_255cm": "soil_temperature_40cm",
}

_FULL_HOURLY_FIELDS = list(_OPENMETEO_TO_DB_COLUMNS.keys())


def _openmeteo_response_to_dataframe(hourly, fields: list) -> pd.DataFrame:
    """Convert an OpenMeteo hourly response object to a DataFrame with DB column names."""
    data = {
        "date": pd.date_range(
            start=pd.to_datetime(hourly.Time(),    unit="s", utc=True),
            end=pd.to_datetime(hourly.TimeEnd(),   unit="s", utc=True),
            freq=pd.Timedelta(seconds=hourly.Interval()),
            inclusive="left",
        )
    }
    for i, field in enumerate(fields):
        db_col = _OPENMETEO_TO_DB_COLUMNS.get(field, field)
        data[db_col] = hourly.Variables(i).ValuesAsNumpy()
    return pd.DataFrame(data=data)


def fetch_archive_hourly_for_range(
    latitude: float,
    longitude: float,
    start_date: datetime.date,
    end_date: datetime.date,
) -> pd.DataFrame:
    """Fetch hourly data from the OpenMeteo archive API for an arbitrary date range.

    Columns are renamed to match the DB Data model (atmospheric_temperature, etc.).
    """
    cache_session = requests_cache.CachedSession(".cache", expire_after=-1)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo     = openmeteo_requests.Client(session=retry_session)

    try:
        responses = openmeteo.weather_api(
            "https://archive-api.open-meteo.com/v1/archive",
            params={
                "latitude":   latitude,
                "longitude":  longitude,
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date":   end_date.strftime("%Y-%m-%d"),
                "hourly":     _FULL_HOURLY_FIELDS,
                "timezone":   "auto",
            },
        )
    finally:
        openmeteo.session.close()

    return _openmeteo_response_to_dataframe(responses[0].Hourly(), _FULL_HOURLY_FIELDS)


def fetch_forecast_hourly_for_range(
    latitude: float,
    longitude: float,
    start_date: datetime.date,
    end_date: datetime.date,
) -> pd.DataFrame:
    """Fetch hourly data from the OpenMeteo forecast API for the given date range.

    past_days and forecast_days are derived from the range vs today.
    Returned DataFrame is filtered to [start_date, end_date] and uses DB column names.
    """
    today        = datetime.datetime.now().date()
    past_days    = max(0, (today - start_date).days)
    forecast_days = max(1, (end_date - today).days + 1)  # forecast_days is 1-based and required

    cache_session = requests_cache.CachedSession(".cache", expire_after=3600)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo     = openmeteo_requests.Client(session=retry_session)

    try:
        responses = openmeteo.weather_api(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude":      latitude,
                "longitude":     longitude,
                "hourly":        _FULL_HOURLY_FIELDS,
                "past_days":     past_days,
                "forecast_days": forecast_days,
                "timezone":      "auto",
            },
        )
    finally:
        openmeteo.session.close()

    df = _openmeteo_response_to_dataframe(responses[0].Hourly(), _FULL_HOURLY_FIELDS)
    # Clip to requested range
    mask = (df["date"].dt.date >= start_date) & (df["date"].dt.date <= end_date)
    return df[mask].reset_index(drop=True)


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

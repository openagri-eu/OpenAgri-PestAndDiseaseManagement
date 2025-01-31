import datetime
from datetime import timedelta

import openmeteo_requests
import pandas as pd
import requests_cache
from retry_requests import retry
from sqlalchemy.orm import Session

import crud
from models import Parcel
from schemas import NewCreateData


def fetch_historical_data_for_parcel(db: Session, parcel: Parcel):


    # Set up the Open-Meteo API client with cache and retry on error
    cache_session = requests_cache.CachedSession('.cache', expire_after=-1)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)

    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": "{}".format(parcel.latitude),
        "longitude": "{}".format(parcel.longitude),
        "start_date": "{}".format((datetime.datetime.now() - timedelta(days=365)).date().strftime("%Y-%m-%d")),
        "end_date": "{}".format((datetime.datetime.now() - timedelta(days=2)).date().strftime("%Y-%m-%d")),
        "hourly": ["temperature_2m", "relative_humidity_2m", "precipitation", "surface_pressure", "wind_speed_10m",
                   "soil_temperature_0_to_7cm", "soil_temperature_7_to_28cm", "soil_temperature_28_to_100cm",
                   "soil_temperature_100_to_255cm"],
        "timezone": "auto",
        "elevation": "NaN"
        }
    responses = openmeteo.weather_api(url, params=params)

    # Process hourly data. The order of variables needs to be the same as requested.
    hourly = responses[0].Hourly()
    hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
    hourly_relative_humidity_2m = hourly.Variables(1).ValuesAsNumpy()
    hourly_precipitation = hourly.Variables(2).ValuesAsNumpy()
    hourly_surface_pressure = hourly.Variables(3).ValuesAsNumpy()
    hourly_wind_speed_10m = hourly.Variables(4).ValuesAsNumpy()
    hourly_soil_temperature_0_to_7cm = hourly.Variables(5).ValuesAsNumpy()
    hourly_soil_temperature_7_to_28cm = hourly.Variables(6).ValuesAsNumpy()
    hourly_soil_temperature_28_to_100cm = hourly.Variables(7).ValuesAsNumpy()
    hourly_soil_temperature_100_to_255cm = hourly.Variables(8).ValuesAsNumpy()

    hourly_data = {"date": pd.date_range(
        start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
        end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
        freq=pd.Timedelta(seconds=hourly.Interval()),
        inclusive="left"
    )}

    hourly_data["temperature_2m"] = hourly_temperature_2m
    hourly_data["relative_humidity_2m"] = hourly_relative_humidity_2m
    hourly_data["precipitation"] = hourly_precipitation
    hourly_data["surface_pressure"] = hourly_surface_pressure
    hourly_data["wind_speed_10m"] = hourly_wind_speed_10m
    hourly_data["soil_temperature_0_to_7cm"] = hourly_soil_temperature_0_to_7cm
    hourly_data["soil_temperature_7_to_28cm"] = hourly_soil_temperature_7_to_28cm
    hourly_data["soil_temperature_28_to_100cm"] = hourly_soil_temperature_28_to_100cm
    hourly_data["soil_temperature_100_to_255cm"] = hourly_soil_temperature_100_to_255cm

    hourly_dataframe = pd.DataFrame(data=hourly_data)

    hourly_dataframe["date"] = hourly_dataframe["date"].astype(str)

    crud.data.batch_insert(
        db=db,
        list_of_data=[
            NewCreateData(
                date=x[1].split(" ")[0],
                time=x[1].split(" ")[1],
                atmospheric_temperature=x[2],
                atmospheric_relative_humidity=x[3],
                precipitation=x[4],
                atmospheric_pressure=x[5],
                average_wind_speed=x[6],
                soil_temperature_10cm=x[7],
                soil_temperature_20cm=x[8],
                soil_temperature_30cm=x[9],
                soil_temperature_40cm=x[10]
            ) for x in hourly_dataframe.itertuples()
        ],
        parcel_id=parcel.id
    )


    openmeteo.session.close()
    return

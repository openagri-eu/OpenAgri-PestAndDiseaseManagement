import datetime
import uuid

import pandas
import requests
from fastapi import HTTPException
from requests import RequestException

import utils

from core import settings
from enum import Enum

import pandas as pd

WEATHER_DATA_API_CALL_URL = str(settings.GATEKEEPER_BASE_URL).strip("/") + "/api/proxy/weather_data"

class TimeUnit(Enum):
    HOURLY = "hourly"
    DAILY = "daily"

openmeteo_friendly_variables = {
    "atmospheric_temperature": "temperature_2m",
    "atmospheric_relative_humidity" : "relative_humidity_2m",
    "precipitation": "precipitation",
    "atmospheric_pressure": "surface_pressure",
    "average_wind_speed": "wind_speed_10m",
    "soil_temperature_10cm": "soil_temperature_0_to_7cm",
    "soil_temperature_20cm": "soil_temperature_7_to_28cm",
    "soil_temperature_30cm": "soil_temperature_28_to_100cm",
    "soil_temperature_40cm": "soil_temperature_100_to_255cm"
}

openweathermap_friendly_variables = {
    "timestamp": "timestamp",
    "ambient_humidity": "atmospheric_relative_humidity",
    "ambient_temperature": "atmospheric_temperature",
    "wind_speed": "average_wind_speed",
    "precipitation": "precipitation"
}

def fetch_weather_data(
        latitude: float,
        longitude: float,
        start_date: datetime.date,
        end_date: datetime.date,
        variables: list,
        access_token: str,
        radius_km: int = 10,
        how_often: TimeUnit = TimeUnit.DAILY
) -> dict:
    try:
        response = requests.post(
            url=WEATHER_DATA_API_CALL_URL + "/api/v1/history/{}/".format(how_often.value),
            headers={"Content-Type": "application/json", "Authorization": "Bearer {}".format(access_token)},
            json={
                "lat": latitude,
                "lon": longitude,
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "variables": variables,
                "radius_km": radius_km
            }
        )
    except RequestException:
        raise HTTPException(
            status_code=400,
            detail="Error during proxy call via gk"
        )

    if response.status_code == 400:
        raise HTTPException(
            status_code=400,
            detail="Error during weather data api call, original error: {}".format(response.reason)
        )

    if response.status_code == 404:
        raise HTTPException(
            status_code=400,
            detail="Error, GK returning 404, Weather Data API missing."
        )

    return response.json()


def fetch_weather_service_forecast_weather_data(
    latitude: float,
    longitude: float,
    access_token: str,
):
    try:
        response = requests.get(
            url=WEATHER_DATA_API_CALL_URL + "/api/data/forecast5/",
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer {}".format(access_token)
            },
            params={
                "lat": latitude,
                "lon": longitude
            }
        )
    except RequestException:
        raise HTTPException(
            status_code=400,
            detail="Error during proxy call via gk"
        )

    if response.status_code == 400:
        raise HTTPException(
            status_code=400,
            detail="Error during weather data api call, original error: {}".format(response.reason)
        )

    if response.status_code == 404:
        raise HTTPException(
            status_code=400,
            detail="Error, GK returning 404, Weather Data API missing."
        )

    return convert_weather_service_forecast_weather_data_to_dataframe(response.json())

def convert_weather_service_forecast_weather_data_to_dataframe(
    json_data: list
):
    df = pd.json_normalize(json_data)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df_pivoted = df.pivot(index='timestamp', columns='measurement_type', values='value')
    df_pivoted.columns.name = None
    df_pivoted.reset_index(inplace=True)
    return df_pivoted


def calculate_risk_index_forecast_wd(
    df: pandas.DataFrame,
    parcel,
    pest_models: list
):
    reverse_dict = {v: k for k, v in openweathermap_friendly_variables.items()}
    df.rename(columns=reverse_dict, inplace=True)

    valid_columns = df.columns.intersection(openweathermap_friendly_variables.keys())
    df = df[valid_columns].rename(columns=openweathermap_friendly_variables)

    for pm in pest_models:
        risks_for_current_pm = ["Low"] * df.shape[0]

        for rule in pm.rules:
            final_str = "(x['{}'] {} {})".format(
                rule.conditions[0].unit.name,
                rule.conditions[0].operator.symbol,
                rule.conditions[0].value,
            )
            for cond in rule.conditions[1:]:
                final_str = (final_str + " & " + "(x['{}'] {} {})".format(
                    cond.unit.name, cond.operator.symbol, cond.value
                )
                             )

            df_with_risk = df.assign(
                risk=eval("lambda x: {}".format(final_str))
            )

            risks_for_current_pm = [
                rule.probability_value if x else y
                for x, y in zip(df_with_risk["risk"], risks_for_current_pm)
            ]

        df["{}".format(pm.name)] = risks_for_current_pm

    context = utils.context

    graph = []

    for pm in pest_models:

        calculated_risks = []
        for date, risk in zip(df["timestamp"], df["{}".format(pm.name)]):
            calculated_risks.append(
                {
                    "@id": "urn:openagri:pestInfectationRisk:obs2:{}".format(
                        uuid.uuid4()
                    ),
                    "@type": ["Observation", "PestInfestationRisk"],
                    "phenomenonTime": "{}".format(str(date).replace(" ", "T")),
                    "hasSimpleResult": "{}".format(risk),
                }
            )

        graph_element = {
            "@id": "urn:openagri:pestInfectationRisk:{}".format(uuid.uuid4()),
            "@type": ["ObservationCollection"],
            "description": "{} pest infectation risk forecast in x ".format(pm.name),
            "observedProperty": {
                "@id": "urn:openagri:pestInfectationRisk:op:{}".format(uuid.uuid4()),
                "@type": ["ObservableProperty", "PestInfection"],
                "name": "UNCINE pest infection",
                "hasAgriPest": {
                    "@id": "urn:openagri:pest:UNCINE",
                    "@type": "AgriPest",
                    "name": "UNCINE",
                    "description": "Uncinula necator (syn. Erysiphe necator) is a fungus that causes powdery mildew of grape. It is a common pathogen of Vitis species, including the wine grape, Vitis vinifera",
                    "eppoConcept": "https://gd.eppo.int/taxon/UNCINE",
                },
            },
            "madeBySensor": {
                "@id": "urn:openagri:pestInfectationRisk:model:{}".format(uuid.uuid4()),
                "@type": ["Sensor", "AIPestDetectionModel"],
                "name": "AI pest detaction model xyz",
            },
            "hasFeatureOfInterest": {
                "@id": "urn:openagri:pestInfectationRisk:foi:{}".format(uuid.uuid4()),
                "@type": ["FeatureOfInterest", "Point"],
                "long": "{}".format(parcel["location"]["long"]),
                "lat": "{}".format(parcel["location"]["lat"]),
            },
            "basedOnWeatherDataset": {
                "@id": "urn:openagri:weatherDataset:{}".format(parcel["@id"]),
                "@type": "WeatherDataset",
                "name": "parcel_name_tba",
            },
            "resultTime": "{}".format(
                datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            ),
            "hasMember": calculated_risks,
        }

        graph.append(graph_element)

    doc = {"@context": context, "@graph": graph}

    return doc

import datetime
from typing import List, Optional

from pandas import DataFrame
from sqlalchemy.orm import Session
import pandas as pd

import crud
import utils
import uuid

from models import PestModel, Parcel
from .wdutils import openmeteo_friendly_variables

prob_values = {
    "low": 1,
    "moderate": 2,
    "high": 3
}


def _build_observation(timestamp: str, risk: str) -> dict:
    return {
        "@id": "urn:openagri:pestInfectationRisk:obs2:{}".format(uuid.uuid4()),
        "@type": ["Observation", "PestInfestationRisk"],
        "phenomenonTime": timestamp,
        "hasSimpleResult": "{}".format(risk),
    }


def _build_graph_element(pm: PestModel, lat: float, lon: float, parcel_id, calculated_risks: list) -> dict:
    return {
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
            "long": "{}".format(lon),
            "lat": "{}".format(lat),
        },
        "basedOnWeatherDataset": {
            "@id": "urn:openagri:weatherDataset:{}".format(parcel_id),
            "@type": "WeatherDataset",
            "name": "parcel_name_tba",
        },
        "resultTime": "{}".format(datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")),
        "hasMember": calculated_risks,
    }


def calculate_risk_index_probability(db: Session, parcel: Parcel, pest_models: List[PestModel],
                                     from_date: datetime.date, to_date:datetime.date,
                                     parameter: Optional[str] = None):
    data_db = crud.data.get_data_query_by_parcel_id_and_date_interval(db=db, parcel_id=parcel.id,
                                                                      date_from=from_date, date_to=to_date)

    df = pd.read_sql(sql=data_db.statement, con=db.bind, parse_dates={"date": "%Y-%m-%d"})

    for pm in pest_models:
        risks_for_current_pm = ["Low"] * df.shape[0]

        for rule in pm.rules:
            final_str = "(x['{}'] {} {})".format(rule.conditions[0].unit.name, rule.conditions[0].operator.symbol, float(rule.conditions[0].value))
            for cond in rule.conditions[1:]:
                final_str = final_str + " & " + "(x['{}'] {} {})".format(cond.unit.name, cond.operator.symbol, float(cond.value))

            df_with_risk = df.assign(risk=eval("lambda x: {}".format(final_str)))

            risks_for_current_pm = [rule.probability_value if x else y for x, y in zip(df_with_risk["risk"], risks_for_current_pm)]

        df["{}".format(pm.name)] = risks_for_current_pm

    graph = []
    for pm in pest_models:
        calculated_risks = []
        for date, time, risk in zip(df["date"], df["time"], df["{}".format(pm.name)]):
            if parameter and risk != parameter:
                continue
            calculated_risks.append(_build_observation(
                "{}".format(str(date).split(" ")[0] + "T" + str(time)), risk
            ))

        graph.append(_build_graph_element(pm, parcel.latitude, parcel.longitude, parcel.id, calculated_risks))

    return {"@context": utils.context, "@graph": graph}


def calculate_risk_index_probability_wd(
        parcel: dict,
        pest_models: List[PestModel],
        weather_data: dict,
        lat: float,
        lon: float,
        parameter: Optional[str] = None
):
    graph = []

    for pm in pest_models:
        calculated_risks = []

        for hour in weather_data["data"]:
            current_rule_risk_index = "low"
            for rule in pm.rules:
                if parameter and prob_values[rule.probability_value] < prob_values[parameter]:
                    continue

                if rule.probability_value and prob_values[rule.probability_value] <= prob_values[current_rule_risk_index]:
                    continue

                current_rule_applies = True
                for cond in rule.conditions:
                    condition_applies = eval("{} {} {}".format(hour["values"][openmeteo_friendly_variables[cond.unit.name]], cond.operator.symbol, cond.value))
                    if not condition_applies:
                        current_rule_applies = False
                        break

                if current_rule_applies:
                    current_rule_risk_index = rule.probability_value

            if not parameter:
                calculated_risks.append(_build_observation(hour["timestamp"], current_rule_risk_index))
                continue

            if parameter and prob_values[current_rule_risk_index] >= prob_values[parameter]:
                calculated_risks.append(_build_observation(hour["timestamp"], current_rule_risk_index))

        graph.append(_build_graph_element(pm, lat, lon, parcel["@id"], calculated_risks))

    return {"@context": utils.context, "@graph": graph}


def calculate_forecast_risk_index(
    parcel: Parcel, pest_models: list, weather_data: DataFrame
):
    reverse_dict = {v: k for k, v in openmeteo_friendly_variables.items()}
    weather_data.rename(columns=reverse_dict, inplace=True)

    for pm in pest_models:
        risks_for_current_pm = ["Low"] * weather_data.shape[0]

        for rule in pm.rules:
            if len(rule.conditions) == 0:
                continue
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

            df_with_risk = weather_data.assign(
                risk=eval("lambda x: {}".format(final_str))
            )

            risks_for_current_pm = [
                rule.probability_value if x else y
                for x, y in zip(df_with_risk["risk"], risks_for_current_pm)
            ]

        weather_data["{}".format(pm.name)] = risks_for_current_pm

    graph = []
    for pm in pest_models:
        calculated_risks = []
        for date, risk in zip(weather_data["date"], weather_data["{}".format(pm.name)]):
            calculated_risks.append(_build_observation(
                "{}".format(str(date).replace(" ", "T")), risk
            ))

        graph.append(_build_graph_element(pm, parcel.latitude, parcel.longitude, parcel.id, calculated_risks))

    return {"@context": utils.context, "@graph": graph}

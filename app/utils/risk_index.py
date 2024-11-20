from typing import List, Optional

from sqlalchemy.orm import Session
import pandas as pd

import crud
import utils
import uuid

from models import PestModel


def calculate_risk_index_probability(db: Session, weather_dataset_id: int, pest_models: List[PestModel], parameter: Optional[str] = None):
    # SQL query for the data
    data_db = crud.data.get_data_interval_query_by_dataset_id(db=db, dataset_id=weather_dataset_id)

    df = pd.read_sql(sql=data_db.statement, con=db.bind, parse_dates={"date": "%Y-%m-%d"})

    # Calculate the risks associated with each pest_model
    for pm in pest_models:
        risks_for_current_pm = ["Low"] * df.shape[0]

        for rule in pm.rules:
            conds = []
            for cond in rule.conditions:
                conds.append("(x['{}'] {} {})".format(cond.unit.name, cond.operator.symbol, float(cond.value)))
            pre_final_str = ""
            for cond_strs in conds[:len(conds) - 1]:
                pre_final_str = pre_final_str + cond_strs + " & "
            final_str = pre_final_str + conds[-1]

            df_with_risk = df.assign(risk=eval("lambda x: {}".format(final_str)))

            # With this, only one rule should only ever fire for one singular date/time weather data point.
            # If multiple rules turn up as valid (both are true), then the last one from the db is going to have its
            # prob. value written as a final response for this pest model
            risks_for_current_pm = [rule.probability_value if x else y for x, y in zip(df_with_risk["risk"], risks_for_current_pm)]

        df["{}".format(pm.name)] = risks_for_current_pm

    context = utils.context

    graph = []

    for pm in pest_models:

        calculated_risks = []
        for date, time, risk in zip(df["date"], df["time"], df["{}".format(pm.name)]):

            if parameter and risk != parameter:
                continue

            calculated_risks.append(
                {
                    "@id": "urn:openagri:pestPrediction:{}".format(uuid.uuid4()),
                    "@type": "fsm:PestInfestationRisk",
                    "saref:hasTimestamp": "{}".format(str(date).split(" ")[0] + "T" + str(time)),
                    "ocsm:hasRiskLevel": "{}".format(risk)
                }
            )

        calculation_response = {
            "@id": "urn:openagri:pestModel:{}".format(pm.id),
            "@type": "ocsm:AIPestDetectionModel",
            "fsm:eppoCode": "UNCINE",
            "foodie:description": "{}".format(pm.description),
            "ocsm:hasPredictedInfestationRisks": calculated_risks,
            "ocsm:basedOnWeatherDataset": {
                "@id":"urn:openagri:weatherDataset:{}".format(weather_dataset_id),
                "@type": "ocsm:WeatherDataset"
            }
        }

        graph.append(calculation_response)

    doc = {
        "@context": context,
        "@graph": graph
    }

    return doc

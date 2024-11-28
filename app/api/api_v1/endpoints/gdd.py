from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import crud
from api import deps
from models import User

import pandas as pd

router = APIRouter()

@router.get("/calculate-gdd/{weather_dataset_id}")
def calculate_gdd(
    weather_dataset_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    This API calculates the GDD for a dataset and a pest model
    """

    weather_dataset = crud.dataset.get(db=db, id=weather_dataset_id)

    if not weather_dataset:
        raise HTTPException(
            status_code=400,
            detail="Error, weather dataset with ID:{} does not exist.".format(weather_dataset_id)
        )

    data_db = crud.data.get_data_query_by_dataset_id(db=db, dataset_id=weather_dataset_id)

    df = pd.read_sql(sql=data_db.statement, con=db.bind, parse_dates={"date": "%Y-%m-%d"})

    gdd = 0
    baseline_temp = 11

    gdd_values = []

    for t in df["atmospheric_temperature_daily_average"]:
        curr_gdd = 0

        if t > baseline_temp:
            curr_gdd = t - baseline_temp

        gdd_values.append(gdd + curr_gdd)

        gdd = gdd + curr_gdd

    df["gdd"] = gdd_values

    return df

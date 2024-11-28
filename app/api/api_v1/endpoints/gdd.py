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

    baseline_temp = 11.0

    dates = df["date"].to_list()
    atdas = df["atmospheric_temperature_daily_average"].to_list()
    final_list_of_gdds = []
    global_temp_gdd = 0

    for c in range(len(atdas)):
        curr_gdd = 0

        if atdas[c] > baseline_temp:
            curr_gdd = atdas[c] - baseline_temp

        global_temp_gdd = global_temp_gdd + curr_gdd

        final_list_of_gdds.append((dates[c], global_temp_gdd))

    response = {
        "total_accumulated_gdd": final_list_of_gdds[-1][1],
        "gdds_accumulated_per_day": map(lambda x: (str(x[0]).split("T")[0].split(" ")[0], x[1]), final_list_of_gdds)
    }

    return response

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import crud
from api import deps
import datetime


from schemas import DatasetIds, list_path_param
from utils import fetch_parcel_by_id, fetch_parcel_lat_lon, fetch_weather_data, calculate_gdd_wd

router = APIRouter()

@router.get("/{model_ids}/gdd/", dependencies=[Depends(deps.is_using_gatekeeper)])
def calculate_gdd_fc(
        parcel_id: str,
        from_date: datetime.date,
        to_date: datetime.date,
        access_token: str = Depends(deps.get_jwt),
        model_ids: DatasetIds = Depends(list_path_param),
        db: Session = Depends(deps.get_db)

):
    """
    Calculates and returns GDD values (uses resources located on fc)
    """

    if from_date > to_date:
        raise HTTPException(
            status_code=400,
            detail="from_date must be later than to_date, from_date: {} | to_date: {}".format(from_date, to_date)
        )

    parcel_fc = fetch_parcel_by_id(access_token=access_token, parcel_id=parcel_id)

    if not parcel_fc:
        raise HTTPException(
            status_code=400,
            detail="Parcel with ID:{} doesn't exist".format(parcel_id)
        )

    lat, lon = fetch_parcel_lat_lon(parcel_fc)

    # Now that we have a (lat,lon) pair, we can query the weather service for weather data
    weather_data = fetch_weather_data(
        latitude=lat, longitude=lon, access_token=access_token, start_date=from_date, end_date=to_date, variables=["temperature_2m_max"]
    )

    # Fetch the disease models from the DB
    disease_models_db = []
    for disease_id in model_ids.ids:
        disease_model_db = crud.disease.get(db=db, id=disease_id)
        if not disease_model_db:
            raise HTTPException(
                status_code=400,
                detail="Error, model with ID {} does not exist".format(disease_id)
            )

        disease_models_db.append(disease_model_db)

    calculation_results = calculate_gdd_wd(
        disease_models=disease_models_db,
        weather_data=weather_data
    )

    return calculation_results

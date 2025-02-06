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

    pass
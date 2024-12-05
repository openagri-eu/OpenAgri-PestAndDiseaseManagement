from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from api import deps

import crud
from models import User
from schemas import PestModels, CreatePestModel, PestModelDB

router = APIRouter()


@router.get("/", response_model=PestModels)
def get_pest_models(
        db: Session = Depends(deps.get_db),
        user: User = Depends(deps.get_current_user)
):
    """
    Returns all pest models
    """

    pest_models_db = crud.pest_model.get_all(db=db)

    return PestModels(pests=pest_models_db)

@router.post("/", response_model=PestModelDB)
def create_pest_model(
        pm: CreatePestModel,
        db: Session = Depends(deps.get_db),
        user: User = Depends(deps.get_current_user)
):
    """
    Create a base pest model
    """

    return crud.pest_model.create(db=db, obj_in=pm)

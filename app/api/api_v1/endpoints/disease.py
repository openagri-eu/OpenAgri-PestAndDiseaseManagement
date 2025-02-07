from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import crud
from api import deps
from models import User
from schemas import ListDisease, InputDisease, DiseaseDB

router = APIRouter()

@router.get("/", response_model=ListDisease)
def get_all_diseases(
        db: Session = Depends(deps.get_db),
        user: User = Depends(deps.get_current_user)
) -> ListDisease:
    """
    Returns a list of all diseases
    """

    response = crud.disease.get_all(db=db)

    return ListDisease(diseases=response)

@router.post("/", response_model=DiseaseDB)
def create_disease(
        input_obj: InputDisease,
        db: Session = Depends(deps.get_db),
        user: User = Depends(deps.get_current_user)
) -> DiseaseDB:
    """
    Create a new disease
    """

    if len(input_obj.gdd_points) == 0:
        raise HTTPException(
            status_code=400,
            detail="Error, there needs to be at least one gdd point in the list"
        )

    pass
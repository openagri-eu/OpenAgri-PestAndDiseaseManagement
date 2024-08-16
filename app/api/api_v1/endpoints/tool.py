from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api import deps
from schemas import RiskIndexSchema, Message

router = APIRouter()

@router.get("/calculate-risk-index/", response_model=Message)
def calculate_risk_index(
    risk_index_obj: RiskIndexSchema,
    db: Session = Depends(deps.get_db)
):
    """
    Return risk index associated data for frontend to render.
    """

    return Message(message="a")
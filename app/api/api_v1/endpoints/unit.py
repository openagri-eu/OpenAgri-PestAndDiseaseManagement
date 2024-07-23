from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api import deps
from schemas import Operators, Units, UnitCreate, Message, UnitDelete
from crud import unit, operator

router = APIRouter()


@router.post("/", response_model=Message)
def create_unit(
        unit_in: UnitCreate,
        db: Session = Depends(deps.get_db)
):
    """
    Creates a user defined unit
    """

    unit_db = unit.create(db=db, obj_in=unit_in)

    return Message(message="Successfully created!")


@router.get("/", response_model=Units)
def get_units(
        db: Session = Depends(deps.get_db)
):
    """
    Returns a list of symbols that are currently available in the system
    """

    units_db = unit.get_all(db=db)

    return Units(units=units_db)


@router.delete("/")
def delete_unit(
        unit_id: UnitDelete,
        db: Session = Depends(deps.get_db)
):
    """
    Delete a unit
    """

    removed_unit = unit.remove(db=db, id=unit_id.id)

    if removed_unit:
        return Message(message="Successfully removed unit!")

    return Message(message="Unit doesn't exist.")


@router.get("/operators/", response_model=Operators)
def get_operators(
        db: Session = Depends(deps.get_db)
) -> Operators:
    """
    Returns all operators available for use (<, >=, ==, etc...)
    """

    operators_db = operator.get_all(db=db)

    return Operators(operators=operators_db)

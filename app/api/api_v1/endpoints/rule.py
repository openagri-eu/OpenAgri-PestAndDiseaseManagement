from fastapi import APIRouter, HTTPException, Depends
from requests import Session

import crud
from api import deps
from schemas import Message
from schemas.rule import Rule, Rules

router = APIRouter()


@router.post("/", response_model=Rule)
def create_rule(
        rule: Rule,
        db: Session = Depends(deps.get_db)
):
    """
    Create a rule such as: temperature > 50 AND air_pressure < 20 AND humidity < 50
    """

    if len(rule.conditions) == 0:
        raise HTTPException(
            status_code=400,
            detail="Can't create rule with no conditions."
        )

    # Check whether there are two conditions with the same unit
    cond_times = {}
    for cond in rule.conditions:
        if cond_times[cond.unit_id] is None:
            cond_times[cond.unit_id] = [cond.unit_id]
        cond_times[cond.unit_id].append(cond.unit_id)

    for cond in cond_times.values():
        if len(cond) > 1:
            raise HTTPException(
                status_code=400,
                detail="Can't have same unit multiple times in one rule."
            )

    crud.rule.create(db=db, obj_in=rule)

    for cond in rule.conditions:
        crud.condition.create(db=db, obj_in=cond)

    return rule



@router.get("/", response_model=Rules)
def get_all_rules(
        db: Session = Depends(deps.get_db)
):
    """
    Returns all stored rules.
    """

    return Rules(rules=current_rules)


@router.delete("/", response_model=Message)
def delete_rule(
        db: Session = Depends(deps.get_db)
) -> Message:
    """
    Delete a rule
    """



# This API regards the live data rules, not the dataset rules (for risk index definition)
# @router.post("/enable/", response_model=Rule)
# def enable_disable_rule(
#         db: Session = Depends(deps.get_db)
# ) -> Rule:
#     """
#     Enable or disable a rule
#     """

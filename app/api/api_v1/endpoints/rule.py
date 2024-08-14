from fastapi import APIRouter, HTTPException, Depends
from requests import Session

import crud
from api import deps
from schemas import Message, Rule, Rules

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
        if not cond.unit_id in cond_times:
            cond_times[cond.unit_id] = [cond.unit_id]
            continue
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

    rules_db = crud.rule.get_all(db=db)

    return Rules(rules=rules_db)


@router.delete("/{rule_id}", response_model=Message)
def delete_rule(
        rule_id: int,
        db: Session = Depends(deps.get_db)
) -> Message:
    """
    Delete a rule
    """

    rule_db = crud.rule.get(db=db, id=rule_id)

    if not rule_db:
        raise HTTPException(
            status_code=400,
            detail="Can't delete rule that doesn't exist."
        )

    crud.rule.remove(db=db, id=rule_id)

    return Message(message="Successfully deleted the rule!")

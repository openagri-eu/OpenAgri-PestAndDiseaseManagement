from fastapi import APIRouter, HTTPException, Depends
from requests import Session

from api import deps
from schemas import Message
from schemas.rule import Rule, Rules

router = APIRouter()


@router.post("/", response_model=Rule)
def create_rule(
    rule: Rule
):
    """
    Create a rule such as: temperature > 50 AND air_pressure < 20 AND 20 <= humidity < 50
    For a list of allowed values, call the get_symbols API.

    If the another_compared_value value is passed, it means that the condition is defined as:
    compared_value < x < another_compared_value. (The sequence of values is not important)
    The two boolean fields convey whether the min or max values should be included in
    the rule i.e. < or <= for both values.

    For a description of the condition class, look below the API definitions on this page, where the class definitions
    are located.
    """

    mf_allowed = {"temperature", "humidity", "air_pressure"}
    o_allowed = {">", "<", "==", ">=", "<="}

    if len(rule.conditions) == 0:
        raise HTTPException(
            status_code=400,
            detail="Can't create rule with no conditions."
        )

    for cond in rule.conditions:
        if cond.measurement_field not in mf_allowed:
            raise HTTPException(
                status_code=400,
                detail="{} is not allowed. (allow list:{})".format(cond.measurement_field, mf_allowed)
            )
        if cond.operation not in o_allowed:
            raise HTTPException(
                status_code=400,
                detail="{} is not allowed. (allow list:{})".format(cond.operation, o_allowed)
            )

    current_rules.append(rule)
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


@router.post("/enable/", response_model=Rule)
def enable_disable_rule(
        db: Session = Depends(deps.get_db)
) -> Rule:
    """
    Enable or disable a rule
    """

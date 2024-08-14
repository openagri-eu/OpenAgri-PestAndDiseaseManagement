import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class Condition(BaseModel):
    unit_id: int
    operator_id: int
    value: int


class CreateCondition(Condition):
    pass


class Rule(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    description: Optional[str] = None

    from_time: datetime.time
    to_time: datetime.time

    conditions: List[Condition] = []


class CreateRule(Rule):
    pass


class Rules(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    rules: List[Rule] = []

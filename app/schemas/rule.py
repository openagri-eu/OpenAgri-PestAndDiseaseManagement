import datetime
from typing import List, Optional

from pydantic import BaseModel


class Condition(BaseModel):
    unit_id: int
    operation_id: int
    value: int


class CreateCondition(Condition):
    pass


class Rule(BaseModel):
    name: str
    description: Optional[str] = None

    from_time: datetime.time
    to_time: datetime.time

    conditions: List[Condition] = []


class CreateRule(Rule):
    pass


class Rules(BaseModel):
    rules: List[Rule] = []

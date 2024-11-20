import datetime
from typing import List, Optional, Literal

from pydantic import BaseModel, ConfigDict, UUID4


class Condition(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    unit_id: int
    operator_id: int
    value: float


class CreateCondition(BaseModel):
    rule_id: int
    unit_id: int
    operator_id: int
    value: float


class CreateRule(BaseModel):
    name: str
    description: Optional[str] = None
    probability_value: Literal["low", "moderate", "high"]
    pest_model_id: UUID4


class CreateRuleWithConditions(CreateRule):
    conditions: List[Condition] = []


class UpdateRule(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

    from_time: Optional[datetime.time] = None
    to_time: Optional[datetime.time] = None

    conditions : Optional[List[Condition]] = []


class RuleDB(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: Optional[str]

    conditions: List[Condition]


class RulesDB(BaseModel):
    rules: List[RuleDB] = []



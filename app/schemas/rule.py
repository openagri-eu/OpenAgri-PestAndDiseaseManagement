from typing import List, Optional

from pydantic import BaseModel


class Condition(BaseModel):
    measurement_field: str
    operation: str # >, <, >=, <=, !=
    compared_value: int
    another_compared_value: Optional[int] = None
    include_min_value: Optional[bool] = False
    include_max_value: Optional[bool] = False


class Rule(BaseModel):
    description: Optional[str] = None
    conditions: List[Condition] = []


class Rules(BaseModel):
    rules: List[Rule] = []

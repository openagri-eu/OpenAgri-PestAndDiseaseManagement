from typing import List

from pydantic import BaseModel, ConfigDict


class OperatorAll(BaseModel):
    operator: str


class OperatorSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    operator: str


class Operators(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    operators: List[OperatorSchema]

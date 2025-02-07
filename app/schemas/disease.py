from typing import Optional, List

from pydantic import BaseModel, ConfigDict
from pydantic import UUID4


class CreateDisease(BaseModel):
    name: str
    eppo_code: str
    description: Optional[str]
    gdd_points: str


class DiseaseDB(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID4
    name: str
    eppo_code: str
    description: Optional[str]
    gdd_points: str

class ListDisease(BaseModel):
    diseases: List[DiseaseDB]

class InputDisease(BaseModel):
    name: str
    eppo_code: str
    description: Optional[str]
    gdd_points: List[int]
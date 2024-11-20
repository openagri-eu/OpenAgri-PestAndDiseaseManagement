from typing import Optional, List

from pydantic import BaseModel, ConfigDict, UUID4


class CreatePestModel(BaseModel):
    name: str
    description: Optional[str]
    geo_areas_of_application: Optional[str]
    cultivations: Optional[List[str]]

class UpdatePestModel(BaseModel):
    name: Optional[str]
    description: Optional[str]
    geo_areas_of_application: Optional[str]

class PestModelDB(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID4
    name: str
    description: Optional[str]
    geo_areas_of_application: Optional[str]

class PestModels(BaseModel):
    pests: List[PestModelDB]
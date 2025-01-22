from fastapi import Path, HTTPException
from pydantic import BaseModel, Field, ValidationError, UUID4


class RiskIndexWeather(BaseModel):
    context: str = Field(alias="@context", default=None)
    a: str


class DatasetIds(BaseModel):
    ids: list[UUID4]

def list_path_param(model_ids: str = Path()):
    try:
        ids = DatasetIds(ids=[x for x in model_ids.split(",")])
    except ValidationError:
        raise HTTPException(400, "Dataset IDs must be valid uuids.")

    return ids
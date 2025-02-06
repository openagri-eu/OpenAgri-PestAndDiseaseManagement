from typing import List

from pydantic import BaseModel, ConfigDict


class ParcelBase(BaseModel):
    name: str

class CreateParcel(ParcelBase):
    latitude: float
    longitude: float

class ParcelWKT(ParcelBase):
    wkt_polygon: str

class ParcelDB(CreateParcel):
    id: int

    model_config = ConfigDict(from_attributes=True)

class Parcels(BaseModel):
    elements: List[ParcelDB]
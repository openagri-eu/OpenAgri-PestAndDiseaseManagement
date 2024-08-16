from typing import Optional

from pydantic import BaseModel, ConfigDict
import datetime


class CreateData(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    date: datetime.date
    time: datetime.time
    nuts3: str
    nuts2: str
    temperature_air: int
    relative_humidity: int
    precipitation: int
    wind_speed: int
    wind_direction: int
    wind_gust: int
    atmospheric_pressure: int
    relative_humidity_canopy: int
    temperature_canopy: int
    solar_irradiance_copernicus: int

class UpdateData(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    nuts3: Optional[str] = None
    nuts2: Optional[str] = None
    temperature_air: Optional[int] = None
    relative_humidity: Optional[int] = None
    precipitation: Optional[int] = None
    wind_speed: Optional[int] = None
    wind_direction: Optional[int] = None
    wind_gust: Optional[int] = None
    atmospheric_pressure: Optional[int] = None
    relative_humidity_canopy: Optional[int] = None
    temperature_canopy: Optional[int] = None
    solar_irradiance_copernicus: Optional[int] = None

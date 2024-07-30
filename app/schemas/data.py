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

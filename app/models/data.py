from sqlalchemy import Column, Integer, Date, Time, String

from db.base_class import Base


class Data(Base):
    __tablename__ = 'data'
    id = Column(Integer, primary_key=True, unique=True, nullable=False)
    date = Column(Date, nullable=True)
    time = Column(Time, nullable=True)
    nuts3 = Column(String, nullable=True)
    nuts2 = Column(String, nullable=True)
    temperature_air = Column(Integer, nullable=True, info={"unit_of_measure": "celsius"})
    relative_humidity = Column(Integer, nullable=True, info={"unit_of_measure": "percentage"})
    precipitation = Column(Integer, nullable=True, info={"unit_of_measure": "mm"})
    wind_speed = Column(Integer, nullable=True, info={"unit_of_measure": "km/h"})
    wind_direction = Column(Integer, nullable=True)
    wind_gust = Column(Integer, nullable=True, info={"unit_of_measure": "km/h"})
    atmospheric_pressure = Column(Integer, nullable=True, info={"unit_of_measure": "mbar"})
    relative_humidity_canopy = Column(Integer, nullable=True, info={"unit_of_measure": "percentage"})
    temperature_canopy = Column(Integer, nullable=True, info={"unit_of_measure": "celsius"})
    solar_irradiance_copernicus = Column(Integer, nullable=True, info={"unit_of_measure": "W/m2"})

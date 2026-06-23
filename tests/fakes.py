from __future__ import annotations

from dataclasses import dataclass
from datetime import date, time


@dataclass
class FakeCrop:
    name: str


@dataclass
class FakeThreatModel:
    scientific_name: str
    common_name: str
    crop: FakeCrop
    definition: dict
    threat_type: str | None = None


@dataclass
class FakeDataRow:
    date: date
    time: time
    atmospheric_temperature: float | None = None
    atmospheric_relative_humidity: float | None = None
    precipitation: float | None = None
    average_wind_speed: float | None = None
    atmospheric_pressure: float | None = None


@dataclass
class FakeParcel:
    latitude: float
    longitude: float

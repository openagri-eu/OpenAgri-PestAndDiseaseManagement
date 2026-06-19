from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time
from uuid import UUID

import numpy as np
import pandas as pd

from agstack_pnd.foundation.types import (
    DailyScore,
    ModelResult,
    RiskLevel,
    ThreatDefinition,
    ThreatType,
)
from agstack_pnd.models.disease.fuzzy_mamdani import FuzzyMamdaniRisk

from utils.agstack_adapter import (
    daily_df_to_wdf,
    hourly_rows_to_wdf,
    result_to_rows,
    threatmodel_to_definition,
)


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


def _fungal_tm(**overrides) -> FakeThreatModel:
    definition = {
        "bio_params": {
            "t_base": 5.0,
            "t_optimal_min": 15.0,
            "t_optimal_max": 25.0,
            "pheno_frac_lo": 0.10,
            "pheno_frac_hi": 0.80,
            "pheno_frac_ref_gdd5": 2200.0,  # PND's abbreviated spelling
        },
        "fuzzy_rules": [
            {
                "hum_lo": 80,
                "hum_hi": 100,
                "temp_lo": 10,
                "temp_hi": 25,
                "rain_min": 1.0,
                "risk_level": "high",
                "type": "fungal",
            },
            {
                "hum_lo": 0,
                "hum_hi": 70,
                "temp_lo": 0,
                "temp_hi": 35,
                "rain_min": 0.0,
                "risk_level": "low",
                "type": "fungal",
            },
        ],
    }
    base = dict(
        scientific_name="Venturia inaequalis",
        common_name="Apple scab",
        crop=FakeCrop("apple"),
        definition=definition,
    )
    base.update(overrides)
    return FakeThreatModel(**base)


def _daily_df(n: int = 14) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "date": pd.date_range("2026-05-01", periods=n, freq="D"),
            "temp_max": np.full(n, 24.0),
            "temp_min": np.full(n, 14.0),
            "humidity": np.full(n, 88.0),
            "rainfall": np.full(n, 3.0),
        }
    )


class TestThreatModelToDefinition:
    def test_returns_threat_definition_with_core_fields(self):
        td = threatmodel_to_definition(_fungal_tm())
        assert isinstance(td, ThreatDefinition)
        assert td.scientific_name == "Venturia inaequalis"
        assert td.common_name == "Apple scab"
        assert td.crop == "apple"
        assert len(td.fuzzy_rules) == 2

    def test_pheno_frac_ref_gdd5_is_renamed(self):
        td = threatmodel_to_definition(_fungal_tm())
        assert td.bio_params.pheno_fraction_ref_gdd5 == 2200.0
        assert not hasattr(td.bio_params, "pheno_frac_ref_gdd5")

    def test_rule_type_field_is_dropped(self):
        td = threatmodel_to_definition(_fungal_tm())
        for rule in td.fuzzy_rules:
            assert not hasattr(rule, "type")

    def test_threat_type_inferred_fungus(self):
        assert threatmodel_to_definition(_fungal_tm()).threat_type is ThreatType.FUNGUS

    def test_threat_type_inferred_insect(self):
        tm = _fungal_tm(
            definition={
                "bio_params": {"t_base": 10.0},
                "fuzzy_rules": [
                    {
                        "hum_lo": 0,
                        "hum_hi": 100,
                        "temp_lo": 15,
                        "temp_hi": 30,
                        "rain_min": 0.0,
                        "risk_level": "high",
                        "type": "insect",
                    }
                ],
            }
        )
        assert threatmodel_to_definition(tm).threat_type is ThreatType.INSECT

    def test_explicit_threat_type_column_wins(self):
        tm = _fungal_tm(threat_type="bacterium")
        assert threatmodel_to_definition(tm).threat_type is ThreatType.BACTERIUM

    def test_default_threat_type_is_fungus(self):
        tm = _fungal_tm(
            definition={
                "bio_params": {"t_base": 5.0},
                "fuzzy_rules": [
                    {
                        "hum_lo": 0,
                        "hum_hi": 100,
                        "temp_lo": 0,
                        "temp_hi": 30,
                        "rain_min": 0.0,
                        "risk_level": "low",
                    }
                ],
            }
        )
        assert threatmodel_to_definition(tm).threat_type is ThreatType.FUNGUS

    def test_all_null_bio_params_round_trips(self):
        tm = _fungal_tm(
            definition={
                "bio_params": {
                    "t_base": None,
                    "pheno_hi": None,
                    "pheno_lo": None,
                    "min_streak": None,
                    "t_lethal_max": None,
                    "t_lethal_min": None,
                    "pheno_frac_hi": None,
                    "pheno_frac_lo": None,
                    "t_optimal_max": None,
                    "t_optimal_min": None,
                    "pheno_frac_ref_gdd5": None,
                    "min_wetness_hours_high": None,
                    "min_wetness_hours_critical": None,
                },
                "fuzzy_rules": [
                    {
                        "hum_lo": 0,
                        "hum_hi": 100,
                        "temp_lo": -999,
                        "temp_hi": 999,
                        "rain_min": 0,
                        "risk_level": "low",
                        "type": "ww",
                    }
                ],
            }
        )
        td = threatmodel_to_definition(tm)
        assert isinstance(td, ThreatDefinition)

    def test_bio_params_none_round_trips(self):
        tm = _fungal_tm(
            definition={
                "bio_params": None,
                "fuzzy_rules": [
                    {
                        "hum_lo": 70,
                        "hum_hi": 100,
                        "temp_lo": 5,
                        "temp_hi": 30,
                        "rain_min": 1.0,
                        "risk_level": "moderate",
                    }
                ],
            }
        )
        assert isinstance(threatmodel_to_definition(tm), ThreatDefinition)

    def test_missing_rule_bounds_get_pnd_defaults(self):
        tm = _fungal_tm(
            definition={
                "bio_params": {"t_base": 5.0},
                "fuzzy_rules": [{"risk_level": "moderate"}],  # bounds omitted
            }
        )
        rule = threatmodel_to_definition(tm).fuzzy_rules[0]
        assert (rule.hum_lo, rule.hum_hi) == (0.0, 100.0)
        assert (rule.temp_lo, rule.temp_hi) == (-999.0, 999.0)
        assert rule.rain_min == 0.0

    def test_null_risk_level_falls_back_to_low(self):
        tm = _fungal_tm(
            definition={
                "bio_params": {"t_base": 5.0},
                "fuzzy_rules": [
                    {
                        "hum_lo": 0,
                        "hum_hi": 100,
                        "temp_lo": -999,
                        "temp_hi": 999,
                        "rain_min": 0,
                        "risk_level": None,
                    }
                ],
            }
        )
        assert threatmodel_to_definition(tm).fuzzy_rules[0].risk_level is RiskLevel.LOW


class TestDailyDfToWdf:
    def test_length_and_fields(self):
        wdf = daily_df_to_wdf(_daily_df(5))
        assert wdf.length == 5
        assert set(wdf.field_names()) == {
            "air_temperature",
            "relative_humidity",
            "precipitation",
        }

    def test_air_temperature_is_midpoint(self):
        wdf = daily_df_to_wdf(_daily_df(3))
        assert np.allclose(wdf["air_temperature"], 19.0)  # (24 + 14) / 2

    def test_timestamps_span_the_days(self):
        wdf = daily_df_to_wdf(_daily_df(7))
        days = wdf.timestamps.astype("datetime64[D]")
        assert str(days[0]) == "2026-05-01"
        assert len(np.unique(days)) == 7


class TestHourlyRowsToWdf:
    def _rows(self, n: int = 3) -> list[FakeDataRow]:
        return [
            FakeDataRow(
                date=date(2026, 5, 1),
                time=time(h, 0),
                atmospheric_temperature=18.0 + h,
                atmospheric_relative_humidity=80.0,
                precipitation=0.5,
                average_wind_speed=10.0,
            )
            for h in range(n)
        ]

    def test_renames_to_canonical_fields(self):
        wdf = hourly_rows_to_wdf(self._rows(3))
        assert wdf.length == 3
        assert "air_temperature" in wdf.field_names()
        assert "relative_humidity" in wdf.field_names()
        assert "wind_speed" in wdf.field_names()
        assert np.allclose(wdf["air_temperature"], [18.0, 19.0, 20.0])

    def test_all_null_field_is_omitted(self):
        rows = self._rows(2)
        wdf = hourly_rows_to_wdf(rows)
        assert "atmospheric_pressure" not in wdf.field_names()


class TestResultToRows:
    def _result(self) -> ModelResult:
        return ModelResult(
            model_uuid=UUID("a1b2c3d4-0004-4000-8000-000000000001"),
            model_name="fuzzy_mamdani_risk",
            computed_at=datetime(2026, 5, 2, 0, 0),
            start_date=date(2026, 5, 1),
            end_date=date(2026, 5, 2),
            daily_scores=[
                DailyScore(
                    date=date(2026, 5, 1), value=72.5, risk_level=RiskLevel.HIGH
                ),
                DailyScore(date=date(2026, 5, 2), value=10.0, risk_level=RiskLevel.LOW),
            ],
        )

    def test_columns_and_titlecased_class(self):
        rows = result_to_rows(self._result(), _fungal_tm())
        assert len(rows) == 2
        assert set(rows[0]) == {
            "date",
            "scientific_name",
            "common_name",
            "risk_score",
            "risk_class",
            "detail",
        }
        assert rows[0]["risk_class"] == "High"
        assert rows[1]["risk_class"] == "Low"
        assert rows[0]["risk_score"] == 72.5
        assert rows[0]["scientific_name"] == "Venturia inaequalis"

    def test_missing_risk_level_defaults_low(self):
        result = self._result()
        result.daily_scores.append(DailyScore(date=date(2026, 5, 3), value=0.0))
        assert result_to_rows(result, _fungal_tm())[-1]["risk_class"] == "Low"


class TestEngineConsumesAdapterOutput:
    def test_fuzzy_engine_runs_on_adapter_output(self):
        tm = _fungal_tm()
        wdf = daily_df_to_wdf(_daily_df(14))
        threat = threatmodel_to_definition(tm)

        result = FuzzyMamdaniRisk().calculate(weather_data=wdf, threat=threat)

        assert len(result.daily_scores) == 14
        assert all(0.0 <= s.value <= 100.0 for s in result.daily_scores)

        rows = result_to_rows(result, tm)
        assert len(rows) == 14
        assert all(
            set(r)
            == {
                "date",
                "scientific_name",
                "common_name",
                "risk_score",
                "risk_class",
                "detail",
            }
            for r in rows
        )

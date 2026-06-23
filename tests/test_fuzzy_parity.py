from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from core.config import settings
from utils.fuzzy_risk import calculate_fuzzy_risk


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


def _daily(n: int = 30) -> pd.DataFrame:
    t = np.arange(n)
    humidity = np.clip(70 + 25 * np.sin(t / 2.0 + 1), 0, 100)
    return pd.DataFrame(
        {
            "date": pd.date_range("2026-04-01", periods=n, freq="D"),
            "temp_max": 18 + 6 * np.sin(t / 3.0),
            "temp_min": 8 + 5 * np.sin(t / 3.0),
            "humidity": humidity,
            "rainfall": np.clip(5 * np.sin(t / 1.5), 0, None),
        }
    )


def _grape_downy() -> FakeThreatModel:
    return FakeThreatModel(
        scientific_name="Plasmopara viticola",
        common_name="Downy mildew",
        crop=FakeCrop("grape"),
        definition={
            "bio_params": {
                "t_base": 10.0,
                "t_lethal_min": -3.0,
                "t_lethal_max": 38.0,
                "t_optimal_min": 18.0,
                "t_optimal_max": 25.0,
                "min_streak": 3,
                "min_wetness_hours_critical": 16.0,
                "min_wetness_hours_high": 10.0,
                "pheno_frac_lo": 0.1,
                "pheno_frac_hi": 0.75,
                "pheno_frac_ref_gdd5": 2200.0,
            },
            "fuzzy_rules": [
                {
                    "hum_lo": 90,
                    "hum_hi": 100,
                    "temp_lo": 18,
                    "temp_hi": 25,
                    "rain_min": 10.0,
                    "risk_level": "critical",
                    "type": "fungal",
                },
                {
                    "hum_lo": 80,
                    "hum_hi": 100,
                    "temp_lo": 13,
                    "temp_hi": 30,
                    "rain_min": 5.0,
                    "risk_level": "high",
                    "type": "fungal",
                },
                {
                    "hum_lo": 65,
                    "hum_hi": 90,
                    "temp_lo": 10,
                    "temp_hi": 32,
                    "rain_min": 1.0,
                    "risk_level": "moderate",
                    "type": "fungal",
                },
                {
                    "hum_lo": 0,
                    "hum_hi": 65,
                    "temp_lo": 0,
                    "temp_hi": 38,
                    "rain_min": 0.0,
                    "risk_level": "low",
                    "type": "fungal",
                },
            ],
        },
    )


def _run(df, tms, *, use_agstack: bool, monkeypatch) -> pd.DataFrame:
    monkeypatch.setattr(settings, "USE_AGSTACK_PND", use_agstack)
    out = calculate_fuzzy_risk(df, tms)
    return out.sort_values("date").reset_index(drop=True)


def test_parity_report(monkeypatch):
    df = _daily()
    tm = _grape_downy()

    inline = _run(df, [tm], use_agstack=False, monkeypatch=monkeypatch)
    pkg = _run(df, [tm], use_agstack=True, monkeypatch=monkeypatch)

    # structural parity — must hold (numeric/class parity is NOT yet asserted;
    # see docs/agstack-pnd-alignment.md §8 for the measured divergences)
    assert len(inline) == len(pkg) == len(df)
    assert list(inline.columns) == list(pkg.columns)
    assert inline["risk_score"].astype(float).between(0, 100).all()
    assert pkg["risk_score"].astype(float).between(0, 100).all()

    delta = (inline["risk_score"].astype(float) - pkg["risk_score"].astype(float)).abs()
    class_agree = (inline["risk_class"] == pkg["risk_class"]).mean()

    print(
        f"\n[parity] rows={len(inline)} "
        f"max|Δscore|={delta.max():.2f} mean|Δscore|={delta.mean():.2f} "
        f"class_agree={class_agree:.0%}"
    )
    print(
        pd.DataFrame(
            {
                "date": inline["date"].dt.date,
                "inline": inline["risk_score"].round(1),
                "pkg": pkg["risk_score"].round(1),
                "in_cls": inline["risk_class"],
                "pkg_cls": pkg["risk_class"],
            }
        ).to_string(index=False)
    )

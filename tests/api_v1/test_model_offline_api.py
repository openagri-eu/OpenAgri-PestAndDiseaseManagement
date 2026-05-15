"""
Tests for /{model_ids}/risk-index/forecast/weather-service/offline/

Strategy: mount the model router in an isolated FastAPI app, override get_db
and is_offline_deployment, and patch the weather service call and risk calculation
so tests run without a real DB or network.
"""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock

import pandas as pd
import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.api_v1.endpoints.model import router as model_router
from api import deps
from core import settings

ENDPOINT_MODULE = "app.api.api_v1.endpoints.model"

PEST_MODEL_ID = str(uuid.uuid4())
OFFLINE_URL = f"/{PEST_MODEL_ID}/risk-index/forecast/weather-service/offline/"

SAMPLE_WEATHER_DF = pd.DataFrame([{
    "timestamp": pd.Timestamp("2024-06-01T12:00:00"),
    "temperature": 22.0,
    "humidity": 75.0,
    "precipitation": 1.5,
}])

SAMPLE_RESULT = {
    "@context": {},
    "@graph": [{"@id": "urn:openagri:pestInfectationRisk:abc", "@type": ["ObservationCollection"]}],
}


# ─── fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_db_session() -> MagicMock:
    return MagicMock(spec=Session)


def _make_pest_model() -> MagicMock:
    pm = MagicMock()
    pm.id = PEST_MODEL_ID
    pm.name = "TestPest"
    return pm


@pytest.fixture
def client(mock_db_session: MagicMock) -> TestClient:
    app = FastAPI()
    app.include_router(model_router)
    app.dependency_overrides[deps.get_db] = lambda: mock_db_session
    app.dependency_overrides[deps.is_offline_deployment] = lambda: None
    with TestClient(app) as c:
        yield c


# ─── tests ───────────────────────────────────────────────────────────────────

class TestOfflineRiskIndexForecast:

    def test_happy_path(self, client: TestClient, mock_db_session: MagicMock, mocker):
        mocker.patch(f"{ENDPOINT_MODULE}.crud.pest_model.get", return_value=_make_pest_model())
        mocker.patch(
            f"{ENDPOINT_MODULE}.fetch_weather_service_forecast_weather_data",
            return_value=SAMPLE_WEATHER_DF,
        )
        mocker.patch(
            f"{ENDPOINT_MODULE}.calculate_risk_index_forecast_wd",
            return_value=SAMPLE_RESULT,
        )

        r = client.get(OFFLINE_URL, params={"latitude": 45.0, "longitude": 14.0})

        assert r.status_code == 200
        body = r.json()
        assert "@context" in body
        assert "@graph" in body

    def test_json_format_not_implemented(self, client: TestClient, mocker):
        mocker.patch(f"{ENDPOINT_MODULE}.crud.pest_model.get", return_value=_make_pest_model())
        mocker.patch(
            f"{ENDPOINT_MODULE}.fetch_weather_service_forecast_weather_data",
            return_value=SAMPLE_WEATHER_DF,
        )

        r = client.get(OFFLINE_URL, params={"latitude": 45.0, "longitude": 14.0, "formatting": "JSON"})

        assert r.status_code == 501

    def test_blocked_when_flag_false(self, mock_db_session: MagicMock, monkeypatch):
        monkeypatch.setattr(settings, "OFFLINE_DEPLOYMENT", False)

        app = FastAPI()
        app.include_router(model_router)
        app.dependency_overrides[deps.get_db] = lambda: mock_db_session

        with TestClient(app) as c:
            r = c.get(OFFLINE_URL, params={"latitude": 45.0, "longitude": 14.0})

        assert r.status_code == 403
        assert "offline deployment" in r.json()["detail"].lower()

    def test_invalid_pest_model_id(self, client: TestClient, mock_db_session: MagicMock, mocker):
        mocker.patch(f"{ENDPOINT_MODULE}.crud.pest_model.get", return_value=None)
        mocker.patch(
            f"{ENDPOINT_MODULE}.fetch_weather_service_forecast_weather_data",
            return_value=SAMPLE_WEATHER_DF,
        )

        r = client.get(OFFLINE_URL, params={"latitude": 45.0, "longitude": 14.0})

        assert r.status_code == 400
        assert "does not exist" in r.json()["detail"]

    def test_weather_service_failure(self, client: TestClient, mocker):
        mocker.patch(
            f"{ENDPOINT_MODULE}.fetch_weather_service_forecast_weather_data",
            side_effect=HTTPException(status_code=400, detail="Error during proxy call via gk"),
        )

        r = client.get(OFFLINE_URL, params={"latitude": 45.0, "longitude": 14.0})

        assert r.status_code == 400
        assert "proxy call" in r.json()["detail"]

    def test_weather_fetch_called_without_token(self, client: TestClient, mocker):
        mock_fetch = mocker.patch(
            f"{ENDPOINT_MODULE}.fetch_weather_service_forecast_weather_data",
            return_value=SAMPLE_WEATHER_DF,
        )
        mocker.patch(f"{ENDPOINT_MODULE}.crud.pest_model.get", return_value=_make_pest_model())
        mocker.patch(
            f"{ENDPOINT_MODULE}.calculate_risk_index_forecast_wd",
            return_value=SAMPLE_RESULT,
        )

        client.get(OFFLINE_URL, params={"latitude": 45.0, "longitude": 14.0})

        mock_fetch.assert_called_once_with(latitude=45.0, longitude=14.0)


# ─── wdutils unit tests ───────────────────────────────────────────────────────

class TestFetchWeatherServiceForecastNoBearerToken:

    def test_no_token_omits_authorization_header(self, mocker):
        from utils.wdutils import fetch_weather_service_forecast_weather_data

        mock_get = mocker.patch("utils.wdutils.requests.get")
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = []
        mocker.patch("utils.wdutils.convert_weather_service_forecast_weather_data_to_dataframe", return_value=None)

        fetch_weather_service_forecast_weather_data(45.0, 14.0)

        headers_used = mock_get.call_args.kwargs["headers"]
        assert "Authorization" not in headers_used

    def test_with_token_includes_authorization_header(self, mocker):
        from utils.wdutils import fetch_weather_service_forecast_weather_data

        mock_get = mocker.patch("utils.wdutils.requests.get")
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = []
        mocker.patch("utils.wdutils.convert_weather_service_forecast_weather_data_to_dataframe", return_value=None)

        fetch_weather_service_forecast_weather_data(45.0, 14.0, access_token="mytoken")

        headers_used = mock_get.call_args.kwargs["headers"]
        assert headers_used["Authorization"] == "Bearer mytoken"

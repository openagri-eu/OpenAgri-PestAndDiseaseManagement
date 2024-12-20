import requests
from fastapi import APIRouter

from core import settings

from api.api_v1.endpoints import operator, pest_model, rule, tool, unit

def register_apis_to_gatekeeper():

    # Login
    at = requests.post(
        url=settings.GATEKEEPER_BASE_URL.unicode_string() + "api/login/",
        headers={"Content-Type": "application/json"},
        json={"username": "{}".format(settings.GATEKEEPER_USERNAME), "password": "{}".format(settings.GATEKEEPER_PASSWORD)}
    )

    temp = at.json()

    access = temp["access"]
    refresh = temp["refresh"]

    # Register APIs
    apis_to_register = APIRouter()
    apis_to_register.include_router(operator.router, prefix="/operator")
    apis_to_register.include_router(pest_model.router, prefix="/pest-model")
    apis_to_register.include_router(rule.router, prefix="/rule")
    apis_to_register.include_router(tool.router, prefix="/tool")
    apis_to_register.include_router(unit.router, prefix="/unit")

    print(apis_to_register.routes)
    print(apis_to_register.routes[0])

    print(apis_to_register.routes[0].path)
    print(apis_to_register.routes[0].methods)


    for api in apis_to_register.routes:

        requests.post(
            url=settings.GATEKEEPER_BASE_URL.unicode_string() + "api/register_service/",
            headers={"Content-Type": "application/json", "Authorization" : "Bearer {}".format(access)},
            json={
                "base_url": "{}:{}".format(settings.SERVICE_NAME, settings.SERVICE_PORT),
                "service_name": "pdm",
                "endpoint": "api/v1/" + api.path.strip("/"),
                "methods": list(api.methods)
            }
        )

    # Logout
    requests.post(
        url=settings.GATEKEEPER_BASE_URL.unicode_string() + "api/logout/",
        headers={"Content-Type": "application/json"},
        json={"refresh": refresh}
    )

    return

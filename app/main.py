from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from api.api_v1.api import api_router
from core.config import settings
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
import os

app = FastAPI(
    title="OpenAgri", openapi_url="/api/v1/openapi.json"
)

#app.add_middleware(HTTPSRedirectMiddleware)

# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix="/api/v1")

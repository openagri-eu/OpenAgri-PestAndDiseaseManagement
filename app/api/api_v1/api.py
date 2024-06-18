from fastapi import APIRouter
from .endpoints import login, user, data

api_router = APIRouter()
api_router.include_router(login.router, prefix="/login", tags=["login"])
api_router.include_router(user.router, prefix="/user", tags=["user"])
api_router.include_router(data.router, prefix="/data", tags=["data"])

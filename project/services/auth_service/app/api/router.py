from fastapi import APIRouter

from app.api.routes_auth import router as auth_router


def build_api_router() -> APIRouter:
    router = APIRouter()
    router.include_router(auth_router)
    return router

from fastapi import APIRouter

from app.config.settings import Settings
from app.domain.entities.monitor import Monitor


def build_monitor_router(settings: Settings) -> APIRouter:
    router = APIRouter(tags=["Monitor"])

    @router.get("/", response_model=Monitor, summary="Show the name and version of server")
    def health_check() -> Monitor:
        return Monitor(name=settings.name, version=settings.version)

    return router

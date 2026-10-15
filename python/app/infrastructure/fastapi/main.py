from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config.settings import Settings, get_settings
from app.infrastructure.container import Container, build_container
from app.interface.handlers.fastapi.dependencies import build_jwt_auth
from app.interface.handlers.fastapi.monitor import build_monitor_router
from app.interface.handlers.fastapi.response import APIError, error_response
from app.interface.handlers.fastapi.user import build_user_router

ROUTER_CHECK_ERROR = "middleware-001"
PARAMS_CHECK_ERROR = "middleware-003"


def create_app(settings: Settings | None = None, container: Container | None = None) -> FastAPI:
    settings = settings or get_settings()
    container = container or build_container(settings)

    app = FastAPI(title=settings.name, version=settings.version)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["GET", "POST", "HEAD", "PUT", "DELETE", "PATCH"],
        allow_headers=["Authorization", "Content-Type"],
        allow_credentials=False,
    )

    register_exception_handlers(app)

    jwt_auth = build_jwt_auth(container.user_usecase)
    app.include_router(build_monitor_router(settings), prefix="/api/v1")
    app.include_router(build_user_router(container.user_usecase, jwt_auth), prefix="/api/v1")

    return app


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(APIError)
    async def handle_api_error(_: Request, exc: APIError):
        return error_response(exc.status_code, exc.trace_id, exc.message)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(_: Request, exc: RequestValidationError):
        first = exc.errors()[0] if exc.errors() else {}
        field = ".".join(str(part) for part in first.get("loc", ()) if part != "body")
        message = f"{field}: {first.get('msg', 'invalid request')}" if field else "invalid request"
        return error_response(400, PARAMS_CHECK_ERROR, message)

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_error(_: Request, exc: StarletteHTTPException):
        if exc.status_code == 404:
            return error_response(404, ROUTER_CHECK_ERROR, "router not found")
        return error_response(exc.status_code, f"http-{exc.status_code}", str(exc.detail))


if __name__ == "__main__":
    import uvicorn

    _settings = get_settings()
    uvicorn.run(create_app(_settings), host=_settings.host, port=_settings.port)

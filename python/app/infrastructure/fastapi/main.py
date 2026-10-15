from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config.settings import Settings, get_settings
from app.interface.handlers.fastapi.monitor import build_monitor_router
from app.interface.handlers.fastapi.response import APIError, error_response

ROUTER_CHECK_ERROR = "middleware-001"
PARAMS_CHECK_ERROR = "middleware-003"


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()

    app = FastAPI(title=settings.name, version=settings.version)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["GET", "POST", "HEAD", "PUT", "DELETE", "PATCH"],
        allow_credentials=False,
    )

    register_exception_handlers(app)

    app.include_router(build_monitor_router(settings), prefix="/api/v1")

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

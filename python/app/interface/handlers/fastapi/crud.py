from collections.abc import Iterator
from contextlib import contextmanager
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, Request

from app.domain.entities.crud import DataListResponse, DataResponse
from app.domain.errors import InvalidFilterError, NotFoundError, PermissionDeniedError
from app.interface.handlers.fastapi.dependencies import AuthContext, JWTAuth
from app.interface.handlers.fastapi.response import APIError, ErrorResponse
from app.usecases.crud import DEFAULT_PAGE_SIZE, CRUDUsecase

CRUD_NOT_FOUND_ERROR = "crud-001"
CRUD_FILTER_ERROR = "crud-002"
CRUD_PERMISSION_ERROR = "crud-003"

PAGING_PARAMS = {"_page", "_pageSize"}

ERROR_RESPONSES = {status: {"model": ErrorResponse} for status in (400, 401, 403, 404)}


def build_crud_router(crud_usecase: CRUDUsecase, jwt_auth: JWTAuth) -> APIRouter:
    router = APIRouter(prefix="/data", tags=["CRUD"], responses=ERROR_RESPONSES)
    Auth = Annotated[AuthContext, Depends(jwt_auth)]

    # Registered before /{id} so "describe" is not captured as an id
    @router.get("/{entity_model_slug}/describe")
    def describe(entity_model_slug: str, auth: Auth) -> dict[str, Any]:
        with map_crud_errors():
            return crud_usecase.describe(auth.permission, entity_model_slug.strip())

    @router.get("/{entity_model_slug}")
    def retrieve_list(
        entity_model_slug: str,
        request: Request,
        auth: Auth,
        page: Annotated[int, Query(alias="_page")] = 1,
        page_size: Annotated[int, Query(alias="_pageSize")] = DEFAULT_PAGE_SIZE,
    ) -> DataListResponse:
        """Every query param other than _page/_pageSize is an exact-match filter."""
        filters = {
            key: value for key, value in request.query_params.items() if key not in PAGING_PARAMS
        }
        with map_crud_errors():
            return crud_usecase.retrieve_list(
                auth.permission, entity_model_slug.strip(), page, page_size, filters
            )

    @router.get("/{entity_model_slug}/{id}")
    def retrieve(entity_model_slug: str, id: str, auth: Auth) -> DataResponse:
        with map_crud_errors():
            return crud_usecase.retrieve(auth.permission, entity_model_slug.strip(), id)

    return router


@contextmanager
def map_crud_errors() -> Iterator[None]:
    """Turn CRUD domain errors into APIError responses."""
    try:
        yield
    except NotFoundError as exc:
        raise APIError(404, CRUD_NOT_FOUND_ERROR, str(exc)) from exc
    except InvalidFilterError as exc:
        raise APIError(400, CRUD_FILTER_ERROR, str(exc)) from exc
    except PermissionDeniedError as exc:
        raise APIError(403, CRUD_PERMISSION_ERROR, str(exc)) from exc

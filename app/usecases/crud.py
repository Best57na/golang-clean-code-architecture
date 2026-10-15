import math
from typing import Any

from app.domain.entities.crud import DataListResponse, DataResponse
from app.domain.entities.user import UserPermissionEntity
from app.domain.errors import NotFoundError, PermissionDeniedError
from app.domain.repositories.crud import ICRUDRepository, ICRUDRepositoryFactory

CRUD_PERMISSION = "admin"
DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 1000


class CRUDUsecase:
    def __init__(self, repository_factory: ICRUDRepositoryFactory):
        self._repositories = repository_factory

    def retrieve(
        self, permission: UserPermissionEntity | None, entity_model_slug: str, id: str
    ) -> DataResponse:
        repository = self._get_repository(permission, entity_model_slug)

        data = repository.get_one_by_id(id)
        if data is None:
            raise NotFoundError("data not found")

        return DataResponse(data=data, data_schema=repository.describe())

    def retrieve_list(
        self,
        permission: UserPermissionEntity | None,
        entity_model_slug: str,
        page: int,
        page_size: int,
        filters: dict[str, str],
    ) -> DataListResponse:
        repository = self._get_repository(permission, entity_model_slug)

        page = max(page, 1)
        if page_size < 1:
            page_size = DEFAULT_PAGE_SIZE
        page_size = min(page_size, MAX_PAGE_SIZE)

        rows, total = repository.get_list((page - 1) * page_size, page_size, filters)

        return DataListResponse(
            data=rows,
            page=page,
            page_size=page_size,
            total_page=math.ceil(total / page_size),
            total_data=total,
            data_schema=repository.describe(),
        )

    def describe(
        self, permission: UserPermissionEntity | None, entity_model_slug: str
    ) -> dict[str, Any]:
        return self._get_repository(permission, entity_model_slug).describe()

    def _get_repository(
        self, permission: UserPermissionEntity | None, entity_model_slug: str
    ) -> ICRUDRepository:
        # Generic data access exposes every registered table, so only admins may use it
        if permission is None or permission.permission != CRUD_PERMISSION:
            raise PermissionDeniedError("permission denied")

        repository = self._repositories.get(entity_model_slug)
        if repository is None:
            raise NotFoundError("entity model not found")
        return repository

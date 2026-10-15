import pytest

from app.domain.entities.user import UserPermissionEntity
from app.domain.errors import NotFoundError, PermissionDeniedError
from app.shared.crud.avro_schema import avro_type, generate_avro_schema
from app.shared.crud.converter import convert_name_to_crud_slug
from app.usecases.crud import CRUDUsecase

ADMIN = UserPermissionEntity(id=1, user_id=1, permission="admin")
SCHEMA = {"type": "record", "name": "books", "fields": []}


class FakeCRUDRepository:
    def __init__(self, rows):
        self.rows = rows
        self.last_call = None

    def get_one_by_id(self, id):
        return next((row for row in self.rows if str(row["id"]) == id), None)

    def get_list(self, offset, limit, filters):
        self.last_call = (offset, limit, filters)
        return self.rows[offset : offset + limit], len(self.rows)

    def describe(self):
        return SCHEMA


class FakeFactory:
    def __init__(self, repositories):
        self.repositories = repositories

    def get(self, slug):
        return self.repositories.get(slug)


@pytest.fixture
def books() -> FakeCRUDRepository:
    return FakeCRUDRepository([{"id": i, "title": f"book {i}"} for i in range(1, 26)])


@pytest.fixture
def usecase(books) -> CRUDUsecase:
    return CRUDUsecase(FakeFactory({"books": books}))


def test_retrieve_returns_row_and_schema(usecase):
    response = usecase.retrieve(ADMIN, "books", "3")

    assert response.data == {"id": 3, "title": "book 3"}
    assert response.data_schema == SCHEMA


def test_retrieve_missing_row_raises_not_found(usecase):
    with pytest.raises(NotFoundError, match="data not found"):
        usecase.retrieve(ADMIN, "books", "999")


def test_unknown_entity_model_raises_not_found(usecase):
    with pytest.raises(NotFoundError, match="entity model not found"):
        usecase.describe(ADMIN, "missing")


@pytest.mark.parametrize(
    "permission", [None, UserPermissionEntity(id=2, user_id=2, permission="viewer")]
)
def test_non_admin_is_denied(usecase, permission):
    with pytest.raises(PermissionDeniedError):
        usecase.retrieve_list(permission, "books", 1, 10, {})


def test_retrieve_list_paginates_with_total_count(usecase, books):
    response = usecase.retrieve_list(ADMIN, "books", 3, 10, {"title": "x"})

    assert books.last_call == (20, 10, {"title": "x"})
    assert [row["id"] for row in response.data] == [21, 22, 23, 24, 25]
    assert (response.total_data, response.total_page) == (25, 3)


@pytest.mark.parametrize(
    ("page", "page_size", "expected"),
    [(0, 0, (1, 10)), (-5, 5000, (1, 1000)), (2, 7, (2, 7))],
)
def test_retrieve_list_normalizes_paging(usecase, page, page_size, expected):
    response = usecase.retrieve_list(ADMIN, "books", page, page_size, {})

    assert (response.page, response.page_size) == expected


def test_convert_name_to_crud_slug():
    assert convert_name_to_crud_slug("user_tokens") == "user-tokens"
    assert convert_name_to_crud_slug("UserPermission") == "user-permission"


def test_generate_avro_schema_maps_python_types():
    from datetime import datetime

    schema = generate_avro_schema(
        "books",
        [("id", int), ("title", str), ("active", bool), ("at", datetime), ("note", str | None)],
    )

    assert schema["fields"] == [
        {"name": "id", "type": "int"},
        {"name": "title", "type": "string"},
        {"name": "active", "type": "boolean"},
        {"name": "at", "type": "datetime"},
        {"name": "note", "type": "string"},
    ]
    assert avro_type(object) == "unknown"

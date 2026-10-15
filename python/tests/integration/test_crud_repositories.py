from datetime import UTC, datetime

import mongomock
import pytest
from pydantic import BaseModel

from app.domain.errors import InvalidFilterError
from app.infrastructure.database.postgres.connector import (
    create_database_engine,
    create_session_factory,
)
from app.interface.repositories.crud import (
    CRUDRepositoryFactory,
    MongoCRUDModel,
    PostgresCRUDModel,
)
from app.interface.repositories.postgres.models import Base, UserModel


class BookDocument(BaseModel):
    title: str
    pages: int
    secret: str | None = None


@pytest.fixture
def session_factory():
    engine = create_database_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = create_session_factory(engine)
    with session_factory() as session:
        session.add_all(
            UserModel(email=f"u{i}@example.com", password="hash", first_name=name, last_name="L")
            for i, name in enumerate(["Ann", "Bob", "Ann"], start=1)
        )
        session.commit()
    yield session_factory
    engine.dispose()


@pytest.fixture
def mongo_database():
    database = mongomock.MongoClient(tz_aware=True)["test"]
    database["books"].insert_many(
        [
            {"title": "A", "pages": 100, "secret": "x", "created_at": datetime.now(UTC)},
            {"title": "B", "pages": 200, "secret": "y", "created_at": datetime.now(UTC)},
        ]
    )
    return database


@pytest.fixture
def factory(session_factory, mongo_database) -> CRUDRepositoryFactory:
    return CRUDRepositoryFactory(
        [
            PostgresCRUDModel(UserModel, hidden_fields=frozenset({"password"})),
            MongoCRUDModel("books", BookDocument, hidden_fields=frozenset({"secret"})),
        ],
        session_factory,
        lambda: mongo_database,
    )


def test_factory_returns_none_for_unknown_slug(factory):
    assert factory.get("user-tokens") is None


def test_postgres_get_one_hides_hidden_fields(factory):
    users = factory.get("users")

    user = users.get_one_by_id("1")

    assert user["email"] == "u1@example.com"
    assert "password" not in user
    assert users.get_one_by_id("999") is None
    assert users.get_one_by_id("not-a-number") is None


def test_postgres_list_filters_and_counts(factory):
    rows, total = factory.get("users").get_list(0, 1, {"first_name": "Ann"})

    assert total == 2
    assert [row["id"] for row in rows] == [1]


@pytest.mark.parametrize(
    "filters", [{"password": "hash"}, {"unknown": "x"}, {"id": "not-a-number"}]
)
def test_postgres_list_rejects_invalid_filters(factory, filters):
    with pytest.raises(InvalidFilterError):
        factory.get("users").get_list(0, 10, filters)


def test_postgres_describe_excludes_hidden_fields(factory):
    schema = factory.get("users").describe()

    assert schema["name"] == "users"
    assert {"name": "email", "type": "string"} in schema["fields"]
    assert {"name": "id", "type": "int"} in schema["fields"]
    assert all(field["name"] != "password" for field in schema["fields"])


def test_mongo_get_one_and_list(factory, mongo_database):
    books = factory.get("books")
    book_id = str(mongo_database["books"].find_one({"title": "B"})["_id"])

    assert books.get_one_by_id(book_id)["title"] == "B"
    assert "secret" not in books.get_one_by_id(book_id)
    assert books.get_one_by_id("not-an-object-id") is None

    rows, total = books.get_list(0, 10, {"pages": "200"})
    assert total == 1
    assert rows[0]["id"] == book_id


def test_mongo_rejects_hidden_filter_and_describes_schema(factory):
    books = factory.get("books")

    with pytest.raises(InvalidFilterError):
        books.get_list(0, 10, {"secret": "x"})
    assert books.describe()["fields"] == [
        {"name": "id", "type": "string"},
        {"name": "title", "type": "string"},
        {"name": "pages", "type": "int"},
    ]

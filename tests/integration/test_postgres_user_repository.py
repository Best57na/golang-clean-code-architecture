import pytest

from app.domain.errors import EmailAlreadyExistsError
from app.infrastructure.database.postgres.connector import (
    create_database_engine,
    create_session_factory,
)
from app.interface.repositories.postgres.models import Base, UserPermissionModel
from app.interface.repositories.postgres.user import PostgresUserRepository


@pytest.fixture
def session_factory():
    engine = create_database_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield create_session_factory(engine)
    engine.dispose()


@pytest.fixture
def repository(session_factory) -> PostgresUserRepository:
    return PostgresUserRepository(session_factory)


@pytest.fixture
def user(repository):
    return repository.insert_user("a@example.com", "hash", "First", "Last")


def test_insert_and_read_user(repository, user):
    credential = repository.get_credential_by_email("a@example.com")

    # Compare ids, not whole entities: SQLite drops timezone info that Postgres keeps
    assert user.id is not None
    assert credential.user.id == user.id
    assert credential.user.email == "a@example.com"
    assert credential.password_hash == "hash"
    assert repository.get_user_by_id(user.id).id == user.id
    assert repository.get_credential_by_email("missing@example.com") is None
    assert repository.get_user_by_id(999) is None


def test_insert_duplicate_email_raises(repository, user):
    with pytest.raises(EmailAlreadyExistsError):
        repository.insert_user("a@example.com", "hash", "Other", "User")


def test_upsert_token_keeps_one_row_per_user(repository, user):
    repository.upsert_token(user.id, "access-1", "refresh-1")
    repository.upsert_token(user.id, "access-2", "refresh-2")

    record = repository.find_token_by_user_id(user.id)

    assert (record.access, record.refresh) == ("access-2", "refresh-2")
    assert record.user.id == user.id


def test_find_token_by_access_only_matches_current_token(repository, user):
    repository.upsert_token(user.id, "access-1", "refresh-1")

    assert repository.find_token_by_user_id_and_access(user.id, "access-1") is not None
    assert repository.find_token_by_user_id_and_access(user.id, "stale") is None


def test_delete_token(repository, user):
    repository.upsert_token(user.id, "access-1", "refresh-1")

    repository.delete_token_by_user_id(user.id)

    assert repository.find_token_by_user_id(user.id) is None


def test_get_permission(repository, session_factory, user):
    assert repository.get_permission_by_user_id(user.id) is None

    with session_factory() as session:
        session.add(UserPermissionModel(user_id=user.id, permission="admin"))
        session.commit()

    assert repository.get_permission_by_user_id(user.id).permission == "admin"

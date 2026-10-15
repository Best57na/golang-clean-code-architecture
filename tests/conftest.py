import pytest
from fastapi.testclient import TestClient

from app.config.settings import Settings
from app.infrastructure.container import build_container
from app.infrastructure.database.postgres.connector import create_database_engine
from app.infrastructure.fastapi.main import create_app
from app.interface.repositories.postgres.models import Base


@pytest.fixture
def settings() -> Settings:
    return Settings(
        _env_file=None,
        name="TEST APP",
        version="9.9.9",
        secret_key="test-secret-key-with-enough-length",
        database_url="sqlite+pysqlite:///:memory:",
        bcrypt_rounds=4,
    )


@pytest.fixture
def engine(settings: Settings):
    engine = create_database_engine(settings.sqlalchemy_url)
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def client(settings: Settings, engine) -> TestClient:
    return TestClient(create_app(settings, build_container(settings, engine)))

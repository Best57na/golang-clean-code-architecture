import pytest
from fastapi.testclient import TestClient

from app.config.settings import Settings
from app.infrastructure.fastapi.main import create_app


@pytest.fixture
def settings() -> Settings:
    return Settings(
        _env_file=None,
        name="TEST APP",
        version="9.9.9",
        secret_key="test-secret-key-with-enough-length",
    )


@pytest.fixture
def client(settings: Settings) -> TestClient:
    return TestClient(create_app(settings))

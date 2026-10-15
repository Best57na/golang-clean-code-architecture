from dataclasses import dataclass

from sqlalchemy import Engine

from app.config.settings import Settings
from app.infrastructure.database.postgres.connector import (
    create_database_engine,
    create_session_factory,
)
from app.interface.repositories.postgres.user import PostgresUserRepository
from app.shared.authentication.jwt_authentication import (
    JWTAuthentication,
    issuer_from_app_name,
)
from app.shared.authentication.password import BcryptPasswordHasher
from app.usecases.user import UserUsecase


@dataclass(frozen=True)
class Container:
    """Every usecase the HTTP layer needs, wired with concrete adapters."""

    user_usecase: UserUsecase


def build_container(settings: Settings, engine: Engine | None = None) -> Container:
    engine = engine or create_database_engine(settings.sqlalchemy_url)
    session_factory = create_session_factory(engine)

    user_repository = PostgresUserRepository(session_factory)
    token_service = JWTAuthentication(
        secret_key=settings.secret_key.get_secret_value(),
        issuer=issuer_from_app_name(settings.name),
        access_expires_seconds=settings.jwt_access_expires,
        refresh_expires_seconds=settings.jwt_refresh_expires,
    )
    password_hasher = BcryptPasswordHasher(rounds=settings.bcrypt_rounds)

    return Container(
        user_usecase=UserUsecase(user_repository, password_hasher, token_service),
    )

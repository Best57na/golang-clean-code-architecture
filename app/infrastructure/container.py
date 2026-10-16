from dataclasses import dataclass
from functools import cache

from sqlalchemy import Engine

from app.config.crud_models import CRUD_MODELS
from app.config.settings import Settings
from app.infrastructure.database.mongodb.connector import create_mongo_database
from app.infrastructure.database.postgres.connector import (
    create_database_engine,
    create_session_factory,
)
from app.interface.repositories.crud import CRUDModel, CRUDRepositoryFactory
from app.interface.repositories.postgres.user import PostgresUserRepository
from app.shared.authentication.jwt_authentication import (
    JWTAuthentication,
    issuer_from_app_name,
)
from app.shared.authentication.password import BcryptPasswordHasher
from app.usecases.crud import CRUDUsecase
from app.usecases.user import UserUsecase


@dataclass(frozen=True)
class Container:
    """Every usecase the HTTP layer needs, wired with concrete adapters."""

    user_usecase: UserUsecase
    crud_usecase: CRUDUsecase


def build_container(
    settings: Settings,
    engine: Engine | None = None,
    crud_models: list[CRUDModel] | None = None,
) -> Container:
    engine = engine or create_database_engine(settings.sqlalchemy_url)
    session_factory = create_session_factory(engine)

    @cache
    def mongo_database():
        return create_mongo_database(settings.mongodb_uri, settings.mongodb_db_name)

    user_repository = PostgresUserRepository(session_factory)
    token_service = JWTAuthentication(
        secret_key=settings.secret_key.get_secret_value(),
        issuer=issuer_from_app_name(settings.name),
        access_expires_seconds=settings.jwt_access_expires,
        refresh_expires_seconds=settings.jwt_refresh_expires,
    )
    password_hasher = BcryptPasswordHasher(rounds=settings.bcrypt_rounds)
    crud_repository_factory = CRUDRepositoryFactory(
        CRUD_MODELS if crud_models is None else crud_models, session_factory, mongo_database
    )

    return Container(
        user_usecase=UserUsecase(user_repository, password_hasher, token_service),
        crud_usecase=CRUDUsecase(crud_repository_factory),
    )

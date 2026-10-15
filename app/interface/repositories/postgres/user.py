from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.domain.entities.user import (
    UserCredential,
    UserEntity,
    UserPermissionEntity,
    UserTokenRecord,
)
from app.domain.errors import EmailAlreadyExistsError
from app.interface.repositories.postgres.models import (
    UserModel,
    UserPermissionModel,
    UserTokenModel,
)


class PostgresUserRepository:
    """SQLAlchemy implementation of IUserRepository. Converts ORM models to domain entities."""

    def __init__(self, session_factory: sessionmaker[Session]):
        self._session_factory = session_factory

    def get_credential_by_email(self, email: str) -> UserCredential | None:
        with self._session_factory() as session:
            user = session.scalar(select(UserModel).where(UserModel.email == email))
            if user is None:
                return None
            return UserCredential(user=UserEntity.model_validate(user), password_hash=user.password)

    def get_user_by_id(self, user_id: int) -> UserEntity | None:
        with self._session_factory() as session:
            user = session.get(UserModel, user_id)
            return UserEntity.model_validate(user) if user else None

    def insert_user(
        self, email: str, password_hash: str, first_name: str, last_name: str
    ) -> UserEntity:
        user = UserModel(
            email=email, password=password_hash, first_name=first_name, last_name=last_name
        )
        with self._session_factory() as session:
            session.add(user)
            try:
                session.commit()
            except IntegrityError as exc:
                raise EmailAlreadyExistsError("email has been used") from exc
            return UserEntity.model_validate(user)

    def upsert_token(self, user_id: int, access: str, refresh: str) -> None:
        with self._session_factory() as session:
            token = session.scalar(select(UserTokenModel).where(UserTokenModel.user_id == user_id))
            if token is None:
                session.add(UserTokenModel(user_id=user_id, access=access, refresh=refresh))
            else:
                token.access = access
                token.refresh = refresh
            session.commit()

    def find_token_by_user_id(self, user_id: int) -> UserTokenRecord | None:
        with self._session_factory() as session:
            token = session.scalar(select(UserTokenModel).where(UserTokenModel.user_id == user_id))
            return self._to_record(token)

    def find_token_by_user_id_and_access(self, user_id: int, access: str) -> UserTokenRecord | None:
        with self._session_factory() as session:
            token = session.scalar(
                select(UserTokenModel).where(
                    UserTokenModel.user_id == user_id, UserTokenModel.access == access
                )
            )
            return self._to_record(token)

    def delete_token_by_user_id(self, user_id: int) -> None:
        with self._session_factory() as session:
            session.execute(delete(UserTokenModel).where(UserTokenModel.user_id == user_id))
            session.commit()

    def get_permission_by_user_id(self, user_id: int) -> UserPermissionEntity | None:
        with self._session_factory() as session:
            permission = session.scalar(
                select(UserPermissionModel).where(UserPermissionModel.user_id == user_id)
            )
            return UserPermissionEntity.model_validate(permission) if permission else None

    @staticmethod
    def _to_record(token: UserTokenModel | None) -> UserTokenRecord | None:
        if token is None:
            return None
        return UserTokenRecord(
            user=UserEntity.model_validate(token.user),
            access=token.access,
            refresh=token.refresh,
        )

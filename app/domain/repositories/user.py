from typing import Protocol

from app.domain.entities.user import (
    UserCredential,
    UserEntity,
    UserPermissionEntity,
    UserTokenRecord,
)


class IUserRepository(Protocol):
    """Persistence port for users. Usecases depend on this, never on a concrete database."""

    def get_credential_by_email(self, email: str) -> UserCredential | None: ...

    def get_user_by_id(self, user_id: int) -> UserEntity | None: ...

    def insert_user(
        self, email: str, password_hash: str, first_name: str, last_name: str
    ) -> UserEntity:
        """Raises EmailAlreadyExistsError when the email is taken."""
        ...

    def upsert_token(self, user_id: int, access: str, refresh: str) -> None: ...

    def find_token_by_user_id(self, user_id: int) -> UserTokenRecord | None: ...

    def find_token_by_user_id_and_access(
        self, user_id: int, access: str
    ) -> UserTokenRecord | None: ...

    def delete_token_by_user_id(self, user_id: int) -> None: ...

    def get_permission_by_user_id(self, user_id: int) -> UserPermissionEntity | None: ...

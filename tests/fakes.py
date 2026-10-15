from datetime import UTC, datetime

from app.domain.entities.user import (
    UserCredential,
    UserEntity,
    UserPermissionEntity,
    UserTokenRecord,
)
from app.domain.errors import EmailAlreadyExistsError


class FakeUserRepository:
    """In-memory IUserRepository for usecase tests."""

    def __init__(self):
        self.credentials: dict[int, UserCredential] = {}
        self.tokens: dict[int, tuple[str, str]] = {}
        self.permissions: dict[int, UserPermissionEntity] = {}

    def get_credential_by_email(self, email: str) -> UserCredential | None:
        return next((c for c in self.credentials.values() if c.user.email == email), None)

    def get_user_by_id(self, user_id: int) -> UserEntity | None:
        credential = self.credentials.get(user_id)
        return credential.user if credential else None

    def insert_user(
        self, email: str, password_hash: str, first_name: str, last_name: str
    ) -> UserEntity:
        if self.get_credential_by_email(email):
            raise EmailAlreadyExistsError("email has been used")
        now = datetime.now(UTC)
        user = UserEntity(
            id=len(self.credentials) + 1,
            email=email,
            first_name=first_name,
            last_name=last_name,
            created_at=now,
            updated_at=now,
        )
        self.credentials[user.id] = UserCredential(user=user, password_hash=password_hash)
        return user

    def upsert_token(self, user_id: int, access: str, refresh: str) -> None:
        self.tokens[user_id] = (access, refresh)

    def find_token_by_user_id(self, user_id: int) -> UserTokenRecord | None:
        if user_id not in self.tokens:
            return None
        access, refresh = self.tokens[user_id]
        return UserTokenRecord(user=self.get_user_by_id(user_id), access=access, refresh=refresh)

    def find_token_by_user_id_and_access(self, user_id: int, access: str) -> UserTokenRecord | None:
        record = self.find_token_by_user_id(user_id)
        return record if record and record.access == access else None

    def delete_token_by_user_id(self, user_id: int) -> None:
        self.tokens.pop(user_id, None)

    def get_permission_by_user_id(self, user_id: int) -> UserPermissionEntity | None:
        return self.permissions.get(user_id)

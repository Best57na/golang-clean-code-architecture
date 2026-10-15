from datetime import datetime
from enum import StrEnum
from typing import Protocol

from app.domain.entities.user import UserTokenClaims, UserTokenPayload


class TokenType(StrEnum):
    ACCESS = "access-token"
    REFRESH = "refresh-token"


class ITokenService(Protocol):
    def sign(
        self,
        token_type: TokenType,
        claims: UserTokenClaims,
        expires_at: datetime | None = None,
    ) -> str:
        """Create a signed token. expires_at keeps an existing expiry (used on refresh)."""
        ...

    def parse(self, token: str, token_type: TokenType) -> UserTokenPayload:
        """Verify a token. Raises InvalidTokenError if invalid, expired or the wrong type."""
        ...


class IPasswordHasher(Protocol):
    def hash(self, password: str) -> str: ...

    def verify(self, password: str, password_hash: str) -> bool: ...

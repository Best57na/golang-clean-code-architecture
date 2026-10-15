import uuid
from datetime import UTC, datetime, timedelta

import jwt

from app.domain.entities.user import UserTokenClaims, UserTokenPayload
from app.domain.errors import InvalidTokenError
from app.domain.services.authentication import TokenType

ALGORITHM = "HS256"
AUDIENCE = ["user", "admin"]


def issuer_from_app_name(app_name: str) -> str:
    return app_name.strip().replace(" ", "-").lower()


class JWTAuthentication:
    """HS256 JWT implementation of ITokenService."""

    def __init__(
        self,
        secret_key: str,
        issuer: str,
        access_expires_seconds: int,
        refresh_expires_seconds: int,
    ):
        self._secret_key = secret_key
        self._issuer = issuer
        self._lifetimes = {
            TokenType.ACCESS: timedelta(seconds=access_expires_seconds),
            TokenType.REFRESH: timedelta(seconds=refresh_expires_seconds),
        }

    def sign(
        self,
        token_type: TokenType,
        claims: UserTokenClaims,
        expires_at: datetime | None = None,
    ) -> str:
        now = datetime.now(UTC)
        payload = {
            "claims": claims.model_dump(),
            "iss": self._issuer,
            "sub": token_type.value,
            "aud": AUDIENCE,
            "exp": expires_at or now + self._lifetimes[token_type],
            "nbf": now,
            "iat": now,
            # Unique id so two tokens issued in the same second are still different
            "jti": uuid.uuid4().hex,
        }
        return jwt.encode(payload, self._secret_key, algorithm=ALGORITHM)

    def parse(self, token: str, token_type: TokenType) -> UserTokenPayload:
        try:
            payload = jwt.decode(
                token,
                self._secret_key,
                algorithms=[ALGORITHM],
                audience=AUDIENCE[0],
                issuer=self._issuer,
                options={"require": ["exp", "iat", "sub", "claims"]},
            )
        except jwt.ExpiredSignatureError as exc:
            raise InvalidTokenError("token had expired") from exc
        except jwt.DecodeError as exc:
            raise InvalidTokenError("token format is invalid") from exc
        except jwt.InvalidTokenError as exc:
            raise InvalidTokenError(f"parse token failed: {exc}") from exc

        if payload["sub"] != token_type.value:
            raise InvalidTokenError("token type is invalid")

        return UserTokenPayload(
            claims=UserTokenClaims.model_validate(payload["claims"]),
            expires_at=datetime.fromtimestamp(payload["exp"], tz=UTC),
        )

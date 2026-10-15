from collections.abc import Callable
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.domain.entities.user import UserEntity, UserPermissionEntity
from app.domain.errors import InvalidTokenError
from app.interface.handlers.fastapi.response import APIError
from app.usecases.user import UserUsecase

JWT_AUTH_ERROR = "middleware-002"


@dataclass(frozen=True)
class AuthContext:
    user: UserEntity
    permission: UserPermissionEntity | None


JWTAuth = Callable[..., AuthContext]


def build_jwt_auth(user_usecase: UserUsecase) -> JWTAuth:
    """Dependency that requires a valid `Authorization: Bearer <access token>` header."""

    bearer = HTTPBearer(auto_error=False)

    def jwt_auth(
        credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    ) -> AuthContext:
        if credentials is None:
            raise APIError(401, JWT_AUTH_ERROR, "missing bearer token")
        try:
            user, permission = user_usecase.user_authentication(credentials.credentials)
        except InvalidTokenError as exc:
            raise APIError(401, JWT_AUTH_ERROR, str(exc)) from exc
        return AuthContext(user=user, permission=permission)

    return jwt_auth

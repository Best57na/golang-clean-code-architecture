from datetime import datetime

from app.domain.entities.user import (
    UserEntity,
    UserLoginRequest,
    UserLoginResponse,
    UserPermissionEntity,
    UserRefreshTokenRequest,
    UserRegisterRequest,
    UserTokenClaims,
    UserTokenEntity,
    UserTokenPayload,
    UserTokenRecord,
)
from app.domain.errors import InvalidCredentialsError, InvalidTokenError
from app.domain.repositories.user import IUserRepository
from app.domain.services.authentication import IPasswordHasher, ITokenService, TokenType


class UserUsecase:
    def __init__(
        self,
        user_repository: IUserRepository,
        password_hasher: IPasswordHasher,
        token_service: ITokenService,
    ):
        self._users = user_repository
        self._hasher = password_hasher
        self._tokens = token_service

    def register_user(self, request: UserRegisterRequest) -> UserEntity:
        return self._users.insert_user(
            email=request.email,
            password_hash=self._hasher.hash(request.password),
            first_name=request.first_name,
            last_name=request.last_name,
        )

    def user_login(self, request: UserLoginRequest) -> UserLoginResponse:
        credential = self._users.get_credential_by_email(request.email)
        # Same error for unknown email and wrong password so emails cannot be enumerated
        if credential is None or not self._hasher.verify(
            request.password, credential.password_hash
        ):
            raise InvalidCredentialsError("email or password is invalid")

        return self._issue_tokens(credential.user)

    def user_refresh_token(self, request: UserRefreshTokenRequest) -> UserLoginResponse:
        payload, record = self._verify_refresh_token(request.refresh_token)
        # Keep the original refresh expiry so a session cannot be extended forever
        return self._issue_tokens(record.user, refresh_expires_at=payload.expires_at)

    def user_logout(self, request: UserRefreshTokenRequest) -> None:
        payload, _ = self._verify_refresh_token(request.refresh_token)
        self._users.delete_token_by_user_id(payload.claims.id)

    def user_authentication(
        self, access_token: str
    ) -> tuple[UserEntity, UserPermissionEntity | None]:
        payload = self._tokens.parse(access_token, TokenType.ACCESS)

        # The token must still be the stored one, so logout and refresh revoke old tokens
        record = self._users.find_token_by_user_id_and_access(payload.claims.id, access_token)
        if record is None:
            raise InvalidTokenError("user token not found")

        permission = self._users.get_permission_by_user_id(record.user.id)
        return record.user, permission

    def _verify_refresh_token(self, refresh_token: str) -> tuple[UserTokenPayload, UserTokenRecord]:
        payload = self._tokens.parse(refresh_token, TokenType.REFRESH)

        record = self._users.find_token_by_user_id(payload.claims.id)
        if record is None or record.refresh != refresh_token:
            raise InvalidTokenError("user token not found")

        return payload, record

    def _issue_tokens(
        self, user: UserEntity, refresh_expires_at: datetime | None = None
    ) -> UserLoginResponse:
        claims = UserTokenClaims(id=user.id)
        token = UserTokenEntity(
            access=self._tokens.sign(TokenType.ACCESS, claims),
            refresh=self._tokens.sign(TokenType.REFRESH, claims, expires_at=refresh_expires_at),
        )
        self._users.upsert_token(user.id, token.access, token.refresh)
        return UserLoginResponse(user=user, token=token)

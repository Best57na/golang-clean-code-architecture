from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.domain.entities.user import (
    UserEntity,
    UserLoginRequest,
    UserLoginResponse,
    UserRefreshTokenRequest,
    UserRegisterRequest,
)
from app.domain.errors import (
    EmailAlreadyExistsError,
    InvalidCredentialsError,
    InvalidTokenError,
)
from app.interface.handlers.fastapi.dependencies import AuthContext, JWTAuth
from app.interface.handlers.fastapi.response import APIError, ErrorResponse
from app.usecases.user import UserUsecase

REGISTER_USER_ERROR = "users-001"
LOGIN_USER_ERROR = "users-002"
REFRESH_TOKEN_ERROR = "users-003"
LOGOUT_USER_ERROR = "users-004"

ERROR_RESPONSES = {
    400: {"model": ErrorResponse},
    401: {"model": ErrorResponse},
}


def build_user_router(user_usecase: UserUsecase, jwt_auth: JWTAuth) -> APIRouter:
    router = APIRouter(prefix="/users", tags=["User"], responses=ERROR_RESPONSES)

    @router.post(
        "/register",
        status_code=status.HTTP_201_CREATED,
        responses={409: {"model": ErrorResponse}},
    )
    def register_user(request: UserRegisterRequest) -> UserEntity:
        try:
            return user_usecase.register_user(request)
        except EmailAlreadyExistsError as exc:
            raise APIError(409, REGISTER_USER_ERROR, str(exc)) from exc

    @router.post("/login")
    def user_login(request: UserLoginRequest) -> UserLoginResponse:
        try:
            return user_usecase.user_login(request)
        except InvalidCredentialsError as exc:
            raise APIError(401, LOGIN_USER_ERROR, str(exc)) from exc

    @router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
    def user_logout(request: UserRefreshTokenRequest) -> Response:
        try:
            user_usecase.user_logout(request)
        except InvalidTokenError as exc:
            raise APIError(401, LOGOUT_USER_ERROR, str(exc)) from exc
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    @router.post("/refresh-token")
    def refresh_token(request: UserRefreshTokenRequest) -> UserLoginResponse:
        try:
            return user_usecase.user_refresh_token(request)
        except InvalidTokenError as exc:
            raise APIError(401, REFRESH_TOKEN_ERROR, str(exc)) from exc

    # GET is the REST-correct verb; POST is kept for parity with the Go routes
    @router.get("/profile", operation_id="get_user_profile")
    @router.post("/profile", operation_id="post_user_profile")
    def get_user_profile(auth: Annotated[AuthContext, Depends(jwt_auth)]) -> UserEntity:
        return auth.user

    return router

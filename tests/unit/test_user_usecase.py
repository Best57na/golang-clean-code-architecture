import pytest

from app.domain.entities.user import (
    UserLoginRequest,
    UserPermissionEntity,
    UserRefreshTokenRequest,
    UserRegisterRequest,
)
from app.domain.errors import (
    EmailAlreadyExistsError,
    InvalidCredentialsError,
    InvalidTokenError,
)
from app.domain.services.authentication import TokenType
from app.shared.authentication.jwt_authentication import JWTAuthentication
from app.shared.authentication.password import BcryptPasswordHasher
from app.usecases.user import UserUsecase
from tests.fakes import FakeUserRepository

EMAIL = "somchai@example.com"
PASSWORD = "super-secret-1"


@pytest.fixture
def repository() -> FakeUserRepository:
    return FakeUserRepository()


@pytest.fixture
def tokens() -> JWTAuthentication:
    return JWTAuthentication("unit-test-secret-key-with-enough-length", "test-app", 60, 120)


@pytest.fixture
def usecase(repository, tokens) -> UserUsecase:
    return UserUsecase(repository, BcryptPasswordHasher(rounds=4), tokens)


@pytest.fixture
def registered(usecase):
    return usecase.register_user(
        UserRegisterRequest(
            email=EMAIL, password=PASSWORD, first_name="Somchai", last_name="Jaidee"
        )
    )


def login(usecase, password=PASSWORD):
    return usecase.user_login(UserLoginRequest(email=EMAIL, password=password))


def test_register_stores_hashed_password(usecase, repository, registered):
    stored = repository.credentials[registered.id]

    assert registered.email == EMAIL
    assert stored.password_hash != PASSWORD
    assert stored.password_hash.startswith("$2b$")


def test_register_rejects_duplicate_email(usecase, registered):
    with pytest.raises(EmailAlreadyExistsError):
        usecase.register_user(
            UserRegisterRequest(email=EMAIL, password=PASSWORD, first_name="A", last_name="B")
        )


def test_login_returns_user_and_stores_tokens(usecase, repository, registered):
    response = login(usecase)

    assert response.user.id == registered.id
    assert repository.tokens[registered.id] == (response.token.access, response.token.refresh)


def test_login_uses_same_error_for_unknown_email_and_wrong_password(usecase, registered):
    with pytest.raises(InvalidCredentialsError) as wrong_password:
        login(usecase, password="wrong-password")
    with pytest.raises(InvalidCredentialsError) as unknown_email:
        usecase.user_login(UserLoginRequest(email="nobody@example.com", password=PASSWORD))

    assert str(wrong_password.value) == str(unknown_email.value)


class CountingHasher(BcryptPasswordHasher):
    def __init__(self):
        super().__init__(rounds=4)
        self.verify_calls = 0

    def verify(self, password: str, password_hash: str) -> bool:
        self.verify_calls += 1
        return super().verify(password, password_hash)


def test_login_with_unknown_email_still_runs_bcrypt(repository, tokens):
    hasher = CountingHasher()
    usecase = UserUsecase(repository, hasher, tokens)

    with pytest.raises(InvalidCredentialsError):
        usecase.user_login(UserLoginRequest(email="nobody@example.com", password=PASSWORD))

    # Same work as a wrong password, so response time does not reveal the email exists
    assert hasher.verify_calls == 1


def test_authentication_returns_user_and_permission(usecase, repository, registered):
    repository.permissions[registered.id] = UserPermissionEntity(
        id=1, user_id=registered.id, permission="admin"
    )
    access = login(usecase).token.access

    user, permission = usecase.user_authentication(access)

    assert user.id == registered.id
    assert permission.permission == "admin"


def test_authentication_rejects_refresh_token(usecase, registered):
    refresh = login(usecase).token.refresh

    with pytest.raises(InvalidTokenError):
        usecase.user_authentication(refresh)


def test_refresh_rotates_tokens_and_keeps_refresh_expiry(usecase, tokens, registered):
    first = login(usecase).token

    second = usecase.user_refresh_token(UserRefreshTokenRequest(refresh_token=first.refresh)).token

    assert second.access != first.access
    assert second.refresh != first.refresh
    assert (
        tokens.parse(second.refresh, TokenType.REFRESH).expires_at
        == tokens.parse(first.refresh, TokenType.REFRESH).expires_at
    )
    with pytest.raises(InvalidTokenError):
        usecase.user_authentication(first.access)
    with pytest.raises(InvalidTokenError):
        usecase.user_refresh_token(UserRefreshTokenRequest(refresh_token=first.refresh))


def test_logout_revokes_tokens(usecase, repository, registered):
    token = login(usecase).token

    usecase.user_logout(UserRefreshTokenRequest(refresh_token=token.refresh))

    assert registered.id not in repository.tokens
    with pytest.raises(InvalidTokenError):
        usecase.user_authentication(token.access)

from datetime import UTC, datetime, timedelta

import pytest

from app.domain.entities.user import UserTokenClaims
from app.domain.errors import InvalidTokenError
from app.domain.services.authentication import TokenType
from app.shared.authentication.jwt_authentication import (
    JWTAuthentication,
    issuer_from_app_name,
)
from app.shared.authentication.password import BcryptPasswordHasher


@pytest.fixture
def tokens() -> JWTAuthentication:
    return JWTAuthentication(
        secret_key="unit-test-secret-key-with-enough-length",
        issuer="test-app",
        access_expires_seconds=60,
        refresh_expires_seconds=120,
    )


def test_issuer_replaces_spaces_and_lowercases():
    assert issuer_from_app_name("PYTHON FIRST API APP") == "python-first-api-app"


def test_sign_and_parse_round_trip(tokens):
    token = tokens.sign(TokenType.ACCESS, UserTokenClaims(id=7))

    payload = tokens.parse(token, TokenType.ACCESS)

    assert payload.claims.id == 7


def test_refresh_token_uses_refresh_lifetime(tokens):
    before = datetime.now(UTC)
    access = tokens.parse(tokens.sign(TokenType.ACCESS, UserTokenClaims(id=1)), TokenType.ACCESS)
    refresh = tokens.parse(tokens.sign(TokenType.REFRESH, UserTokenClaims(id=1)), TokenType.REFRESH)

    assert access.expires_at - before <= timedelta(seconds=61)
    assert refresh.expires_at - before >= timedelta(seconds=119)


def test_sign_keeps_given_expiry(tokens):
    expires_at = datetime.now(UTC).replace(microsecond=0) + timedelta(seconds=30)

    token = tokens.sign(TokenType.REFRESH, UserTokenClaims(id=1), expires_at=expires_at)

    assert tokens.parse(token, TokenType.REFRESH).expires_at == expires_at


def test_tokens_issued_in_same_second_are_unique(tokens):
    claims = UserTokenClaims(id=1)

    assert tokens.sign(TokenType.ACCESS, claims) != tokens.sign(TokenType.ACCESS, claims)


def test_parse_rejects_wrong_token_type(tokens):
    refresh = tokens.sign(TokenType.REFRESH, UserTokenClaims(id=1))

    with pytest.raises(InvalidTokenError, match="token type is invalid"):
        tokens.parse(refresh, TokenType.ACCESS)


def test_parse_rejects_expired_token(tokens):
    expired = tokens.sign(
        TokenType.ACCESS,
        UserTokenClaims(id=1),
        expires_at=datetime.now(UTC) - timedelta(seconds=5),
    )

    with pytest.raises(InvalidTokenError, match="token had expired"):
        tokens.parse(expired, TokenType.ACCESS)


def test_parse_rejects_malformed_token(tokens):
    with pytest.raises(InvalidTokenError, match="token format is invalid"):
        tokens.parse("not-a-jwt", TokenType.ACCESS)


def test_parse_rejects_token_signed_with_other_key(tokens):
    other = JWTAuthentication("another-secret-key-with-enough-length", "test-app", 60, 120)
    token = other.sign(TokenType.ACCESS, UserTokenClaims(id=1))

    with pytest.raises(InvalidTokenError):
        tokens.parse(token, TokenType.ACCESS)


def test_password_hasher_verifies_only_matching_password():
    hasher = BcryptPasswordHasher(rounds=4)
    password_hash = hasher.hash("correct-password")

    assert hasher.verify("correct-password", password_hash)
    assert not hasher.verify("wrong-password", password_hash)
    assert not hasher.verify("correct-password", "not-a-bcrypt-hash")

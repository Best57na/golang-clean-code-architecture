from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UserEntity(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    first_name: str
    last_name: str
    created_at: datetime
    updated_at: datetime


class UserCredential(BaseModel):
    """A user together with the stored password hash. Never returned to clients."""

    user: UserEntity
    password_hash: str


class UserTokenEntity(BaseModel):
    access: str
    refresh: str


class UserTokenClaims(BaseModel):
    id: int


class UserTokenPayload(BaseModel):
    """Result of verifying a JWT: who it belongs to and when it expires."""

    claims: UserTokenClaims
    expires_at: datetime


class UserTokenRecord(BaseModel):
    """The token pair currently stored for a user (one active session per user)."""

    user: UserEntity
    access: str
    refresh: str


class UserPermissionEntity(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    permission: str

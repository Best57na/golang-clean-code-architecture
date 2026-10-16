from pydantic import BaseModel

from app.domain.entities.user.user import UserEntity, UserTokenEntity


class UserLoginResponse(BaseModel):
    user: UserEntity
    token: UserTokenEntity

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SignupRequest(BaseModel):
    username: str = Field(min_length=3, max_length=30, pattern=r"^[a-z0-9_]+$")
    password: str = Field(min_length=8, max_length=72)

    @field_validator("password")
    @classmethod
    def check_password_bytes(cls, v: str) -> str:
        if len(v.encode()) > 72:
            raise ValueError("비밀번호는 72바이트 이하여야 합니다")
        return v


class LoginRequest(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    role: str
    is_active: bool
    token_limit: int
    created_at: datetime

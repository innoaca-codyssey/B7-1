from datetime import datetime
from typing import Annotated

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)

Email = Annotated[EmailStr, Field(max_length=254), AfterValidator(str.lower)]


class SignupRequest(BaseModel):
    username: str = Field(min_length=3, max_length=30, pattern=r"^[a-z0-9_]+$")
    password: str = Field(min_length=8, max_length=72)
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=30)]
    email: Email

    @field_validator("password")
    @classmethod
    def check_password_bytes(cls, v: str) -> str:
        if len(v.encode()) > 72:
            raise ValueError("비밀번호는 72바이트 이하여야 합니다")
        return v


class AccountLookup(BaseModel):
    username: str | None = None
    email: Email | None = None

    @model_validator(mode="after")
    def check_identifier(self):
        if not self.username and not self.email:
            raise ValueError("username 또는 email이 필요합니다")
        return self


class VerifyEmailRequest(AccountLookup):
    code: str = Field(pattern=r"^\d{6}$")


class LoginRequest(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    display_name: str
    email: str | None
    email_verified_at: datetime | None
    role: str
    is_active: bool
    token_limit: int
    created_at: datetime

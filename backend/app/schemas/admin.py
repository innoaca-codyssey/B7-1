from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.auth import UserOut


class AdminUserOut(UserOut):
    month_used: int
    session_count: int


class AdminUserUpdate(BaseModel):
    role: Literal["user", "admin"] | None = None
    is_active: bool | None = None
    token_limit: int | None = Field(None, ge=0)

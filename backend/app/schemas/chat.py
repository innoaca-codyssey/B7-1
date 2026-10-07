from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints

from app.schemas.session import MessageOut, Preset


class ChatRequest(BaseModel):
    session_id: int | None = None
    message: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=4000)]
    model_code: str | None = Field(None, max_length=50)
    preset: Preset | None = None


class UsageOut(BaseModel):
    month_used: int
    token_limit: int
    remaining: int


class ChatResponse(BaseModel):
    session_id: int
    user_message: MessageOut
    assistant_message: MessageOut
    usage: UsageOut | None = None

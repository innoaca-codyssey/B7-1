from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Preset = Literal["tutor", "code_review", "debug", "concept"]


class SessionCreate(BaseModel):
    title: str | None = Field(None, max_length=100)
    model_code: str | None = Field(None, max_length=50)
    preset: Preset = "tutor"


class SessionUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=100)
    model_code: str | None = Field(None, max_length=50)
    preset: Preset | None = None


class SessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    model_code: str
    preset: str
    created_at: datetime
    updated_at: datetime
    message_count: int


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: int
    role: str
    content: str
    status: str
    error_code: str | None
    model_code: str | None
    input_tokens: int
    output_tokens: int
    billed_tokens: int
    latency_ms: int | None
    created_at: datetime

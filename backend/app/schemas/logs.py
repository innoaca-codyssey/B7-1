from datetime import datetime

from pydantic import BaseModel


class ChatLogOut(BaseModel):
    id: int
    session_id: int
    session_title: str
    question: str
    answer: str | None
    status: str
    error_code: str | None
    model_code: str | None
    billed_tokens: int
    created_at: datetime


class ChatLogPage(BaseModel):
    items: list[ChatLogOut]
    total: int


class AdminChatLogOut(ChatLogOut):
    username: str
    name: str


class AdminChatLogPage(BaseModel):
    items: list[AdminChatLogOut]
    total: int

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.logging_config import log_event
from app.models import User
from app.schemas.chat import ChatRequest, ChatResponse
from app.services import chat

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def post_chat(
    body: ChatRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    request_id = request.state.request_id
    log_event("request_received", user_id=user.id, path=request.url.path, request_id=request_id)
    return chat.handle_chat(db, user, body, request_id)

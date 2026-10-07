import time

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import settings
from app.crud import ai_models, messages, sessions
from app.logging_config import log_event
from app.models import User
from app.presets import DEFAULT_PRESET, PRESETS
from app.schemas.chat import ChatRequest, ChatResponse
from app.services import ai_client
from app.services.quota import billed_tokens


def handle_chat(db: Session, user: User, body: ChatRequest, request_id: str) -> ChatResponse:
    chat_session = None
    if body.session_id is not None:
        chat_session = sessions.get_owned(db, body.session_id, user.id)
        if not chat_session:
            raise HTTPException(
                status_code=404,
                detail={"code": "NOT_FOUND", "message": "대화를 찾을 수 없습니다."},
            )

    model_code = body.model_code or (chat_session.model_code if chat_session else None)
    model = ai_models.get_active(db, model_code)
    if not model:
        raise HTTPException(
            status_code=400,
            detail={"code": "MODEL_UNAVAILABLE", "message": "사용할 수 없는 모델입니다."},
        )
    preset = body.preset or (chat_session.preset if chat_session else DEFAULT_PRESET)

    if not chat_session:
        chat_session = sessions.create(db, user.id, body.message[:30], model.code, preset)

    user_message = messages.create(
        db, session_id=chat_session.id, user_id=user.id, role="user", content=body.message
    )
    history = messages.list_recent_ok(db, chat_session.id, settings.context_window)
    prompt = [{"role": "system", "content": PRESETS[preset].system_prompt}]
    prompt += [{"role": m.role, "content": m.content} for m in history]

    log_event("ai_call_start", user_id=user.id, request_id=request_id, model=model.code)
    started = time.monotonic()
    result = ai_client.chat(model.code, prompt, model.max_tokens)
    latency_ms = int((time.monotonic() - started) * 1000)
    log_event(
        "ai_call_success",
        request_id=request_id,
        latency_ms=latency_ms,
        tokens=result.input_tokens + result.output_tokens,
    )

    assistant_message = messages.create(
        db,
        session_id=chat_session.id,
        user_id=user.id,
        role="assistant",
        content=result.content,
        model_code=model.code,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
        billed_tokens=billed_tokens(result.input_tokens, result.output_tokens, model.multiplier),
        latency_ms=latency_ms,
        request_id=request_id,
    )
    log_event("db_save_success", user_id=user.id, message_id=assistant_message.id)
    sessions.update(
        db, chat_session, {"model_code": model.code, "preset": preset, "updated_at": func.now()}
    )

    return ChatResponse(
        session_id=chat_session.id,
        user_message=user_message,
        assistant_message=assistant_message,
    )

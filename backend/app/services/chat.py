import logging
import time

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.config import settings
from app.crud import ai_models, messages, sessions
from app.logging_config import log_event
from app.models import ChatSession, Message, User
from app.presets import DEFAULT_PRESET, PRESETS
from app.schemas.chat import ChatRequest, ChatResponse
from app.services import ai_client, quota
from app.services.ai_client import AIError
from app.services.quota import billed_tokens

AI_ERROR_STATUS = {"AI_TIMEOUT": 504, "AI_ERROR": 502}
AI_ERROR_MESSAGES = {
    "AI_TIMEOUT": "현재 응답이 지연되고 있어요. 잠시 후 다시 시도해 주세요.",
    "AI_ERROR": "AI 응답을 받지 못했어요. 잠시 후 다시 시도해 주세요.",
}


def handle_chat(db: Session, user: User, body: ChatRequest, request_id: str) -> ChatResponse:
    quota.check_quota(db, user)

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

    session_id, user_id = chat_session.id, user.id
    model_code, max_tokens, multiplier = model.code, model.max_tokens, model.multiplier
    user_message = save_message(
        db, session_id=session_id, user_id=user_id, role="user", content=body.message
    )
    history = messages.list_recent_ok(db, session_id, settings.context_window)
    prompt = [{"role": "system", "content": PRESETS[preset].system_prompt}]
    prompt += [{"role": m.role, "content": m.content} for m in history]
    db.commit()

    log_event("ai_call_start", user_id=user_id, request_id=request_id, model=model_code)
    started = time.monotonic()
    try:
        result = ai_client.chat(model_code, prompt, max_tokens)
    except AIError as e:
        latency_ms = int((time.monotonic() - started) * 1000)
        log_event(
            "ai_call_fail",
            logging.WARNING,
            request_id=request_id,
            error_code=e.code,
            latency_ms=latency_ms,
        )
        user_message.status = "error"
        user_message.error_code = e.code
        save_message(
            db,
            question=user_message,
            session_id=session_id,
            user_id=user_id,
            role="assistant",
            content=AI_ERROR_MESSAGES[e.code],
            status="error",
            error_code=e.code,
            model_code=model_code,
            latency_ms=latency_ms,
            request_id=request_id,
        )
        touch_session(db, chat_session, model_code, preset)
        raise HTTPException(
            status_code=AI_ERROR_STATUS[e.code],
            detail={
                "code": e.code,
                "message": AI_ERROR_MESSAGES[e.code],
                "session_id": session_id,
            },
        ) from e

    latency_ms = int((time.monotonic() - started) * 1000)
    log_event(
        "ai_call_success",
        request_id=request_id,
        latency_ms=latency_ms,
        tokens=result.input_tokens + result.output_tokens,
    )

    assistant_message = save_message(
        db,
        question=user_message,
        session_id=session_id,
        user_id=user_id,
        role="assistant",
        content=result.content,
        model_code=model_code,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
        billed_tokens=billed_tokens(result.input_tokens, result.output_tokens, multiplier),
        latency_ms=latency_ms,
        request_id=request_id,
    )
    touch_session(db, chat_session, model_code, preset)

    return ChatResponse(
        session_id=session_id,
        user_message=user_message,
        assistant_message=assistant_message,
        usage=quota.get_usage(db, user),
    )


def save_message(db: Session, user_id: int, question: Message | None = None, **fields) -> Message:
    try:
        message = messages.create(db, user_id=user_id, **fields)
    except SQLAlchemyError as e:
        db.rollback()
        log_event("db_save_fail", logging.ERROR, user_id=user_id, error=type(e).__name__)
        if question is not None:
            mark_question_failed(db, question, user_id)
        raise HTTPException(
            status_code=500,
            detail={
                "code": "DB_ERROR",
                "message": "대화를 저장하지 못했습니다. 잠시 후 다시 시도해 주세요.",
                "session_id": fields["session_id"],
            },
        ) from e
    log_event("db_save_success", user_id=user_id, message_id=message.id)
    return message


def mark_question_failed(db: Session, question: Message, user_id: int) -> None:
    try:
        question.status = "error"
        question.error_code = "DB_ERROR"
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        log_event("db_save_fail", logging.ERROR, user_id=user_id, error=type(e).__name__)


def touch_session(db: Session, chat_session: ChatSession, model_code: str, preset: str) -> None:
    sessions.update(
        db, chat_session, {"model_code": model_code, "preset": preset, "updated_at": func.now()}
    )

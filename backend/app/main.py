import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request

from app import models  # noqa: F401
from app.config import settings
from app.crud import ai_models, users
from app.database import Base, SessionLocal, engine, upgrade_users_table
from app.logging_config import log_event, setup_logging
from app.routers import admin, admin_models, auth, chat, logs, sessions, usage
from app.routers import models as models_router

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    with engine.begin() as conn:
        upgrade_users_table(conn)
    with SessionLocal() as db:
        ai_models.seed_defaults(db)
        if settings.admin_username and settings.admin_password:
            users.ensure_admin(
                db, settings.admin_username, settings.admin_password.get_secret_value()
            )
    yield


DESCRIPTION = """
로그인한 사용자의 질문을 AI API로 전달하고 대화를 저장하는 챗봇 서비스 API입니다.

로그인하면 `access_token` 쿠키(HttpOnly)가 발급되고, 인증이 필요한 API는 이 쿠키로 사용자를
확인합니다. 이 화면에서 `POST /api/auth/login`을 실행하면 이후 요청에 쿠키가 함께 전송됩니다.

오류는 `{"detail": {"code": "...", "message": "..."}}` 형식으로 반환하며, 입력 형식 오류는
FastAPI 기본 422 형식입니다.
"""

TAGS = [
    {"name": "auth", "description": "회원가입, 이메일 인증, 로그인, 로그아웃"},
    {"name": "sessions", "description": "대화 목록과 메시지 조회, 생성, 수정, 삭제"},
    {"name": "chat", "description": "질문 전송과 AI 응답"},
    {"name": "models", "description": "사용 가능한 모델과 대화 프리셋"},
    {"name": "me", "description": "내 대화 기록과 이번 달 토큰 사용량"},
    {"name": "admin", "description": "사용자, 모델, 대화 기록, 사용량 관리 (관리자 전용)"},
]

app = FastAPI(
    title="B7-1 Chatbot API",
    version="1.0.0",
    description=DESCRIPTION,
    openapi_tags=TAGS,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)
app.include_router(auth.router)
app.include_router(sessions.router)
app.include_router(models_router.router)
app.include_router(chat.router)
app.include_router(usage.router)
app.include_router(admin_models.router)
app.include_router(logs.router)
app.include_router(admin.router)


@app.middleware("http")
async def log_request(request: Request, call_next):
    request.state.request_id = uuid.uuid4().hex[:12]
    log_event(
        "request_received",
        method=request.method,
        path=request.url.path,
        request_id=request.state.request_id,
    )
    return await call_next(request)

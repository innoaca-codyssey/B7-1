import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request

from app import models  # noqa: F401
from app.crud import ai_models
from app.database import Base, SessionLocal, engine
from app.logging_config import log_event, setup_logging
from app.routers import auth, chat, sessions, usage
from app.routers import models as models_router

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        ai_models.seed_defaults(db)
    yield


app = FastAPI(title="B7-1 Chatbot API", lifespan=lifespan)
app.include_router(auth.router)
app.include_router(models_router.router)
app.include_router(sessions.router)
app.include_router(chat.router)
app.include_router(usage.router)


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

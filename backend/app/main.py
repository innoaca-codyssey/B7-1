import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request

from app import models  # noqa: F401
from app.database import Base, engine
from app.logging_config import log_event, setup_logging

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    yield


app = FastAPI(title="B7-1 Chatbot API", lifespan=lifespan)


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

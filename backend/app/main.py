from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import models  # noqa: F401
from app.crud import ai_models
from app.database import Base, SessionLocal, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        ai_models.seed_defaults(db)
    yield


app = FastAPI(title="B7-1 Chatbot API", lifespan=lifespan)

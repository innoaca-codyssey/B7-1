from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import models  # noqa: F401
from app.database import Base, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    yield


app = FastAPI(title="B7-1 Chatbot API", lifespan=lifespan)

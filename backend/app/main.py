from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import models  # noqa: F401
from app.config import settings
from app.crud import users
from app.database import Base, SessionLocal, engine
from app.routers import admin, auth, logs, sessions


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    if settings.admin_username and settings.admin_password:
        with SessionLocal() as db:
            users.ensure_admin(db, settings.admin_username, settings.admin_password)
    yield


app = FastAPI(title="B7-1 Chatbot API", lifespan=lifespan)
app.include_router(auth.router)
app.include_router(sessions.router)
app.include_router(logs.router)
app.include_router(admin.router)

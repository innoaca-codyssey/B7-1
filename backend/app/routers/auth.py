from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.crud import users
from app.database import get_db
from app.schemas.auth import SignupRequest, UserOut
from app.security import hash_password

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/signup", response_model=UserOut, status_code=201)
def signup(body: SignupRequest, db: Annotated[Session, Depends(get_db)]):
    try:
        return users.create(db, body.username, hash_password(body.password))
    except users.UsernameTakenError:
        raise HTTPException(
            status_code=409,
            detail={"code": "USERNAME_TAKEN", "message": "이미 사용 중인 아이디입니다."},
        ) from None

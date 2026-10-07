from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.config import settings
from app.crud import users
from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.schemas.auth import LoginRequest, SignupRequest, UserOut
from app.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/signup", response_model=UserOut, status_code=201)
def signup(body: SignupRequest, db: Annotated[Session, Depends(get_db)]):
    try:
        return users.create(
            db,
            body.username,
            hash_password(body.password),
            display_name=body.name,
            email=body.email,
        )
    except users.UsernameTakenError:
        raise HTTPException(
            status_code=409,
            detail={"code": "USERNAME_TAKEN", "message": "이미 사용 중인 아이디입니다."},
        ) from None
    except users.EmailTakenError:
        raise HTTPException(
            status_code=409,
            detail={"code": "EMAIL_TAKEN", "message": "이미 사용 중인 이메일입니다."},
        ) from None


@router.post("/login", response_model=UserOut)
def login(body: LoginRequest, response: Response, db: Annotated[Session, Depends(get_db)]):
    user = users.get_by_username(db, body.username)
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=401,
            detail={
                "code": "INVALID_CREDENTIALS",
                "message": "아이디 또는 비밀번호가 올바르지 않습니다.",
            },
        )
    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail={"code": "USER_DISABLED", "message": "비활성화된 계정입니다."},
        )
    response.set_cookie(
        "access_token",
        create_access_token(user.id),
        max_age=settings.jwt_expire_minutes * 60,
        httponly=True,
        samesite="lax",
    )
    return user


@router.post("/logout", status_code=204)
def logout(response: Response):
    response.delete_cookie("access_token", httponly=True, samesite="lax")


@router.get("/me", response_model=UserOut)
def me(user: Annotated[User, Depends(get_current_user)]):
    return user

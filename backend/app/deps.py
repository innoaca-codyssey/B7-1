from typing import Annotated

from fastapi import Cookie, Depends, HTTPException
from sqlalchemy.orm import Session

from app.crud import users
from app.database import get_db
from app.models import User
from app.security import decode_access_token


def get_current_user(
    db: Annotated[Session, Depends(get_db)],
    access_token: Annotated[str | None, Cookie()] = None,
) -> User:
    user_id = decode_access_token(access_token) if access_token else None
    user = users.get(db, user_id) if user_id else None
    if not user:
        raise HTTPException(
            status_code=401,
            detail={"code": "UNAUTHORIZED", "message": "로그인이 필요합니다."},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail={"code": "USER_DISABLED", "message": "비활성화된 계정입니다."},
        )
    return user


def require_admin(user: Annotated[User, Depends(get_current_user)]) -> User:
    if user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail={"code": "FORBIDDEN", "message": "관리자만 사용할 수 있습니다."},
        )
    return user

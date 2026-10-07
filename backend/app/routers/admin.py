from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.crud import users
from app.database import get_db
from app.deps import require_admin
from app.models import User
from app.schemas.admin import AdminUserOut, AdminUserUpdate
from app.schemas.auth import UserOut

router = APIRouter(prefix="/api/admin", tags=["admin"])

Db = Annotated[Session, Depends(get_db)]
Admin = Annotated[User, Depends(require_admin)]


def to_admin_user(user: User, month_used: int, session_count: int) -> AdminUserOut:
    return AdminUserOut(
        **UserOut.model_validate(user).model_dump(),
        month_used=month_used,
        session_count=session_count,
    )


@router.get("/users", response_model=list[AdminUserOut])
def list_users(db: Db, admin: Admin):
    return [to_admin_user(*row) for row in users.list_with_stats(db)]


@router.patch("/users/{user_id}", response_model=AdminUserOut)
def update_user(user_id: int, body: AdminUserUpdate, db: Db, admin: Admin):
    user = users.get(db, user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail={"code": "NOT_FOUND", "message": "사용자를 찾을 수 없습니다."},
        )
    fields = body.model_dump(exclude_unset=True, exclude_none=True)
    if user.id == admin.id and (fields.get("is_active") is False or fields.get("role") == "user"):
        raise HTTPException(
            status_code=400,
            detail={
                "code": "SELF_MODIFY",
                "message": "자기 계정은 비활성화하거나 권한을 낮출 수 없습니다.",
            },
        )
    users.update(db, user, fields)
    return to_admin_user(*users.get_with_stats(db, user_id))

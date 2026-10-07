from sqlalchemy import select

from app.models import User


def test_user_defaults(db):
    db.add(User(username="alice", password_hash="hash"))
    db.commit()

    user = db.scalar(select(User).where(User.username == "alice"))
    assert user.role == "user"
    assert user.is_active is True
    assert user.token_limit == 100000
    assert user.created_at is not None

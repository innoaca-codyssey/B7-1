import pytest

from app.crud import users


def test_create_duplicate_username(db):
    users.create(db, "alice", "hash")
    with pytest.raises(users.UsernameTakenError):
        users.create(db, "alice", "hash")

    assert users.create(db, "bob", "hash").id

from app.security import hash_password, verify_password


def test_verify_password_over_72_bytes():
    password_hash = hash_password("password1")
    assert verify_password("password1", password_hash)
    assert not verify_password("가" * 30, password_hash)

from sqlalchemy import text

from app.database import engine, upgrade_users_table


def test_upgrade_users_table_to_existing_table(db):
    with engine.begin() as conn:
        conn.execute(
            text(
                "ALTER TABLE users DROP COLUMN display_name, DROP COLUMN email, "
                "DROP COLUMN email_verified_at"
            )
        )
        conn.execute(
            text(
                "INSERT INTO users (username, password_hash, role, is_active, token_limit) "
                "VALUES ('alice', 'hash', 'user', true, 100000)"
            )
        )

    for _ in range(2):
        with engine.begin() as conn:
            upgrade_users_table(conn)

    with engine.connect() as conn:
        row = conn.execute(text("SELECT display_name, email, email_verified_at FROM users")).one()
        assert row.display_name == "alice"
        assert row.email is None
        assert row.email_verified_at is not None
        nullable = conn.scalar(
            text(
                "SELECT is_nullable FROM information_schema.columns "
                "WHERE table_name = 'users' AND column_name = 'display_name'"
            )
        )
    assert nullable == "NO"

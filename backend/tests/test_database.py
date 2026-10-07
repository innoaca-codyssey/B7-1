from sqlalchemy import text

from app.database import add_display_name_column, engine


def test_add_display_name_column_to_existing_table(db):
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE users DROP COLUMN display_name"))
        conn.execute(
            text(
                "INSERT INTO users (username, password_hash, role, is_active, token_limit) "
                "VALUES ('alice', 'hash', 'user', true, 100000)"
            )
        )

    for _ in range(2):
        with engine.begin() as conn:
            add_display_name_column(conn)

    with engine.connect() as conn:
        assert conn.scalar(text("SELECT display_name FROM users")) == "alice"
        nullable = conn.scalar(
            text(
                "SELECT is_nullable FROM information_schema.columns "
                "WHERE table_name = 'users' AND column_name = 'display_name'"
            )
        )
    assert nullable == "NO"

from sqlalchemy import Connection, create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def upgrade_users_table(conn: Connection) -> None:
    columns = dict(
        conn.execute(
            text(
                "SELECT column_name, is_nullable FROM information_schema.columns "
                "WHERE table_name = 'users'"
            )
        ).all()
    )
    if columns.get("display_name") != "NO":
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS display_name VARCHAR(30)"))
        conn.execute(text("UPDATE users SET display_name = username WHERE display_name IS NULL"))
        conn.execute(text("ALTER TABLE users ALTER COLUMN display_name SET NOT NULL"))
    if "email" not in columns:
        conn.execute(text("ALTER TABLE users ADD COLUMN email VARCHAR(254) UNIQUE"))
    if "email_verified_at" not in columns:
        conn.execute(text("ALTER TABLE users ADD COLUMN email_verified_at TIMESTAMPTZ"))
        conn.execute(text("UPDATE users SET email_verified_at = now()"))

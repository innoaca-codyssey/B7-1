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


def add_display_name_column(conn: Connection) -> None:
    nullable = conn.scalar(
        text(
            "SELECT is_nullable FROM information_schema.columns "
            "WHERE table_name = 'users' AND column_name = 'display_name'"
        )
    )
    if nullable == "NO":
        return
    conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS display_name VARCHAR(30)"))
    conn.execute(text("UPDATE users SET display_name = username WHERE display_name IS NULL"))
    conn.execute(text("ALTER TABLE users ALTER COLUMN display_name SET NOT NULL"))

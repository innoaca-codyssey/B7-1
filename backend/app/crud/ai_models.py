from decimal import Decimal

from sqlalchemy import select
from sqlalchemy import update as sa_update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models import AIModel

DEFAULT_MODELS = [
    ("gemini-3-flash", "Gemini 3 Flash", "google", Decimal("0.5")),
    ("gemini-3.1-flash-lite", "Gemini 3.1 Flash Lite", "google", Decimal("0.5")),
    ("gemini-3.1-pro", "Gemini 3.1 Pro", "google", Decimal("1.5")),
    ("claude-haiku-4", "Claude Haiku 4.5", "anthropic", Decimal("0.5")),
    ("claude-sonnet-4", "Claude Sonnet 4.6", "anthropic", Decimal("1.0")),
    ("gpt-5-mini", "GPT-5 Mini", "openai", Decimal("0.5")),
    ("claude-opus-4-7", "Claude Opus 4.7", "anthropic", Decimal("1.5")),
    ("claude-opus-4-8", "Claude Opus 4.8", "anthropic", Decimal("1.5")),
    ("gpt-5.5", "GPT-5.5", "openai", Decimal("2.0")),
    ("gpt-5.4", "GPT-5.4", "openai", Decimal("1.0")),
    ("gpt-5.4-mini", "GPT-5.4 mini", "openai", Decimal("0.5")),
]
DEFAULT_MODEL_CODE = "gpt-5-mini"


def seed_defaults(db: Session) -> None:
    rows = [
        {
            "code": code,
            "name": name,
            "provider": provider,
            "multiplier": multiplier,
            "is_default": code == DEFAULT_MODEL_CODE,
            "sort_order": i,
        }
        for i, (code, name, provider, multiplier) in enumerate(DEFAULT_MODELS)
    ]
    db.execute(insert(AIModel).values(rows).on_conflict_do_nothing(index_elements=["code"]))
    db.commit()


def list_active(db: Session) -> list[AIModel]:
    return list(db.scalars(select(AIModel).where(AIModel.is_active).order_by(AIModel.sort_order)))


def get_active(db: Session, code: str | None) -> AIModel | None:
    stmt = select(AIModel).where(AIModel.is_active)
    stmt = stmt.where(AIModel.code == code) if code else stmt.where(AIModel.is_default)
    return db.scalar(stmt)


def list_all(db: Session) -> list[AIModel]:
    return list(db.scalars(select(AIModel).order_by(AIModel.sort_order)))


def get_by_code(db: Session, code: str) -> AIModel | None:
    return db.scalar(select(AIModel).where(AIModel.code == code))


def update(db: Session, model: AIModel, fields: dict) -> AIModel:
    if fields.get("is_default"):
        db.execute(
            sa_update(AIModel)
            .where(AIModel.is_default, AIModel.id != model.id)
            .values(is_default=False)
        )
    for key, value in fields.items():
        setattr(model, key, value)
    db.commit()
    db.refresh(model)
    return model

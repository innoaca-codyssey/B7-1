import threading

import pytest
from sqlalchemy.exc import IntegrityError

from app.crud import ai_models
from app.database import SessionLocal
from app.models import AIModel


@pytest.fixture
def seeded(db):
    ai_models.seed_defaults(db)
    return db


def default_codes(db):
    db.expire_all()
    return [m.code for m in db.query(AIModel).filter_by(is_default=True)]


def test_concurrent_default_change_waits_for_lock(seeded):
    first = SessionLocal()
    second = SessionLocal()
    try:
        first.query(AIModel).filter_by(is_default=True).with_for_update().all()
        first.query(AIModel).filter_by(is_default=True).update({"is_default": False})
        first.query(AIModel).filter_by(code="gpt-5.4").update({"is_default": True})

        errors = []

        def change():
            try:
                model = ai_models.get_by_code(second, "gpt-5.5")
                ai_models.update(second, model, {"is_default": True})
            except Exception as e:
                errors.append(e)

        thread = threading.Thread(target=change)
        thread.start()
        thread.join(1)
        assert thread.is_alive()

        first.commit()
        thread.join(5)
        assert errors == []
    finally:
        first.close()
        second.close()

    assert default_codes(seeded) == ["gpt-5.5"]


def test_default_conflict_rolls_back(seeded, monkeypatch):
    model = ai_models.get_by_code(seeded, "gpt-5.4")

    def failing_commit():
        raise IntegrityError("UPDATE", {}, Exception("uq_ai_models_default"))

    monkeypatch.setattr(seeded, "commit", failing_commit)
    with pytest.raises(ai_models.DefaultModelConflictError):
        ai_models.update(seeded, model, {"is_default": True})
    monkeypatch.undo()

    assert default_codes(seeded) == ["gpt-5-mini"]

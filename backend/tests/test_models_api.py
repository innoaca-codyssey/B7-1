from app.crud import ai_models
from app.models import AIModel


def test_list_models(client, db):
    gemini = db.query(AIModel).filter_by(code="gemini-3-flash").one()
    gemini.is_active = False
    db.commit()

    res = client.get("/api/models")
    assert res.status_code == 200
    body = res.json()
    codes = [m["code"] for m in body]
    assert len(codes) == 10
    assert "gemini-3-flash" not in codes
    assert codes[0] == "gemini-3.1-flash-lite"
    default = next(m for m in body if m["is_default"])
    assert default == {
        "code": "gpt-5-mini",
        "name": "GPT-5 Mini",
        "provider": "openai",
        "multiplier": 0.5,
        "is_default": True,
    }


def test_seed_keeps_admin_changes(client, db):
    model = db.query(AIModel).filter_by(code="gpt-5.5").one()
    model.multiplier = 3
    model.is_active = False
    db.commit()

    ai_models.seed_defaults(db)

    db.refresh(model)
    assert model.multiplier == 3
    assert model.is_active is False
    assert db.query(AIModel).count() == 11


def test_list_presets(client):
    res = client.get("/api/presets")
    assert res.status_code == 200
    body = res.json()
    assert [p["code"] for p in body] == ["tutor", "code_review", "debug", "concept"]
    assert all("system_prompt" not in p for p in body)

"""Flexible planner + slot-filling (stubbed plan, deterministic)."""
from app import conversation, planner, tasking
from app.registry import JsonRegistry

PHONE = "+15555550123"


def _reg(tmp_path):
    return JsonRegistry(tmp_path / "owners.json")


def _verified(reg):
    conversation.handle(PHONE, "CLAIM", reg)
    conversation.handle(PHONE, "Budgetbot", reg)
    conversation.handle(PHONE, "budget 1000", reg)


def _enable(monkeypatch, plan_fn):
    monkeypatch.setattr(tasking, "planner_enabled", lambda: True)
    monkeypatch.setattr(planner, "plan", plan_fn)


def test_slot_filling_asks_then_charges(tmp_path, monkeypatch):
    reg = _reg(tmp_path); _verified(reg)
    def fake(text, pending, allow, budget):
        if "furnish" in text.lower():
            return {"intent": "purchase", "goal": None,
                    "items": [{"name": "office sofa", "amount_cents": None, "vendor": None}],
                    "question": "What's the price, and Acme or Staples?"}
        return {"intent": "purchase", "goal": None,
                "items": [{"name": "office sofa", "amount_cents": 40000, "vendor": "Acme"}], "question": None}
    _enable(monkeypatch, fake)
    r1 = conversation.handle(PHONE, "buy office furnishings", reg)
    assert "price" in r1.lower()
    assert reg.get_by_phone(PHONE).pending_task is not None       # remembered
    r2 = conversation.handle(PHONE, "$400 from Acme", reg)
    assert "Bought" in r2 and "office sofa" in r2
    assert reg.get_by_phone(PHONE).pending_task is None           # cleared after charge


def test_settings_intent_stays_deterministic(tmp_path, monkeypatch):
    reg = _reg(tmp_path); _verified(reg)
    _enable(monkeypatch, lambda *a: {"intent": "settings", "goal": None, "items": [], "question": None})
    r = conversation.handle(PHONE, "can you bump my spending limit a bit", reg)
    assert "budget" in r.lower()  # hint to the deterministic command; not LLM-applied


def test_cancel_clears_pending(tmp_path, monkeypatch):
    reg = _reg(tmp_path); _verified(reg)
    seq = iter([
        {"intent": "purchase", "goal": None, "items": [{"name": "sofa", "amount_cents": None, "vendor": None}], "question": "price?"},
        {"intent": "cancel", "goal": None, "items": [], "question": None},
    ])
    _enable(monkeypatch, lambda *a: next(seq))
    conversation.handle(PHONE, "buy a sofa", reg)
    assert reg.get_by_phone(PHONE).pending_task is not None
    r = conversation.handle(PHONE, "never mind", reg)
    assert "cancel" in r.lower() and reg.get_by_phone(PHONE).pending_task is None


def test_smalltalk_routes_to_welcome(tmp_path, monkeypatch):
    reg = _reg(tmp_path); _verified(reg)
    _enable(monkeypatch, lambda *a: {"intent": "smalltalk", "goal": None, "items": [], "question": None})
    r = conversation.handle(PHONE, "what can you do for me", reg)
    assert "Budgetbot" in r


def test_offline_fallback_unchanged(tmp_path):
    # planner disabled (no Nebius) -> deterministic path still rejects vague input
    reg = _reg(tmp_path); _verified(reg)
    r = conversation.handle(PHONE, "buy office furnishings", reg)
    assert "🤔" in r

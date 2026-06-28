"""Intent Check (Epic 3) — catalog parse, multi-item loop, grounding halt.

Grounding is stubbed so the centerpiece is deterministic and can't flake (NFR008).
"""
from app import catalog, conversation, grounding
from app.registry import JsonRegistry

PHONE = "+15555550123"


def _reg(tmp_path):
    return JsonRegistry(tmp_path / "owners.json")


def _verified(reg):
    conversation.handle(PHONE, "CLAIM", reg)
    conversation.handle(PHONE, "Budgetbot", reg)
    conversation.handle(PHONE, "budget 400", reg)
    conversation.handle(PHONE, "allow Acme, Staples", reg)


def _stub_grounding(monkeypatch, off=("espresso machine", "chair", "coffee")):
    def fake(goal, item):
        low = item.lower()
        if any(o in low for o in off):
            return False, f"{item} not part of {goal}"
        return True, ""
    monkeypatch.setattr(grounding, "check", fake)


# --- catalog units ---
def test_catalog_scan_order_and_vendors():
    items = catalog.scan("Set up the desk: keyboard, mouse, monitor from Acme and Staples")
    assert [(i.description, i.amount_cents, i.vendor) for i in items] == [
        ("keyboard", 4000, "Acme"), ("mouse", 2500, "Acme"), ("monitor", 30000, "Staples")]


def test_explicit_price_overrides_catalog():
    items = catalog.scan("espresso machine $250 from Acme")
    assert items[0].amount_cents == 25000 and items[0].vendor == "Acme"


def test_extract_goal():
    assert catalog.extract_goal("Set up the new hire's desk: keyboard") == "Set up the new hire's desk"
    assert catalog.extract_goal("buy a keyboard") is None


# --- multi-item flow ---
def test_all_conform_charges_all_and_sets_goal(tmp_path, monkeypatch):
    _stub_grounding(monkeypatch)
    reg = _reg(tmp_path); _verified(reg)
    reply = conversation.handle(PHONE, "Set up the new hire's desk: keyboard, mouse, monitor", reg)
    assert "keyboard" in reply and "mouse" in reply and "monitor" in reply
    assert reg.get_by_phone(PHONE).active_goal == "Set up the new hire's desk"


def test_injected_espresso_halts_on_intent_drift(tmp_path, monkeypatch):
    _stub_grounding(monkeypatch)
    reg = _reg(tmp_path); _verified(reg)
    conversation.handle(PHONE, "Set up the new hire's desk: keyboard, mouse, monitor", reg)
    reply = conversation.handle(PHONE, "espresso machine $250 from Acme", reg)
    assert "🛑" in reply and "espresso machine" in reply and "Didn't charge" in reply


def test_gate_halts_before_grounding(tmp_path, monkeypatch):
    _stub_grounding(monkeypatch)
    reg = _reg(tmp_path)
    conversation.handle(PHONE, "CLAIM", reg)
    conversation.handle(PHONE, "Budgetbot", reg)   # default $50 budget
    reply = conversation.handle(PHONE, "buy a chair", reg)   # $500 > $50
    assert "🛑" in reply and "budget" in reply.lower()


def test_single_catalog_item_no_goal_charges(tmp_path, monkeypatch):
    _stub_grounding(monkeypatch)
    reg = _reg(tmp_path); _verified(reg)
    reply = conversation.handle(PHONE, "buy a keyboard", reg)
    assert "Bought" in reply and "keyboard" in reply

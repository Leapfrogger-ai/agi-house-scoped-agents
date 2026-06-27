"""End-to-end conversation flow against the JSON registry, no external services
(Stories 1.3, 1.4, 1.6 + the simulated delegate path)."""
from app import conversation
from app.registry import AWAITING_NAME, READY, JsonRegistry


def _reg(tmp_path):
    return JsonRegistry(tmp_path / "owners.json")


PHONE = "+15555550123"


def test_first_text_starts_claim(tmp_path):
    reg = _reg(tmp_path)
    reply = conversation.handle(PHONE, "CLAIM", reg)
    assert "claiming" in reply.lower()
    assert reg.get_by_phone(PHONE).state == AWAITING_NAME


def test_second_inbound_verifies_owner(tmp_path):
    reg = _reg(tmp_path)
    conversation.handle(PHONE, "CLAIM", reg)
    reply = conversation.handle(PHONE, "Budgetbot", reg)
    rec = reg.get_by_phone(PHONE)
    assert rec.verified and rec.state == READY and rec.name == "Budgetbot"
    assert "Budgetbot" in reply


def test_single_inbound_stays_unverified(tmp_path):
    reg = _reg(tmp_path)
    conversation.handle(PHONE, "CLAIM", reg)
    assert reg.get_by_phone(PHONE).verified is False


def test_blank_name_reprompts(tmp_path):
    reg = _reg(tmp_path)
    conversation.handle(PHONE, "CLAIM", reg)
    reply = conversation.handle(PHONE, "🙂", reg)
    assert "name" in reply.lower()
    assert reg.get_by_phone(PHONE).state == AWAITING_NAME


def _verified(reg):
    conversation.handle(PHONE, "CLAIM", reg)
    conversation.handle(PHONE, "Budgetbot", reg)


def test_happy_path_charge_simulated(tmp_path):
    reg = _reg(tmp_path)
    _verified(reg)
    reply = conversation.handle(PHONE, "buy office supplies, $30 from Acme", reg)
    assert "Paid" in reply and "Acme" in reply and "30.00" in reply


def test_over_budget_denied(tmp_path):
    reg = _reg(tmp_path)
    _verified(reg)
    reply = conversation.handle(PHONE, "buy $80 of supplies from Acme", reg)
    assert "🛑" in reply and "budget" in reply.lower()


def test_off_allowlist_denied(tmp_path):
    reg = _reg(tmp_path)
    _verified(reg)
    reply = conversation.handle(PHONE, "pay EvilCorp $20", reg)
    assert "🛑" in reply and "EvilCorp" in reply


def test_returning_owner_greeted_by_name(tmp_path):
    reg = _reg(tmp_path)
    _verified(reg)
    reply = conversation.handle(PHONE, "hey", reg)
    assert "Welcome back" in reply and "Budgetbot" in reply


def test_bad_task_reprompts(tmp_path):
    reg = _reg(tmp_path)
    _verified(reg)
    reply = conversation.handle(PHONE, "buy some stuff", reg)
    assert "🤔" in reply


def test_budget_command_changes_enforcement(tmp_path):
    reg = _reg(tmp_path)
    _verified(reg)
    # default $50 budget denies $80
    assert "🛑" in conversation.handle(PHONE, "buy $80 from Acme", reg)
    # raise budget, then the same task is allowed
    assert "Budget set to *$100*" in conversation.handle(PHONE, "budget 100", reg)
    assert reg.get_by_phone(PHONE).budget_cents == 10000
    assert "Paid" in conversation.handle(PHONE, "buy $80 from Acme", reg)


def test_allow_command_changes_enforcement(tmp_path):
    reg = _reg(tmp_path)
    _verified(reg)
    assert "🛑" in conversation.handle(PHONE, "buy $20 from Staples", reg)
    reply = conversation.handle(PHONE, "allow Acme, Staples", reg)
    assert "Staples" in reply and reg.get_by_phone(PHONE).vendor_allowlist == ["Acme", "Staples"]
    assert "Paid" in conversation.handle(PHONE, "buy $20 from Staples", reg)


def test_view_only_commands(tmp_path):
    reg = _reg(tmp_path)
    _verified(reg)
    assert "$50" in conversation.handle(PHONE, "budget", reg)
    assert "Acme" in conversation.handle(PHONE, "allow", reg)

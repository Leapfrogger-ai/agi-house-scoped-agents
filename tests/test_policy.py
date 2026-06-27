"""Policy-gate unit cases (Story 2.3) — the one place correctness MUST be guaranteed.

These are the deterministic containment guarantees the live demo relies on (NFR003).
"""
from app.manifest import IntentManifest
from app.policy import evaluate


def _m(amount_cents: int, vendor: str = "Acme", budget_cents: int = 5000) -> IntentManifest:
    return IntentManifest(
        owner_phone="hash",
        task="t",
        amount_cents=amount_cents,
        vendor=vendor,
        budget_cents=budget_cents,
        vendor_allowlist=["Acme"],
    )


def test_in_budget_allowed_vendor_allows():
    v = evaluate(_m(3000))
    assert v.allowed and v.reason == ""


def test_over_budget_denies():
    v = evaluate(_m(8000))
    assert not v.allowed and v.reason == "over-budget"


def test_off_allowlist_denies():
    v = evaluate(_m(2000, vendor="EvilCorp"))
    assert not v.allowed and v.reason == "off-allowlist"


def test_exactly_at_budget_allows():
    v = evaluate(_m(5000))
    assert v.allowed


def test_allowlist_is_case_insensitive():
    assert evaluate(_m(2000, vendor="acme")).allowed


def test_deterministic_repeat():
    m = _m(8000)
    assert evaluate(m).reason == evaluate(m).reason == "over-budget"


def test_budget_checked_before_allowlist():
    # over-budget AND off-allowlist -> budget reason wins (stable ordering)
    v = evaluate(_m(9000, vendor="EvilCorp"))
    assert v.reason == "over-budget"

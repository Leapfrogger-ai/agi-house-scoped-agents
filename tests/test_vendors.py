"""Vendor roster routing (Connect mode) — pure logic, testable without Connect enabled."""
from app.vendors import load_roster, resolve

ROSTER = {"Acme": "acct_acme", "Staples": "acct_staples"}


def test_resolve_exact():
    assert resolve("Acme", ROSTER) == "acct_acme"


def test_resolve_case_insensitive():
    assert resolve("acme", ROSTER) == "acct_acme"
    assert resolve("  STAPLES ", ROSTER) == "acct_staples"


def test_resolve_missing_is_none():
    assert resolve("Globex", ROSTER) is None


def test_load_roster_parses_json():
    assert load_roster('{"Acme":"acct_1"}') == {"Acme": "acct_1"}


def test_load_roster_bad_input_is_empty():
    assert load_roster("not json") == {}
    assert load_roster(None) == {}

"""Settings parser units (Story 1.7). Deterministic, no LLM."""
import pytest

from app.settings import (
    SetAllow,
    SetBudget,
    SettingsError,
    ShowAllow,
    ShowBudget,
    parse_money,
    parse_settings_command,
)


def test_set_budget():
    assert parse_settings_command("budget 100") == SetBudget(10000)


def test_set_budget_with_dollar_and_commas():
    assert parse_settings_command("budget $1,200") == SetBudget(120000)


def test_show_budget():
    assert isinstance(parse_settings_command("budget"), ShowBudget)


def test_bad_budget_raises_hint():
    with pytest.raises(SettingsError):
        parse_settings_command("budget abc")


def test_set_allow():
    assert parse_settings_command("allow Acme, Staples") == SetAllow(["Acme", "Staples"])


def test_show_allow():
    assert isinstance(parse_settings_command("allow"), ShowAllow)


def test_allow_only_commas_raises():
    with pytest.raises(SettingsError):
        parse_settings_command("allow , ,")


def test_task_is_not_a_command():
    assert parse_settings_command("buy $30 from Acme") is None


def test_parse_money_rejects_nonpositive():
    with pytest.raises(ValueError):
        parse_money("0")

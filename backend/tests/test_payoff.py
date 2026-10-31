"""Debt payoff planner: the math, the strategies, and the edge cases."""
import pytest

from app.providers.demo import DemoProvider
from app.schemas import CreditCard
from app.services.payoff import MAX_MONTHS, Debt, compare, debts_from_cards, simulate


def card(name: str, balance: float, apr: float | None, minimum: float | None) -> CreditCard:
    return CreditCard(account_id=name, name=name, balance=balance, limit=None, utilization_pct=None, apr=apr,
                      minimum_payment=minimum, next_due_date=None)


def test_zero_apr_is_simple_division():
    plan = simulate([Debt(name="A", balance=1000, apr=0, minimum=100)], "avalanche")
    assert plan.feasible and plan.months == 10 and plan.total_interest == 0 and plan.total_paid == 1000
    assert plan.balance_by_month[0] == 1000 and plan.balance_by_month[-1] == 0
    assert plan.balance_by_card["A"] == plan.balance_by_month  # one card: per-card history equals the total


def test_matches_standard_amortization():
    # $1,000 at 1%/month paying $100: after 10 payments $58.40 is left, plus 1% interest = a final $58.98
    # payment in month 11. Total interest = 1058.98 - 1000 = $58.98.
    plan = simulate([Debt(name="A", balance=1000, apr=12, minimum=100)], "avalanche")
    assert plan.months == 11
    assert plan.total_interest == pytest.approx(58.98, abs=0.01)
    assert plan.total_paid == pytest.approx(1000 + plan.total_interest, abs=0.01)


def test_strategies_pick_different_targets():
    debts = [Debt(name="Big high-rate", balance=3000, apr=29, minimum=60),
             Debt(name="Small low-rate", balance=400, apr=9, minimum=25)]
    av, sb = simulate(debts, "avalanche", 200), simulate(debts, "snowball", 200)
    assert sb.order[0].name == "Small low-rate"  # snowball: smallest balance first
    assert av.total_interest < sb.total_interest  # avalanche: least interest
    assert av.monthly_payment == sb.monthly_payment == 285  # same budget both ways: minimums + extra


def test_extra_payment_finishes_sooner_and_cheaper():
    debts = [Debt(name="A", balance=2000, apr=22, minimum=50)]
    base, extra = simulate(debts, "avalanche"), simulate(debts, "avalanche", 150)
    assert extra.months < base.months and extra.total_interest < base.total_interest


def test_payment_below_interest_never_pays_off():
    plan = simulate([Debt(name="A", balance=10_000, apr=30, minimum=100)], "avalanche")  # $250/mo interest
    assert not plan.feasible and plan.months == MAX_MONTHS


def test_negative_extra_rejected():
    with pytest.raises(ValueError):
        simulate([Debt(name="A", balance=100, apr=0, minimum=10)], "avalanche", -5)


def test_missing_bank_fields_are_assumed_and_disclosed():
    debts = debts_from_cards([card("No info", 2000, None, None), card("Paid off", 0, 20, 25)])
    assert len(debts) == 1  # zero-balance cards are skipped
    assert debts[0].apr == 0 and debts[0].minimum == 40 and set(debts[0].assumed) == {"apr", "minimum"}
    result = compare([card("No info", 2000, None, None)])
    assert any("didn't report an APR" in a for a in result.assumptions)


def test_no_card_debt_returns_none():
    assert compare([]) is None


def test_minimums_only_explains_that_extra_money_is_what_differs():
    result = compare(DemoProvider().get_credit_cards(), extra_per_month=0)
    assert result.avalanche.total_interest == result.snowball.total_interest
    assert "add an extra amount" in result.recommendation


def test_demo_cards_recommend_avalanche():
    result = compare(DemoProvider().get_credit_cards(), extra_per_month=100)
    assert result.avalanche.feasible and result.avalanche.order[0].name == "Cash Back Visa"  # 24.99% APR
    assert result.snowball.order[0].name == "Student Mastercard"  # smaller balance
    assert result.interest_saved_by_avalanche > 0 and "Avalanche saves" in result.recommendation


def test_penny_tool_returns_plan_without_chart_data():
    import json

    from app.ai.tools import run_tool

    out = json.loads(run_tool("get_payoff_plan", {"extra_per_month": 100}, DemoProvider()))
    assert out["avalanche"]["order"][0]["name"] == "Cash Back Visa"
    assert "balance_by_month" not in out["avalanche"] and "balance_by_card" not in out["avalanche"] and out["interest_saved_by_avalanche"] > 0

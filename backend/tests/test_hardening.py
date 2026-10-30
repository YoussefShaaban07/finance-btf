"""Tests for the backend hardening: multi-bank Plaid cards, session handling, and the tool registry."""
import json
from types import SimpleNamespace
from typing import ClassVar

import pytest

from app.ai import tools
from app.db import SavingsGoal, init_db, session_scope
from app.providers.demo import DemoProvider
from app.providers.plaid_provider import PlaidProvider


class _Resp(dict):
    def to_dict(self) -> dict:
        return dict(self)


def _account(acct_id: str, balance: float, limit: float) -> dict:
    return {"account_id": acct_id, "name": acct_id, "official_name": None, "type": "credit", "subtype": "credit card",
            "balances": {"current": balance, "limit": limit}}


class FakePlaidClient:
    """Two banks, one card each. Each bank only knows the liability details for its own card."""

    accounts: ClassVar[dict] = {"tok_a": [_account("card_a", 500, 1000)], "tok_b": [_account("card_b", 200, 2000)]}
    liabilities: ClassVar[dict] = {
        "tok_a": [{"account_id": "card_a", "aprs": [{"apr_type": "purchase_apr", "apr_percentage": 24.0}],
                   "minimum_payment_amount": 35.0, "next_payment_due_date": None}],
        "tok_b": [{"account_id": "card_b", "aprs": [{"apr_type": "purchase_apr", "apr_percentage": 19.0}],
                   "minimum_payment_amount": 25.0, "next_payment_due_date": None}],
    }

    def accounts_balance_get(self, req):
        return _Resp(accounts=self.accounts[req.access_token])

    def liabilities_get(self, req):
        return _Resp(liabilities={"credit": self.liabilities[req.access_token]})


def _plaid_provider_with_two_banks() -> PlaidProvider:
    p = PlaidProvider.__new__(PlaidProvider)  # skip __init__: no real Plaid client or encrypted tokens needed
    p.client = FakePlaidClient()
    p.items = [("Bank A", "tok_a"), ("Bank B", "tok_b")]
    return p


def test_credit_cards_keep_details_from_every_bank():
    cards = {c.account_id: c for c in _plaid_provider_with_two_banks().get_credit_cards()}
    assert set(cards) == {"card_a", "card_b"}
    assert cards["card_a"].apr == 24.0 and cards["card_a"].minimum_payment == 35.0
    assert cards["card_b"].apr == 19.0 and cards["card_b"].minimum_payment == 25.0
    assert cards["card_a"].utilization_pct == 50.0


def test_session_scope_rolls_back_on_error():
    init_db()
    with pytest.raises(RuntimeError), session_scope() as db:
        db.add(SavingsGoal(user_id="rollback-test", name="x", target=1, target_date=__import__("datetime").date.today()))
        db.flush()
        raise RuntimeError("boom")
    with session_scope() as db:
        assert db.query(SavingsGoal).filter_by(user_id="rollback-test").count() == 0


def test_every_tool_schema_has_a_handler():
    assert {t["name"] for t in tools.TOOL_SCHEMAS} == set(tools.HANDLERS)


def test_unknown_tool_returns_error_not_exception():
    assert "unknown tool" in json.loads(tools.run_tool("transfer_money", {}, DemoProvider()))["error"]


def test_tool_errors_are_returned_to_the_model():
    broken = SimpleNamespace(get_accounts=lambda: (_ for _ in ()).throw(ConnectionError("bank offline")), is_demo=False)
    out = json.loads(tools.run_tool("get_accounts", {}, broken))
    assert out["error"].startswith("ConnectionError")

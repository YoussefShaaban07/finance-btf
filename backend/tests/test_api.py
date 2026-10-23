import os
from types import SimpleNamespace

os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ["PLAID_CLIENT_ID"] = ""
os.environ["PLAID_SECRET"] = ""
os.environ["FINNHUB_API_KEY"] = ""

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.ai.chat import chat  # noqa: E402
from app.main import app  # noqa: E402
from app.providers.demo import DemoProvider  # noqa: E402
from app.schemas import Account, ChatMessage, Transaction  # noqa: E402
from app.services.finance import compute_net_worth, spending_summary  # noqa: E402


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_health_demo_mode(client):
    assert client.get("/health").json()["demo_mode"] is True


def test_net_worth_math():
    nw = compute_net_worth([
        Account(id="a", name="chk", type="depository", balance=1000),
        Account(id="b", name="cc", type="credit", balance=250),
        Account(id="c", name="ira", type="investment", balance=500),
        Account(id="d", name="car", type="loan", balance=400),
    ])
    assert (nw.assets, nw.liabilities, nw.net_worth) == (1500, 650, 850)


def test_spending_ignores_transfers():
    from datetime import date
    t = lambda amt, cat: Transaction(id=cat + str(amt), date=date.today(), name="x", amount=amt, category=cat, account_id="a")  # noqa: E731
    s = spending_summary([t(-1000, "INCOME"), t(50, "FOOD_AND_DRINK"), t(300, "TRANSFER_OUT")])
    assert s["income"] == 1000 and s["spent"] == 50 and "TRANSFER_OUT" not in s["by_category"]


def test_finance_endpoints(client):
    for path in ["/accounts", "/networth", "/credit-cards", "/holdings", "/transactions?days=14", "/spending"]:
        r = client.get(path)
        assert r.status_code == 200, path
    cards = client.get("/credit-cards").json()
    assert all(0 <= c["utilization_pct"] <= 100 for c in cards)


def test_snapshot_history(client):
    client.post("/networth/snapshot", headers={"X-User-Id": "u1"})
    assert len(client.get("/networth/history", headers={"X-User-Id": "u1"}).json()) >= 1


def test_market_demo(client):
    q = client.get("/market/quote/nvda").json()
    assert q["symbol"] == "NVDA" and q["price"] > 0
    assert len(client.get("/market/quotes?symbols=AAPL,VTI").json()) == 2


def test_plaid_disabled_in_demo(client):
    assert client.post("/plaid/link-token").status_code == 400


# ---- chatbot tool loop with a fake LLM (no API key needed) ----

class FakeLLM:
    """Round 1: asks for net worth. Round 2: answers using the tool result it received."""

    def __init__(self):
        self.calls = []
        self.messages = SimpleNamespace(create=self._create)

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        if len(self.calls) == 1:
            return SimpleNamespace(stop_reason="tool_use", content=[
                SimpleNamespace(type="tool_use", id="t1", name="get_net_worth", input={})])
        tool_result = kwargs["messages"][-1]["content"][0]["content"]
        return SimpleNamespace(stop_reason="end_turn", content=[
            SimpleNamespace(type="text", text=f"Here you go: {tool_result}")])


def test_chat_uses_tools_and_real_numbers():
    llm = FakeLLM()
    resp = chat([ChatMessage(role="user", content="what's my net worth?")], DemoProvider(), client=llm)
    assert resp.tools_used == ["get_net_worth"]
    expected = compute_net_worth(DemoProvider().get_accounts()).net_worth
    assert str(expected) in resp.reply
    assert "DEMO MODE" in llm.calls[0]["system"]


def test_chat_without_key_is_graceful(client):
    r = client.post("/chat", json={"messages": [{"role": "user", "content": "hi"}]})
    assert r.status_code == 200 and "ANTHROPIC_API_KEY" in r.json()["reply"]

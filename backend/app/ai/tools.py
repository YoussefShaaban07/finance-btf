"""Tools the chatbot can call. Each one reads the user's REAL data, so answers are grounded, not guessed."""
import json
import logging
from collections import Counter
from collections.abc import Callable
from typing import Any

from app.providers.base import FinanceProvider
from app.services import market
from app.services.alerts import card_alerts, unusual_charges
from app.services.finance import compute_net_worth, spending_summary
from app.services.subscriptions import find_subscriptions

log = logging.getLogger(__name__)

# Extra data the host app can plug in (savings goals live in our DB, not at the bank).
GoalsFn = Callable[[], list[dict]]

TOOL_SCHEMAS = [
    {
        "name": "get_net_worth",
        "description": "User's current net worth: total assets, total liabilities, and a breakdown by account type.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_accounts",
        "description": "All linked accounts (checking, savings, credit cards, investments, loans) with balances.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_credit_cards",
        "description": "Credit cards with balance, limit, utilization %, APR, minimum payment and next due date.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_spending_summary",
        "description": "Income vs. spending and spend by category over the last N days.",
        "input_schema": {
            "type": "object",
            "properties": {"days": {"type": "integer", "description": "Lookback window, default 30", "minimum": 1, "maximum": 365}},
        },
    },
    {
        "name": "get_recent_transactions",
        "description": "Recent individual transactions, optionally filtered by category (e.g. FOOD_AND_DRINK) or merchant text.",
        "input_schema": {
            "type": "object",
            "properties": {
                "days": {"type": "integer", "minimum": 1, "maximum": 365},
                "category": {"type": "string"},
                "merchant": {"type": "string"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 100},
            },
        },
    },
    {
        "name": "get_holdings",
        "description": "User's investment holdings: ticker, shares, price, value, cost basis and gain/loss.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_stock_quote",
        "description": "Live quote for any stock/ETF ticker.",
        "input_schema": {
            "type": "object",
            "properties": {"symbol": {"type": "string", "description": "Ticker, e.g. AAPL"}},
            "required": ["symbol"],
        },
    },
    {
        "name": "get_subscriptions",
        "description": "Recurring monthly charges (subscriptions, rent, bills) found in the last 90 days, with yearly cost.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_alerts",
        "description": "Current alerts: unusual charges, card payments due soon, high credit utilization.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_savings_goals",
        "description": "User's savings goals: target, amount saved, % done, and how much per month is needed.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_market_news",
        "description": "Latest general market news headlines.",
        "input_schema": {"type": "object", "properties": {"limit": {"type": "integer", "minimum": 1, "maximum": 10}}},
    },
]


ToolArgs = dict[str, Any]
ToolHandler = Callable[[ToolArgs, FinanceProvider, GoalsFn | None], Any]


def _int(args: ToolArgs, key: str, default: int) -> int:
    return int(args.get(key, default))


def _net_worth(_args: ToolArgs, p: FinanceProvider, _goals: GoalsFn | None) -> Any:
    return compute_net_worth(p.get_accounts()).model_dump()


def _accounts(_args: ToolArgs, p: FinanceProvider, _goals: GoalsFn | None) -> Any:
    return [a.model_dump() for a in p.get_accounts()]


def _credit_cards(_args: ToolArgs, p: FinanceProvider, _goals: GoalsFn | None) -> Any:
    return [c.model_dump(mode="json") for c in p.get_credit_cards()]


def _spending_summary(args: ToolArgs, p: FinanceProvider, _goals: GoalsFn | None) -> Any:
    days = _int(args, "days", 30)
    return {"days": days, **spending_summary(p.get_transactions(days))}


def _recent_transactions(args: ToolArgs, p: FinanceProvider, _goals: GoalsFn | None) -> Any:
    txns = p.get_transactions(_int(args, "days", 30))
    if cat := args.get("category"):
        txns = [t for t in txns if t.category.upper() == cat.upper()]
    if m := args.get("merchant"):
        txns = [t for t in txns if m.lower() in t.name.lower()]
    return {
        "count_matching": len(txns),
        "top_merchants": Counter(t.name for t in txns).most_common(5),
        "transactions": [t.model_dump(mode="json") for t in txns[:_int(args, "limit", 25)]],
    }


def _holdings(_args: ToolArgs, p: FinanceProvider, _goals: GoalsFn | None) -> Any:
    return [{**h.model_dump(), "gain": round(h.value - h.cost_basis, 2) if h.cost_basis else None}
            for h in p.get_holdings()]


def _stock_quote(args: ToolArgs, _p: FinanceProvider, _goals: GoalsFn | None) -> Any:
    return market.get_quote(args["symbol"]).model_dump()


def _subscriptions(_args: ToolArgs, p: FinanceProvider, _goals: GoalsFn | None) -> Any:
    subs = find_subscriptions(p.get_transactions(90))
    return {"monthly_total": round(sum(x.amount for x in subs), 2),
            "yearly_total": round(sum(x.yearly_cost for x in subs), 2),
            "subscriptions": [x.model_dump() for x in subs]}


def _alerts(_args: ToolArgs, p: FinanceProvider, _goals: GoalsFn | None) -> Any:
    alerts = unusual_charges(p.get_transactions(30)) + card_alerts(p.get_credit_cards())
    return [a.model_dump() for a in alerts] or {"message": "No alerts right now."}


def _savings_goals(_args: ToolArgs, _p: FinanceProvider, goals_fn: GoalsFn | None) -> Any:
    goals = goals_fn() if goals_fn else None
    return goals or {"message": "The user hasn't set any savings goals yet."}


def _market_news(args: ToolArgs, _p: FinanceProvider, _goals: GoalsFn | None) -> Any:
    return [n.model_dump() for n in market.get_news(_int(args, "limit", 5))]


HANDLERS: dict[str, ToolHandler] = {
    "get_net_worth": _net_worth,
    "get_accounts": _accounts,
    "get_credit_cards": _credit_cards,
    "get_spending_summary": _spending_summary,
    "get_recent_transactions": _recent_transactions,
    "get_holdings": _holdings,
    "get_stock_quote": _stock_quote,
    "get_subscriptions": _subscriptions,
    "get_alerts": _alerts,
    "get_savings_goals": _savings_goals,
    "get_market_news": _market_news,
}

# Fail at import, not mid-conversation, if a tool is advertised to the model without a handler (or vice versa).
_missing = {t["name"] for t in TOOL_SCHEMAS} ^ set(HANDLERS)
if _missing:
    raise RuntimeError(f"Tool schemas and handlers are out of sync: {sorted(_missing)}")


def run_tool(name: str, args: ToolArgs, provider: FinanceProvider, goals_fn: GoalsFn | None = None) -> str:
    """Execute a tool and return JSON text for the model. Errors are returned, not raised, so the model can recover."""
    handler = HANDLERS.get(name)
    if handler is None:
        return json.dumps({"error": f"unknown tool {name}"})
    try:
        result = handler(args, provider, goals_fn)
    except Exception as e:
        log.warning("Tool %s failed", name, exc_info=True)
        result = {"error": f"{type(e).__name__}: {e}"}
    return json.dumps(result, default=str)

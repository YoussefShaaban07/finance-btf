"""Tools the chatbot can call. Each one reads the user's REAL data, so answers are grounded, not guessed."""
import json
from collections import Counter
from typing import Callable

from app.providers.base import FinanceProvider
from app.services import market
from app.services.alerts import card_alerts, unusual_charges
from app.services.finance import compute_net_worth, spending_summary
from app.services.subscriptions import find_subscriptions

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


def run_tool(name: str, args: dict, provider: FinanceProvider, goals_fn: GoalsFn | None = None) -> str:
    """Execute a tool and return JSON text for the model. Errors are returned, not raised, so the model can recover."""
    try:
        if name == "get_net_worth":
            result = compute_net_worth(provider.get_accounts()).model_dump()
        elif name == "get_accounts":
            result = [a.model_dump() for a in provider.get_accounts()]
        elif name == "get_credit_cards":
            result = [c.model_dump(mode="json") for c in provider.get_credit_cards()]
        elif name == "get_spending_summary":
            days = int(args.get("days", 30))
            result = {"days": days, **spending_summary(provider.get_transactions(days))}
        elif name == "get_recent_transactions":
            txns = provider.get_transactions(int(args.get("days", 30)))
            if cat := args.get("category"):
                txns = [t for t in txns if t.category.upper() == cat.upper()]
            if m := args.get("merchant"):
                txns = [t for t in txns if m.lower() in t.name.lower()]
            limit = int(args.get("limit", 25))
            result = {
                "count_matching": len(txns),
                "top_merchants": Counter(t.name for t in txns).most_common(5),
                "transactions": [t.model_dump(mode="json") for t in txns[:limit]],
            }
        elif name == "get_holdings":
            holdings = provider.get_holdings()
            result = [
                {**h.model_dump(), "gain": round(h.value - h.cost_basis, 2) if h.cost_basis else None}
                for h in holdings
            ]
        elif name == "get_stock_quote":
            result = market.get_quote(args["symbol"]).model_dump()
        elif name == "get_subscriptions":
            subs = find_subscriptions(provider.get_transactions(90))
            result = {"monthly_total": round(sum(x.amount for x in subs), 2),
                      "yearly_total": round(sum(x.yearly_cost for x in subs), 2),
                      "subscriptions": [x.model_dump() for x in subs]}
        elif name == "get_alerts":
            alerts = unusual_charges(provider.get_transactions(30)) + card_alerts(provider.get_credit_cards())
            result = [a.model_dump() for a in alerts] or {"message": "No alerts right now."}
        elif name == "get_savings_goals":
            goals = goals_fn() if goals_fn else None
            result = goals or {"message": "The user hasn't set any savings goals yet."}
        elif name == "get_market_news":
            result = [n.model_dump() for n in market.get_news(int(args.get("limit", 5)))]
        else:
            result = {"error": f"unknown tool {name}"}
    except Exception as e:  # noqa: BLE001
        result = {"error": f"{type(e).__name__}: {e}"}
    return json.dumps(result, default=str)

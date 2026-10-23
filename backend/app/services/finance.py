"""Pure functions over normalized data — easy to unit test."""
from collections import defaultdict

from app.schemas import Account, NetWorth, Transaction

LIABILITY_TYPES = {"credit", "loan"}


def compute_net_worth(accounts: list[Account]) -> NetWorth:
    assets = liabilities = 0.0
    by_type: dict[str, float] = defaultdict(float)
    for a in accounts:
        by_type[a.type] += a.balance
        if a.type in LIABILITY_TYPES:
            liabilities += a.balance
        else:
            assets += a.balance
    return NetWorth(
        assets=round(assets, 2),
        liabilities=round(liabilities, 2),
        net_worth=round(assets - liabilities, 2),
        by_type={k: round(v, 2) for k, v in by_type.items()},
    )


def spending_summary(txns: list[Transaction]) -> dict:
    """Money in vs. out and spend by category. Plaid convention: amount > 0 is an outflow."""
    by_cat: dict[str, float] = defaultdict(float)
    income = spent = 0.0
    for t in txns:
        if t.category in ("TRANSFER_IN", "TRANSFER_OUT", "LOAN_PAYMENTS"):
            continue  # moving money between your own accounts isn't spending
        if t.amount < 0:
            income += -t.amount
        else:
            spent += t.amount
            by_cat[t.category] += t.amount
    return {
        "income": round(income, 2),
        "spent": round(spent, 2),
        "net": round(income - spent, 2),
        "by_category": dict(sorted(((k, round(v, 2)) for k, v in by_cat.items()), key=lambda kv: -kv[1])),
    }

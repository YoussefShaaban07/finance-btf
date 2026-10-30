"""Find recurring charges (subscriptions, rent, bills) from transaction history."""
from collections import defaultdict
from datetime import timedelta
from itertools import pairwise

from pydantic import BaseModel

from app.schemas import Transaction


class Subscription(BaseModel):
    merchant: str
    amount: float
    category: str
    times_seen: int
    last_charged: str
    next_expected: str
    yearly_cost: float


def find_subscriptions(txns: list[Transaction], tolerance: float = 0.05) -> list[Subscription]:
    """A merchant charged ~the same amount roughly monthly (25–35 days apart), at least twice."""
    by_merchant: dict[str, list[Transaction]] = defaultdict(list)
    for t in txns:
        if t.amount > 0:
            by_merchant[t.name].append(t)

    subs = []
    for merchant, charges in by_merchant.items():
        charges.sort(key=lambda t: t.date)
        if len(charges) < 2:
            continue
        typical = charges[-1].amount
        same_price = [c for c in charges if abs(c.amount - typical) <= tolerance * typical]
        if len(same_price) < 2:
            continue
        gaps = [(b.date - a.date).days for a, b in pairwise(same_price)]
        if not all(25 <= g <= 35 for g in gaps):
            continue
        last = same_price[-1]
        subs.append(Subscription(
            merchant=merchant,
            amount=typical,
            category=last.category,
            times_seen=len(same_price),
            last_charged=last.date.isoformat(),
            next_expected=(last.date + timedelta(days=round(sum(gaps) / len(gaps)))).isoformat(),
            yearly_cost=round(typical * 12, 2),
        ))
    return sorted(subs, key=lambda s: -s.amount)

"""Alerts: unusual charges, card payments due soon, high credit utilization."""
from datetime import date
from statistics import median

from pydantic import BaseModel

from app.schemas import CreditCard, Transaction


class Alert(BaseModel):
    level: str  # "warning" | "info"
    title: str
    detail: str


def unusual_charges(txns: list[Transaction], multiple: float = 2.0, min_amount: float = 20.0) -> list[Alert]:
    """Flag a purchase that's way bigger than what you normally spend at that merchant (or in that category)."""
    spends = [t for t in txns if t.amount > 0]
    by_key: dict[str, list[float]] = {}
    for t in spends:
        by_key.setdefault(t.name, []).append(t.amount)
        by_key.setdefault("cat:" + t.category, []).append(t.amount)

    alerts = []
    for t in spends:
        history = by_key[t.name] if len(by_key[t.name]) >= 3 else by_key["cat:" + t.category]
        if len(history) < 3 or t.amount < min_amount:
            continue
        typical = median(history)
        if t.amount >= multiple * typical:
            alerts.append(Alert(level="warning", title=f"Unusual charge: {t.name}",
                                detail=f"${t.amount:,.2f} on {t.date} — you usually spend about ${typical:,.2f} there."))
    return alerts


def card_alerts(cards: list[CreditCard], due_within_days: int = 7, util_threshold: float = 30.0) -> list[Alert]:
    alerts = []
    for c in cards:
        if c.next_due_date:
            days = (c.next_due_date - date.today()).days
            if 0 <= days <= due_within_days:
                pay = f" (minimum ${c.minimum_payment:,.2f})" if c.minimum_payment else ""
                alerts.append(Alert(level="warning", title=f"{c.name} payment due in {days} days",
                                    detail=f"Balance ${c.balance:,.2f}{pay}."))
        if c.utilization_pct is not None and c.utilization_pct >= util_threshold:
            alerts.append(Alert(level="info", title=f"{c.name} is at {c.utilization_pct:.0f}% utilization",
                                detail="Keeping it under 30% helps your credit score."))
    return alerts

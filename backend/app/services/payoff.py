"""Debt payoff planner: avalanche vs. snowball, simulated month by month.

Both strategies spend the same fixed amount every month: every card's minimum payment plus any extra the user
chooses. Minimums are paid first; whatever is left goes to one target card. When a card is paid off, its
minimum "rolls over" into the pot, so payments snowball. The only difference is which card is the target:

  avalanche: highest APR first      (mathematically the least interest)
  snowball:  smallest balance first (quick wins, which some people find easier to stick with)

Simplifications, stated so the numbers aren't oversold: APRs are compounded monthly (APR / 12), minimum
payments stay fixed at today's amount, and no new charges are added.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from pydantic import BaseModel

from app.schemas import CreditCard

Strategy = Literal["avalanche", "snowball"]
MAX_MONTHS = 600  # 50 years: anything longer is reported as "never pays off"
DEFAULT_MIN_FLOOR = 25.0
DEFAULT_MIN_RATE = 0.02  # when a bank doesn't report a minimum, assume 2% of balance, at least $25
CENT = 0.005


class Debt(BaseModel):
    name: str
    balance: float
    apr: float  # percent, e.g. 24.99
    minimum: float
    assumed: list[str] = []  # fields we had to guess because the bank didn't report them


class PaidOff(BaseModel):
    name: str
    month: int


class PayoffPlan(BaseModel):
    strategy: Strategy
    feasible: bool
    months: int  # months until debt-free (0 if no debt; MAX_MONTHS if not feasible)
    total_interest: float
    total_paid: float
    monthly_payment: float
    order: list[PaidOff]  # in the order the cards get paid off
    balance_by_month: list[float]  # total owed at the start, then after each month
    balance_by_card: dict[str, list[float]]  # the same, per card (what the chart draws)


def debts_from_cards(cards: list[CreditCard]) -> list[Debt]:
    """Cards with a balance, with sensible stand-ins (flagged in `assumed`) for anything the bank didn't report."""
    debts = []
    for c in cards:
        if c.balance <= CENT:
            continue
        assumed = []
        apr = c.apr
        if apr is None:
            apr = 0.0
            assumed.append("apr")
        minimum = c.minimum_payment
        if not minimum:
            minimum = min(c.balance, max(DEFAULT_MIN_FLOOR, c.balance * DEFAULT_MIN_RATE))
            assumed.append("minimum")
        name, n = c.name, 2
        while any(d.name == name for d in debts):  # two "Visa" cards from different banks stay distinct
            name, n = f"{c.name} ({n})", n + 1
        debts.append(Debt(name=name, balance=c.balance, apr=apr, minimum=minimum, assumed=assumed))
    return debts


@dataclass
class _Account:
    debt: Debt
    balance: float = field(init=False)

    def __post_init__(self) -> None:
        self.balance = self.debt.balance

    @property
    def open(self) -> bool:
        return self.balance > CENT


def _priority(strategy: Strategy, a: _Account) -> tuple:
    if strategy == "avalanche":
        return (-a.debt.apr, a.balance)  # highest rate first; smaller balance breaks ties
    return (a.balance, -a.debt.apr)  # smallest balance first; higher rate breaks ties


def simulate(debts: list[Debt], strategy: Strategy, extra_per_month: float = 0.0) -> PayoffPlan:
    """Run one strategy to the end. Pure function: same input, same plan."""
    if extra_per_month < 0:
        raise ValueError("Extra payment can't be negative.")
    accounts = [_Account(d) for d in debts]
    budget = round(sum(d.minimum for d in debts) + extra_per_month, 2)
    start = round(sum(a.balance for a in accounts), 2)
    history = [start]
    by_card = {a.debt.name: [round(a.balance, 2)] for a in accounts}
    order: list[PaidOff] = []
    total_interest = total_paid = 0.0
    month = 0

    while any(a.open for a in accounts):
        month += 1
        if month > MAX_MONTHS:
            return PayoffPlan(strategy=strategy, feasible=False, months=MAX_MONTHS,
                              total_interest=round(total_interest, 2), total_paid=round(total_paid, 2),
                              monthly_payment=budget, order=order, balance_by_month=history, balance_by_card=by_card)

        for a in accounts:  # 1. interest accrues on whatever is still owed
            if a.open:
                interest = a.balance * a.debt.apr / 100 / 12
                a.balance += interest
                total_interest += interest

        pot = budget
        for a in accounts:  # 2. every open card gets its minimum (or what's left of its balance)
            if a.open:
                pay = min(a.debt.minimum, a.balance, pot)
                a.balance -= pay
                pot -= pay

        for a in sorted((a for a in accounts if a.open), key=lambda a: _priority(strategy, a)):  # 3. the rest
            if pot <= CENT:
                break
            pay = min(a.balance, pot)
            a.balance -= pay
            pot -= pay

        total_paid += budget - pot
        for a in accounts:
            if not a.open and all(p.name != a.debt.name for p in order):
                a.balance = 0.0
                order.append(PaidOff(name=a.debt.name, month=month))
        history.append(round(sum(a.balance for a in accounts), 2))
        for a in accounts:
            by_card[a.debt.name].append(round(max(a.balance, 0.0), 2))

    return PayoffPlan(strategy=strategy, feasible=True, months=month, total_interest=round(total_interest, 2),
                      total_paid=round(total_paid, 2), monthly_payment=budget, order=order, balance_by_month=history,
                      balance_by_card=by_card)


class PayoffComparison(BaseModel):
    avalanche: PayoffPlan
    snowball: PayoffPlan
    interest_saved_by_avalanche: float
    recommendation: str
    assumptions: list[str]


def compare(cards: list[CreditCard], extra_per_month: float = 0.0) -> PayoffComparison | None:
    """Both strategies side by side, plus a plain-English verdict. None when there's no card debt."""
    debts = debts_from_cards(cards)
    if not debts:
        return None
    av = simulate(debts, "avalanche", extra_per_month)
    sb = simulate(debts, "snowball", extra_per_month)
    saved = round(sb.total_interest - av.total_interest, 2)

    if not av.feasible:
        verdict = ("At this payment the balances never get paid off: interest grows faster than you pay. "
                   "Add an extra monthly payment to see a plan.")
    elif saved >= 1:
        verdict = (f"Avalanche saves ${saved:,.2f} in interest. Snowball pays off {sb.order[0].name} first "
                   f"(month {sb.order[0].month}) if a quick win helps you stay motivated.")
    elif extra_per_month == 0:
        verdict = (f"Paying only the minimums, both plans are the same: debt-free in {av.months} months. "
                   "The strategy decides where extra money goes, so add an extra amount to compare them.")
    else:
        verdict = (f"The two plans cost about the same here (debt-free in {av.months} months). Snowball pays off "
                   f"{sb.order[0].name} first (month {sb.order[0].month}), which is the easier win.")

    assumptions = ["APR compounds monthly, minimums stay at today's amount, and no new charges are added."]
    for d in debts:
        if "apr" in d.assumed:
            assumptions.append(f"{d.name}: the bank didn't report an APR, so it's treated as 0%.")
        if "minimum" in d.assumed:
            assumptions.append(f"{d.name}: no minimum reported, so it uses ${d.minimum:,.2f} (2% of balance, at least $25).")
    return PayoffComparison(avalanche=av, snowball=sb, interest_saved_by_avalanche=saved, recommendation=verdict,
                            assumptions=assumptions)

"""Deterministic fake data so the whole app (and the chatbot) works with zero API keys."""
import random
from datetime import date, timedelta

from app.providers.base import FinanceProvider
from app.schemas import Account, CreditCard, Holding, Transaction

ACCOUNTS = [
    Account(id="chk_1", name="Everyday Checking", type="depository", subtype="checking", balance=2840.55, institution="Demo Bank"),
    Account(id="sav_1", name="High-Yield Savings", type="depository", subtype="savings", balance=6200.00, institution="Demo Bank"),
    Account(id="cc_1", name="Cash Back Visa", type="credit", subtype="credit card", balance=742.18, limit=3000, institution="Demo Bank"),
    Account(id="cc_2", name="Student Mastercard", type="credit", subtype="credit card", balance=315.40, limit=1000, institution="Demo Credit Union"),
    Account(id="inv_1", name="Roth IRA", type="investment", subtype="roth", balance=4310.00, institution="Demo Brokerage"),
    Account(id="loan_1", name="Car Loan", type="loan", subtype="auto", balance=8900.00, institution="Demo Credit Union"),
]

CARD_DETAILS = {
    "cc_1": {"apr": 24.99, "min": 35.00, "due_in_days": 9},
    "cc_2": {"apr": 19.49, "min": 25.00, "due_in_days": 17},
}

HOLDINGS = [
    Holding(ticker="VTI", name="Vanguard Total Stock Market ETF", quantity=8, price=292.10, value=2336.80, cost_basis=2010.00),
    Holding(ticker="AAPL", name="Apple Inc.", quantity=4, price=231.50, value=926.00, cost_basis=780.00),
    Holding(ticker="NVDA", name="NVIDIA Corp.", quantity=6, price=174.53, value=1047.18, cost_basis=690.00),
]

MERCHANTS = [
    ("Kroger", "FOOD_AND_DRINK", 25, 110),
    ("Chick-fil-A", "FOOD_AND_DRINK", 8, 18),
    ("Starbucks", "FOOD_AND_DRINK", 4, 9),
    ("Shell", "TRANSPORTATION", 30, 55),
    ("Amazon", "GENERAL_MERCHANDISE", 12, 90),
    ("Spotify", "ENTERTAINMENT", 11.99, 11.99),
    ("Netflix", "ENTERTAINMENT", 15.49, 15.49),
    ("Entergy", "RENT_AND_UTILITIES", 70, 120),
    ("Planet Fitness", "PERSONAL_CARE", 10, 10),
]


class DemoProvider(FinanceProvider):
    is_demo = True

    def get_accounts(self) -> list[Account]:
        return [a.model_copy() for a in ACCOUNTS]

    def get_credit_cards(self) -> list[CreditCard]:
        cards = []
        for a in ACCOUNTS:
            if a.type != "credit":
                continue
            d = CARD_DETAILS[a.id]
            cards.append(
                CreditCard(
                    account_id=a.id,
                    name=a.name,
                    balance=a.balance,
                    limit=a.limit,
                    utilization_pct=round(a.balance / a.limit * 100, 1) if a.limit else None,
                    apr=d["apr"],
                    minimum_payment=d["min"],
                    next_due_date=date.today() + timedelta(days=d["due_in_days"]),
                )
            )
        return cards

    def get_holdings(self) -> list[Holding]:
        return [h.model_copy() for h in HOLDINGS]

    def get_transactions(self, days: int = 30) -> list[Transaction]:
        rng = random.Random(42)  # same data every run
        today = date.today()
        txns: list[Transaction] = []
        for offset in range(days):
            day = today - timedelta(days=offset)
            if day.day in (1, 15):
                txns.append(Transaction(id=f"pay_{offset}", date=day, name="Payroll Deposit",
                                        amount=-1150.00, category="INCOME", account_id="chk_1"))
            for _ in range(rng.randint(0, 3)):
                name, cat, lo, hi = rng.choice(MERCHANTS)
                acct = rng.choice(["chk_1", "cc_1", "cc_2"])
                txns.append(Transaction(id=f"tx_{offset}_{len(txns)}", date=day, name=name,
                                        amount=round(rng.uniform(lo, hi), 2), category=cat, account_id=acct))
        return sorted(txns, key=lambda t: t.date, reverse=True)

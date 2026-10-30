"""Everything the views need, computed once per page run.

Views receive a `DashboardContext` and only render. No view talks to Plaid or does math on raw data itself,
which keeps the numbers on screen and the numbers the assistant sees identical.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from app.config import Settings
from app.db import session_scope
from app.schemas import Account, CreditCard, Holding, NetWorth, Transaction
from app.services import goals as goals_svc
from app.services.alerts import Alert, card_alerts, unusual_charges
from app.services.finance import compute_net_worth, spending_summary
from app.services.goals import GoalProgress
from app.services.subscriptions import Subscription, find_subscriptions
from dashboard.data import HISTORY_DAYS, Snapshot


@dataclass
class DashboardContext:
    user_id: str
    days: int
    settings: Settings
    snapshot: Snapshot
    errors: list[str]
    linked_banks: list[str] = field(default_factory=list)

    accounts: list[Account] = field(init=False)
    cards: list[CreditCard] = field(init=False)
    holdings: list[Holding] = field(init=False)
    txns: list[Transaction] = field(init=False)
    net_worth: NetWorth = field(init=False)
    spend: dict = field(init=False)
    monthly_net: float = field(init=False)
    alerts: list[Alert] = field(init=False)
    subscriptions: list[Subscription] = field(init=False)
    savings_balance: float = field(init=False)

    def __post_init__(self) -> None:
        s = self.snapshot
        self.accounts = s.get_accounts()
        self.cards = s.get_credit_cards()
        self.holdings = s.get_holdings()
        self.txns = s.get_transactions(self.days)
        history = s.get_transactions(HISTORY_DAYS)

        self.net_worth = compute_net_worth(self.accounts)
        self.spend = spending_summary(self.txns)
        self.monthly_net = spending_summary(history)["net"] / (HISTORY_DAYS / 30)
        self.alerts = unusual_charges(s.get_transactions(30)) + card_alerts(self.cards)
        self.subscriptions = find_subscriptions(history)

        deposits = [a for a in self.accounts if a.type == "depository"]
        savings = [a for a in deposits if (a.subtype or "") == "savings"]
        self.savings_balance = sum(a.balance for a in (savings or deposits))

    @property
    def is_demo(self) -> bool:
        return self.snapshot.is_demo

    def goal_progress(self) -> list[GoalProgress]:
        with session_scope() as db:
            return [goals_svc.progress(g, self.savings_balance, self.monthly_net)
                    for g in goals_svc.list_goals(db, self.user_id)]

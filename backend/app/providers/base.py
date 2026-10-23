from abc import ABC, abstractmethod

from app.schemas import Account, CreditCard, Holding, Transaction


class FinanceProvider(ABC):
    is_demo: bool = False

    @abstractmethod
    def get_accounts(self) -> list[Account]: ...

    @abstractmethod
    def get_credit_cards(self) -> list[CreditCard]: ...

    @abstractmethod
    def get_holdings(self) -> list[Holding]: ...

    @abstractmethod
    def get_transactions(self, days: int = 30) -> list[Transaction]: ...

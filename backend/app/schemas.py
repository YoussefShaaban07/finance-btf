"""Normalized shapes every provider (Plaid or demo) returns. The rest of the app only sees these."""
from datetime import date

from pydantic import BaseModel


class Account(BaseModel):
    id: str
    name: str
    type: str  # depository | credit | investment | loan | other
    subtype: str | None = None
    balance: float  # current balance; for credit/loan this is what you owe
    limit: float | None = None
    institution: str = ""


class CreditCard(BaseModel):
    account_id: str
    name: str
    balance: float
    limit: float | None
    utilization_pct: float | None
    apr: float | None
    minimum_payment: float | None
    next_due_date: date | None


class Holding(BaseModel):
    ticker: str
    name: str
    quantity: float
    price: float
    value: float
    cost_basis: float | None = None


class Transaction(BaseModel):
    id: str
    date: date
    name: str
    amount: float  # positive = money out (Plaid convention), negative = money in
    category: str
    account_id: str


class NetWorth(BaseModel):
    assets: float
    liabilities: float
    net_worth: float
    by_type: dict[str, float]


class Quote(BaseModel):
    symbol: str
    price: float
    change: float
    change_pct: float
    prev_close: float


class NewsItem(BaseModel):
    headline: str
    source: str
    url: str
    summary: str = ""


class ChatMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]


class ChatResponse(BaseModel):
    reply: str
    tools_used: list[str]

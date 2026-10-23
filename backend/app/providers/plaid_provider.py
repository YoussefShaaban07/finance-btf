"""Real data via Plaid. Works with the free Sandbox (fake banks) out of the box."""
from datetime import date, timedelta

import plaid
from plaid.api import plaid_api
from plaid.model.accounts_balance_get_request import AccountsBalanceGetRequest
from plaid.model.investments_holdings_get_request import InvestmentsHoldingsGetRequest
from plaid.model.liabilities_get_request import LiabilitiesGetRequest
from plaid.model.transactions_sync_request import TransactionsSyncRequest

from app.config import get_settings
from app.crypto import decrypt
from app.providers.base import FinanceProvider
from app.schemas import Account, CreditCard, Holding, Transaction

_ENVS = {
    "sandbox": plaid.Environment.Sandbox,
    "production": plaid.Environment.Production,
}


def plaid_client() -> plaid_api.PlaidApi:
    s = get_settings()
    config = plaid.Configuration(
        host=_ENVS.get(s.plaid_env, plaid.Environment.Sandbox),
        api_key={"clientId": s.plaid_client_id, "secret": s.plaid_secret},
    )
    return plaid_api.PlaidApi(plaid.ApiClient(config))


def _call_optional(fn):
    """Some institutions don't support every product (e.g. no investments). Skip those quietly."""
    try:
        return fn()
    except plaid.ApiException as e:
        if any(code in str(e.body) for code in ("PRODUCTS_NOT_SUPPORTED", "NO_INVESTMENT_ACCOUNTS",
                                                "NO_LIABILITY_ACCOUNTS", "PRODUCT_NOT_READY")):
            return None
        raise


class PlaidProvider(FinanceProvider):
    def __init__(self, items):
        self.client = plaid_client()
        self.items = [(i.institution_name, decrypt(i.access_token_enc)) for i in items]

    def get_accounts(self) -> list[Account]:
        out = []
        for inst, token in self.items:
            resp = self.client.accounts_balance_get(AccountsBalanceGetRequest(access_token=token)).to_dict()
            for a in resp["accounts"]:
                bal = a["balances"]
                out.append(Account(
                    id=a["account_id"],
                    name=a.get("official_name") or a["name"],
                    type=str(a["type"]),
                    subtype=str(a.get("subtype")) if a.get("subtype") else None,
                    balance=bal.get("current") or 0.0,
                    limit=bal.get("limit"),
                    institution=inst,
                ))
        return out

    def get_credit_cards(self) -> list[CreditCard]:
        accounts = {a.id: a for a in self.get_accounts() if a.type == "credit"}
        cards = []
        for _, token in self.items:
            resp = _call_optional(lambda: self.client.liabilities_get(LiabilitiesGetRequest(access_token=token)).to_dict())
            details = {c["account_id"]: c for c in (resp or {}).get("liabilities", {}).get("credit") or []}
            for acct_id, a in accounts.items():
                d = details.get(acct_id, {})
                purchase_apr = next((x["apr_percentage"] for x in d.get("aprs", []) if x.get("apr_type") == "purchase_apr"), None)
                cards.append(CreditCard(
                    account_id=acct_id,
                    name=a.name,
                    balance=a.balance,
                    limit=a.limit,
                    utilization_pct=round(a.balance / a.limit * 100, 1) if a.limit else None,
                    apr=purchase_apr,
                    minimum_payment=d.get("minimum_payment_amount"),
                    next_due_date=d.get("next_payment_due_date"),
                ))
        # an account can only belong to one item, so dedupe by id
        return list({c.account_id: c for c in cards}.values())

    def get_holdings(self) -> list[Holding]:
        out = []
        for _, token in self.items:
            resp = _call_optional(lambda: self.client.investments_holdings_get(
                InvestmentsHoldingsGetRequest(access_token=token)).to_dict())
            if not resp:
                continue
            secs = {s["security_id"]: s for s in resp["securities"]}
            for h in resp["holdings"]:
                sec = secs.get(h["security_id"], {})
                out.append(Holding(
                    ticker=sec.get("ticker_symbol") or "N/A",
                    name=sec.get("name") or "Unknown",
                    quantity=h["quantity"],
                    price=h["institution_price"],
                    value=h["institution_value"],
                    cost_basis=h.get("cost_basis"),
                ))
        return out

    def get_transactions(self, days: int = 30) -> list[Transaction]:
        cutoff = date.today() - timedelta(days=days)
        out = []
        for _, token in self.items:
            cursor, has_more = None, True
            while has_more:
                kwargs = {"access_token": token}
                if cursor:
                    kwargs["cursor"] = cursor
                resp = self.client.transactions_sync(TransactionsSyncRequest(**kwargs)).to_dict()
                for t in resp["added"]:
                    if t["date"] < cutoff:
                        continue
                    pfc = t.get("personal_finance_category") or {}
                    out.append(Transaction(
                        id=t["transaction_id"],
                        date=t["date"],
                        name=t.get("merchant_name") or t["name"],
                        amount=t["amount"],
                        category=pfc.get("primary") or "OTHER",
                        account_id=t["account_id"],
                    ))
                cursor, has_more = resp["next_cursor"], resp["has_more"]
        return sorted(out, key=lambda t: t.date, reverse=True)

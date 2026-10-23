from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import NetWorthSnapshot, get_db
from app.deps import current_user, provider_dep
from app.providers.base import FinanceProvider
from app.schemas import Account, CreditCard, Holding, NetWorth, Transaction
from app.services.finance import compute_net_worth, spending_summary

router = APIRouter(tags=["finance"])


@router.get("/accounts", response_model=list[Account])
def accounts(p: FinanceProvider = Depends(provider_dep)):
    return p.get_accounts()


@router.get("/networth", response_model=NetWorth)
def net_worth(p: FinanceProvider = Depends(provider_dep)):
    return compute_net_worth(p.get_accounts())


@router.post("/networth/snapshot")
def snapshot(p: FinanceProvider = Depends(provider_dep), db: Session = Depends(get_db),
             user_id: str = Depends(current_user)):
    """Call daily (cron) to build a net-worth-over-time chart."""
    nw = compute_net_worth(p.get_accounts())
    db.add(NetWorthSnapshot(user_id=user_id, assets=nw.assets, liabilities=nw.liabilities, net_worth=nw.net_worth))
    db.commit()
    return nw


@router.get("/networth/history")
def history(db: Session = Depends(get_db), user_id: str = Depends(current_user)):
    rows = (db.query(NetWorthSnapshot).filter(NetWorthSnapshot.user_id == user_id)
            .order_by(NetWorthSnapshot.taken_at).all())
    return [{"date": r.taken_at.date().isoformat(), "net_worth": r.net_worth} for r in rows]


@router.get("/credit-cards", response_model=list[CreditCard])
def credit_cards(p: FinanceProvider = Depends(provider_dep)):
    return p.get_credit_cards()


@router.get("/holdings", response_model=list[Holding])
def holdings(p: FinanceProvider = Depends(provider_dep)):
    return p.get_holdings()


@router.get("/transactions", response_model=list[Transaction])
def transactions(days: int = Query(30, ge=1, le=365), p: FinanceProvider = Depends(provider_dep)):
    return p.get_transactions(days)


@router.get("/spending")
def spending(days: int = Query(30, ge=1, le=365), p: FinanceProvider = Depends(provider_dep)):
    return {"days": days, **spending_summary(p.get_transactions(days))}

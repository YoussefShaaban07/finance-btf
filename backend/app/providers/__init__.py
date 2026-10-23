from sqlalchemy.orm import Session

from app.config import get_settings
from app.providers.base import FinanceProvider


def get_provider(db: Session, user_id: str) -> FinanceProvider:
    """Demo data when Plaid isn't configured or the user hasn't linked a bank yet."""
    from app.db import PlaidItem
    from app.providers.demo import DemoProvider

    if get_settings().demo_mode:
        return DemoProvider()
    items = db.query(PlaidItem).filter(PlaidItem.user_id == user_id).all()
    if not items:
        return DemoProvider()
    from app.providers.plaid_provider import PlaidProvider

    return PlaidProvider(items)

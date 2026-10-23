from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.db import get_db
from app.providers import get_provider
from app.providers.base import FinanceProvider


def current_user(x_user_id: str = Header(default="demo-user")) -> str:
    # TODO(auth): replace with Supabase/Firebase JWT verification before real users touch this.
    return x_user_id


def provider_dep(db: Session = Depends(get_db), user_id: str = Depends(current_user)) -> FinanceProvider:
    return get_provider(db, user_id)

"""Link / unlink banks. Shared by the API routes and the Streamlit dashboard."""
from sqlalchemy.orm import Session

from app.config import get_settings
from app.crypto import decrypt, encrypt
from app.db import PlaidItem

SANDBOX_INSTITUTION = ("ins_109508", "First Platypus Bank (Sandbox)")


def plaid_ready() -> tuple[bool, str]:
    """(ok, reason) — is everything configured to link a bank?"""
    s = get_settings()
    if s.demo_mode:
        return False, "Add PLAID_CLIENT_ID and PLAID_SECRET to connect a sandbox bank."
    if not s.token_encryption_key:
        return False, "Add TOKEN_ENCRYPTION_KEY (see README) so bank tokens can be stored encrypted."
    return True, ""


def save_item(db: Session, user_id: str, public_token: str, institution_name: str) -> dict:
    from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest

    from app.providers.plaid_provider import plaid_client

    resp = plaid_client().item_public_token_exchange(ItemPublicTokenExchangeRequest(public_token=public_token)).to_dict()
    db.add(PlaidItem(user_id=user_id, item_id=resp["item_id"], institution_name=institution_name,
                     access_token_enc=encrypt(resp["access_token"])))
    db.commit()
    return {"item_id": resp["item_id"], "institution": institution_name}  # never return the access token


def link_sandbox_bank(db: Session, user_id: str) -> dict:
    """Create a fake bank login in Plaid Sandbox and store it, no Link UI needed."""
    if get_settings().plaid_env != "sandbox":
        raise ValueError("Sandbox linking only works with PLAID_ENV=sandbox")
    from plaid.model.products import Products
    from plaid.model.sandbox_public_token_create_request import SandboxPublicTokenCreateRequest

    from app.providers.plaid_provider import plaid_client

    inst_id, inst_name = SANDBOX_INSTITUTION
    public_token = plaid_client().sandbox_public_token_create(SandboxPublicTokenCreateRequest(
        institution_id=inst_id,
        initial_products=[Products("transactions"), Products("liabilities"), Products("investments")],
    )).to_dict()["public_token"]
    return save_item(db, user_id, public_token, inst_name)


def unlink_all(db: Session, user_id: str) -> int:
    """Revoke access at Plaid, then delete our encrypted copy."""
    from plaid.model.item_remove_request import ItemRemoveRequest

    from app.providers.plaid_provider import plaid_client

    items = db.query(PlaidItem).filter(PlaidItem.user_id == user_id).all()
    client = plaid_client()
    for item in items:
        try:
            client.item_remove(ItemRemoveRequest(access_token=decrypt(item.access_token_enc)))
        except Exception:  # noqa: BLE001 — still delete locally even if Plaid already forgot it
            pass
        db.delete(item)
    db.commit()
    return len(items)


def linked_institutions(db: Session, user_id: str) -> list[str]:
    return [i.institution_name for i in db.query(PlaidItem).filter(PlaidItem.user_id == user_id).all()]

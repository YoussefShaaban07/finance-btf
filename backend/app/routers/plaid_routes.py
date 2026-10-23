from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import get_settings
from app.crypto import encrypt
from app.db import PlaidItem, get_db
from app.deps import current_user

router = APIRouter(prefix="/plaid", tags=["plaid"])


def _require_plaid():
    if get_settings().demo_mode:
        raise HTTPException(400, "Plaid isn't configured (demo mode). Set PLAID_CLIENT_ID and PLAID_SECRET.")


class ExchangeBody(BaseModel):
    public_token: str
    institution_name: str = ""


def _save_item(db: Session, user_id: str, public_token: str, institution_name: str) -> dict:
    from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest

    from app.providers.plaid_provider import plaid_client

    resp = plaid_client().item_public_token_exchange(ItemPublicTokenExchangeRequest(public_token=public_token)).to_dict()
    db.add(PlaidItem(user_id=user_id, item_id=resp["item_id"], institution_name=institution_name,
                     access_token_enc=encrypt(resp["access_token"])))
    db.commit()
    return {"item_id": resp["item_id"], "institution": institution_name}  # never return the access token


@router.post("/link-token")
def create_link_token(user_id: str = Depends(current_user)):
    """Step 1: the app opens Plaid Link with this token."""
    _require_plaid()
    from plaid.model.country_code import CountryCode
    from plaid.model.link_token_create_request import LinkTokenCreateRequest
    from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
    from plaid.model.products import Products

    from app.providers.plaid_provider import plaid_client

    req = LinkTokenCreateRequest(
        user=LinkTokenCreateRequestUser(client_user_id=user_id),
        client_name="Finance BFF",
        products=[Products("transactions")],
        additional_consented_products=[Products("liabilities"), Products("investments")],
        country_codes=[CountryCode("US")],
        language="en",
    )
    return {"link_token": plaid_client().link_token_create(req).to_dict()["link_token"]}


@router.post("/exchange")
def exchange_public_token(body: ExchangeBody, db: Session = Depends(get_db), user_id: str = Depends(current_user)):
    """Step 2: Link hands the app a public_token; we swap it for a permanent access token, server-side."""
    _require_plaid()
    return _save_item(db, user_id, body.public_token, body.institution_name)


@router.post("/sandbox-link")
def sandbox_link(db: Session = Depends(get_db), user_id: str = Depends(current_user)):
    """Dev shortcut: link a fake Sandbox bank without opening the Link UI."""
    _require_plaid()
    if get_settings().plaid_env != "sandbox":
        raise HTTPException(400, "Only available in sandbox")
    from plaid.model.products import Products
    from plaid.model.sandbox_public_token_create_request import SandboxPublicTokenCreateRequest

    from app.providers.plaid_provider import plaid_client

    public_token = plaid_client().sandbox_public_token_create(SandboxPublicTokenCreateRequest(
        institution_id="ins_109508",  # "First Platypus Bank"
        initial_products=[Products("transactions"), Products("liabilities"), Products("investments")],
    )).to_dict()["public_token"]
    return _save_item(db, user_id, public_token, "First Platypus Bank (Sandbox)")


@router.get("/items")
def list_items(db: Session = Depends(get_db), user_id: str = Depends(current_user)):
    items = db.query(PlaidItem).filter(PlaidItem.user_id == user_id).all()
    return [{"item_id": i.item_id, "institution": i.institution_name, "linked_at": i.created_at} for i in items]

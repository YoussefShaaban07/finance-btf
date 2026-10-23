from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import PlaidItem, get_db
from app.deps import current_user
from app.services.plaid_link import link_sandbox_bank, plaid_ready, save_item, unlink_all

router = APIRouter(prefix="/plaid", tags=["plaid"])


def _require_plaid():
    ok, reason = plaid_ready()
    if not ok:
        raise HTTPException(400, reason)


class ExchangeBody(BaseModel):
    public_token: str
    institution_name: str = ""


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
        client_name="SpendWise",
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
    return save_item(db, user_id, body.public_token, body.institution_name)


@router.post("/sandbox-link")
def sandbox_link(db: Session = Depends(get_db), user_id: str = Depends(current_user)):
    """Dev shortcut: link a fake Sandbox bank without opening the Link UI."""
    _require_plaid()
    try:
        return link_sandbox_bank(db, user_id)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e


@router.delete("/items")
def unlink(db: Session = Depends(get_db), user_id: str = Depends(current_user)):
    _require_plaid()
    return {"removed": unlink_all(db, user_id)}


@router.get("/items")
def list_items(db: Session = Depends(get_db), user_id: str = Depends(current_user)):
    items = db.query(PlaidItem).filter(PlaidItem.user_id == user_id).all()
    return [{"item_id": i.item_id, "institution": i.institution_name, "linked_at": i.created_at} for i in items]

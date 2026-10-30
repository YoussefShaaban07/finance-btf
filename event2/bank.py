"""Event 2: talk to a fake bank through Plaid's Sandbox.

From the FinTech Club Event 2 kit (github.com/UnknownHacker1/event2-kit), copied in per its "Bringing it into
your team repo" step. Only change: the CSV paths are relative to this file. SpendWise's main Plaid integration
(backend/app/providers/plaid_provider.py) is separate; this module powers the Bank feed tab.

Three calls, in order:
    1. Get a short-lived public token
    2. Swap it for an access token
    3. Use the access token to pull accounts and transactions

Keys come from .env, never from this file.
No keys, or Plaid is down? You get the CSV files instead, so nobody gets stuck.
"""

import os
import time
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

PLAID = "https://sandbox.plaid.com"
TEST_BANK = "ins_109508"  # First Platypus Bank, Plaid's fake bank
HERE = Path(__file__).resolve().parent  # CSVs live next to this file, wherever the app is started from


def ask_plaid(path, **body):
    """Send a request, get JSON back. That's all an API call is."""
    keys = {"client_id": os.getenv("PLAID_CLIENT_ID"), "secret": os.getenv("PLAID_SECRET")}
    response = requests.post(PLAID + path, json=keys | body, timeout=30)
    if not response.ok:
        raise RuntimeError(response.json().get("error_code", response.status_code))
    return response.json()


def connect():
    """Step 1 and 2: public token, then swap it for an access token."""
    public = ask_plaid("/sandbox/public_token/create",
                       institution_id=TEST_BANK, initial_products=["transactions"])
    return ask_plaid("/item/public_token/exchange", public_token=public["public_token"])["access_token"]


def get_accounts(access_token):
    """Step 3a: the accounts."""
    raw = ask_plaid("/accounts/get", access_token=access_token)["accounts"]
    rows = [(a["name"], a["type"], a["balances"]["current"]) for a in raw]
    return pd.DataFrame(rows, columns=["name", "type", "balance"])


def get_transactions(access_token):
    """Step 3b: the transactions. A brand-new fake bank needs a few seconds to fill up."""
    added, cursor, quiet = [], None, 0
    for _ in range(15):
        body = {"cursor": cursor} if cursor else {}
        page = ask_plaid("/transactions/sync", access_token=access_token,
                         options={"days_requested": 90}, **body)
        added += page["added"]
        cursor = page["next_cursor"]
        if page["has_more"]:
            continue
        quiet = 0 if page["added"] else quiet + 1
        if added and quiet == 3:  # history comes in waves, so wait until it stops
            break
        time.sleep(2)

    rows = [(t["date"], t.get("merchant_name") or t["name"],
             (t.get("personal_finance_category") or {}).get("primary", "OTHER"), t["amount"])
            for t in added]
    tx = pd.DataFrame(rows, columns=["date", "merchant", "category", "amount"])
    return tx.sort_values("date", ascending=False).reset_index(drop=True)


def load_bank():
    """Returns accounts, transactions, and a label saying where they came from."""
    load_dotenv()
    if not (os.getenv("PLAID_CLIENT_ID") and os.getenv("PLAID_SECRET")):
        return _csv_bank("CSV backup (no keys in .env yet)")
    try:
        token = connect()  # stays here on the server, never shown on screen
        return get_accounts(token), get_transactions(token), "Plaid Sandbox"
    except Exception as error:
        return _csv_bank(f"CSV backup (Plaid said: {error})")


def _csv_bank(label):
    return pd.read_csv(HERE / "fake_accounts.csv"), pd.read_csv(HERE / "fake_transactions.csv"), label

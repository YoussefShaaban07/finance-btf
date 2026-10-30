"""Event 2 kit integration: CSV fallback, Plaid error handling, and .env key loading."""
import os

import pytest

from event2 import bank


class FakeResponse:
    def __init__(self, payload: dict, ok: bool = True):
        self._payload, self.ok, self.status_code = payload, ok, 200 if ok else 400

    def json(self) -> dict:
        return self._payload


@pytest.fixture
def no_plaid_keys(monkeypatch):
    monkeypatch.setattr(bank, "load_dotenv", lambda: None)  # ignore any real .env on this machine
    monkeypatch.delenv("PLAID_CLIENT_ID", raising=False)
    monkeypatch.delenv("PLAID_SECRET", raising=False)


def test_no_keys_falls_back_to_csv_from_any_folder(no_plaid_keys, monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)  # the CSVs must load even when the app starts somewhere else
    accounts, tx, source = bank.load_bank()
    assert source.startswith("CSV backup")
    assert list(accounts.columns) == ["name", "type", "balance"] and len(accounts) > 0
    assert list(tx.columns) == ["date", "merchant", "category", "amount"] and len(tx) > 0


def test_plaid_error_code_shows_in_the_label(monkeypatch):
    monkeypatch.setattr(bank, "load_dotenv", lambda: None)
    monkeypatch.setenv("PLAID_CLIENT_ID", "id")
    monkeypatch.setenv("PLAID_SECRET", "bad")
    monkeypatch.setattr(bank.requests, "post",
                        lambda *a, **k: FakeResponse({"error_code": "INVALID_API_KEYS"}, ok=False))
    _, _, source = bank.load_bank()
    assert source == "CSV backup (Plaid said: INVALID_API_KEYS)"


def test_sandbox_flow_returns_plaid_data(monkeypatch):
    monkeypatch.setattr(bank, "load_dotenv", lambda: None)
    monkeypatch.setattr(bank.time, "sleep", lambda s: None)
    monkeypatch.setenv("PLAID_CLIENT_ID", "id")
    monkeypatch.setenv("PLAID_SECRET", "secret")
    txn = {"date": "2026-10-01", "merchant_name": "Starbucks", "name": "SBUX",
           "personal_finance_category": {"primary": "FOOD_AND_DRINK"}, "amount": 4.5}
    pages = iter([{"added": [txn], "next_cursor": "c1", "has_more": False}]
                 + [{"added": [], "next_cursor": "c1", "has_more": False}] * 5)
    routes = {
        "/sandbox/public_token/create": lambda: {"public_token": "public-sandbox"},
        "/item/public_token/exchange": lambda: {"access_token": "access-sandbox"},
        "/accounts/get": lambda: {"accounts": [{"name": "Plaid Checking", "type": "depository",
                                                 "balances": {"current": 110.0}}]},
        "/transactions/sync": lambda: next(pages),
    }
    monkeypatch.setattr(bank.requests, "post", lambda url, json, timeout: FakeResponse(routes[url[len(bank.PLAID):]]()))
    accounts, tx, source = bank.load_bank()
    assert source == "Plaid Sandbox"
    assert accounts.iloc[0]["balance"] == 110.0
    assert tx.iloc[0]["merchant"] == "Starbucks" and tx.iloc[0]["category"] == "FOOD_AND_DRINK"


def test_dashboard_reads_keys_from_dotenv(monkeypatch, tmp_path):
    from dashboard import setup

    (tmp_path / ".env").write_text("PLAID_CLIENT_ID=from-dotenv\nGEMINI_API_KEY=from-dotenv\n")
    monkeypatch.setattr(setup, "ROOT", tmp_path)
    monkeypatch.setattr(setup, "_load_streamlit_secrets", lambda: None)
    env = {k: v for k, v in os.environ.items() if k != "PLAID_CLIENT_ID"}
    env["GEMINI_API_KEY"] = "already-set"  # existing values win over .env
    monkeypatch.setattr(os, "environ", env)  # a private copy, so nothing leaks into other tests
    setup.load_secrets()
    assert os.environ["PLAID_CLIENT_ID"] == "from-dotenv"
    assert os.environ["GEMINI_API_KEY"] == "already-set"


def test_dotenv_fills_blanks_left_by_secrets_template(monkeypatch, tmp_path):
    """Streamlit exports secrets.toml's blank `PLAID_SECRET = ""` lines as empty env vars; .env must still win."""
    from dashboard import setup

    (tmp_path / ".env").write_text("﻿PLAID_CLIENT_ID=id-from-dotenv\nPLAID_SECRET=secret-from-dotenv\n",
                                   encoding="utf-8")  # with a BOM, the way some editors save
    monkeypatch.setattr(setup, "ROOT", tmp_path)
    monkeypatch.setattr(setup, "_load_streamlit_secrets", lambda: None)
    env = dict(os.environ, PLAID_CLIENT_ID="", PLAID_SECRET="")
    monkeypatch.setattr(os, "environ", env)
    setup.load_secrets()
    assert os.environ["PLAID_CLIENT_ID"] == "id-from-dotenv"
    assert os.environ["PLAID_SECRET"] == "secret-from-dotenv"

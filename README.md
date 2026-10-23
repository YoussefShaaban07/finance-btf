# 💸 Finance BFF

An AI-powered personal finance dashboard: all your accounts, spending, cards, subscriptions, goals, and stocks in one place, plus **Penny**, an AI assistant that answers money questions using your actual numbers.

Built for the FinTech Club Innovation Series. **All data is fake** (demo data or Plaid Sandbox). Educational only, not financial advice.

## Features

| | Feature | Club event |
|---|---|---|
| 📊 | Net worth, assets, debts, cash flow; spending by category + by day; searchable transactions | 1: Vibe Check |
| 🏦 | One-click **Plaid Sandbox** bank connection (balances, cards, investments, transactions) | 2: Plug It In |
| 🤖 | **Ask AI**: assistant with 11 read-only tools, so it looks things up instead of guessing | 3: Talk to Your Wallet |
| 🔔 | Alerts: unusual charges, card payments due soon, high utilization | 3 |
| 🔁 | Automatic subscription detection with yearly cost | 3 |
| 🎯 | Savings goals with "on track / behind" | 3 |
| 💳 | Credit cards: utilization, APR, estimated monthly interest, due dates | 1–2 |
| 📈 | Portfolio + live stock watchlist | 2 |
| 🔒 | Encrypted bank tokens, no secrets in code, prompt-injection defense, AI evals: see [SECURITY.md](SECURITY.md) | 4: Lock It Down |
| 🎤 | 3-minute demo script: see [DEMO.md](DEMO.md) | 5: Demo Night |

## Run it

### Option A: your computer
```bash
python -m pip install -r requirements.txt      # Mac: python3
python -m streamlit run app.py
```
Your browser opens at http://localhost:8501. It works right away with demo data.

### Option B: GitHub Codespaces (nothing to install)
**Code → Codespaces → Create codespace on main**, wait for setup, then run `streamlit run app.py` and click **Open in Browser**.

### First change (Event 1, Task 5)
Open `app.py`, find `# TEAM TODO`, and change `TEAM_NAME`. Save, and the page updates.

## Turn on the real stuff (all free)

Copy `.streamlit/secrets.toml.example` → `.streamlit/secrets.toml` and fill in what you have. Restart the app after editing.
In Codespaces, add them as **Codespaces secrets** instead (repo Settings → Secrets and variables → Codespaces).

| Key | Where | Unlocks |
|---|---|---|
| `GEMINI_API_KEY` | [aistudio.google.com/apikey](https://aistudio.google.com/apikey) (**free tier**) | The AI assistant |
| `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com) (paid) | AI assistant, alternative to Gemini (used first if both are set) |
| `PLAID_CLIENT_ID`, `PLAID_SECRET` | [dashboard.plaid.com](https://dashboard.plaid.com) → Developers → Keys (**Sandbox** secret) | Connect sandbox bank button |
| `TOKEN_ENCRYPTION_KEY` | run `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` | Required with Plaid |
| `FINNHUB_API_KEY` | [finnhub.io](https://finnhub.io) | Live stock prices |

⚠️ **Never commit `secrets.toml` or paste keys into code.** It's already in `.gitignore`.

## How the AI works
Penny gets **tools**, not a pile of data in her prompt. For "Can I afford a $1,200 laptop?" she calls `get_accounts` and `get_spending_summary`, then does the math. Every tool is read-only, so she *can't* move money even if tricked.

Tools: `get_net_worth`, `get_accounts`, `get_credit_cards`, `get_spending_summary`, `get_recent_transactions`, `get_holdings`, `get_subscriptions`, `get_alerts`, `get_savings_goals`, `get_stock_quote`, `get_market_news`.

Her rules are in `backend/app/ai/chat.py`. Works with **Gemini or Claude**: same tools, same rules. **Test her** with `python evals/run_evals.py` (needs an AI key). It runs 9 graded cases, including refusing to move money and ignoring a prompt-injection attack hidden in a merchant name.

## Project layout
```
app.py                 ← the dashboard (start here)
dashboard/             ← loading keys + cached data for the dashboard
backend/app/
  providers/           ← DemoProvider | PlaidProvider (same interface)
  services/            ← net worth, spending, alerts, subscriptions, goals, market data, Plaid linking
  ai/                  ← assistant rules + tools + tool-use loop
  main.py              ← optional REST API (FastAPI) for the mobile app
backend/tests/         ← 16 unit tests:  cd backend && pytest
evals/                 ← AI assistant evals
mobile/                ← optional Expo phone app (talks to the REST API)
```

## Optional extras
- **REST API:** `cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload`, then open http://localhost:8000/docs
- **Phone app:** `cd mobile && npm install && npx expo start` (set `EXPO_PUBLIC_API_URL` in `mobile/.env` to your computer's IP)

## Team
| Role | Name |
|---|---|
| Developer | |
| Designer | |
| AI Prompter | |
| Researcher | |

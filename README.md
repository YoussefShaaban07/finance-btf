# Finance BFF 💸

A personal finance app: track your **net worth**, **credit cards**, **stocks**, and **spending**, and ask **Penny**, an AI assistant that answers questions using your actual account data.

> Works out of the box in **demo mode** (realistic sample data, no API keys). Add keys one at a time to light up real features.

## Features

| Tab | What it does | Data source |
|---|---|---|
| **Net Worth** | Assets − liabilities, breakdown by type, all accounts | Plaid `/accounts/balance` |
| **Cards** | Balance, limit, utilization % (color-coded), APR, min payment, due date | Plaid `/liabilities` |
| **Stocks** | Portfolio value + gain/loss, live watchlist | Plaid `/investments/holdings` + Finnhub |
| **Wallet** | Income vs. spend, spend by category, transactions (7/30/90d) | Plaid `/transactions/sync` |
| **Ask Penny** | AI chat that calls tools to read your real numbers | Claude API (tool use) |

### How the chatbot works
Penny doesn't guess. It gets 8 tools (`get_net_worth`, `get_credit_cards`, `get_spending_summary`, `get_recent_transactions`, `get_holdings`, `get_stock_quote`, …) and a tool-use loop in `backend/app/ai/chat.py`:

```
"Can I afford a $1,200 laptop?"
  → get_accounts()            # checking = $2,840
  → get_spending_summary(30)  # spending $1,9xx/mo, income $2,300
  → answer with the math
```

## Architecture

```
mobile/ (Expo + expo-router, TypeScript)
   │  REST
backend/ (FastAPI)
   ├── providers/   DemoProvider | PlaidProvider  ← same interface, swap freely
   ├── services/    net worth + spending math (pure functions), Finnhub market data
   ├── ai/          tool schemas + tool-use loop
   └── db.py        SQLite/Postgres: encrypted Plaid tokens, net-worth snapshots
```

## Run it

### Backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env          # fill in whatever keys you have
uvicorn app.main:app --reload --host 0.0.0.0
```
Open http://localhost:8000/docs for interactive API docs.

**Tests:** `pytest`. Includes a fake-LLM test that verifies the chatbot answers with real tool output.

### Mobile
```bash
cd mobile
npm install
cp .env.example .env          # set EXPO_PUBLIC_API_URL to your computer's LAN IP
npx expo start                # scan the QR code with Expo Go
```

## API keys (all free)

| Key | Get it | Unlocks |
|---|---|---|
| `PLAID_CLIENT_ID` / `PLAID_SECRET` | [dashboard.plaid.com](https://dashboard.plaid.com) → Sandbox | Real bank/card/brokerage data (sandbox = fake banks) |
| `TOKEN_ENCRYPTION_KEY` | `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` | Required once Plaid is on |
| `FINNHUB_API_KEY` | [finnhub.io](https://finnhub.io) | Live quotes + market news |
| `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com) | The chatbot |

With Plaid sandbox keys set, tap **+ Link sandbox bank** on the Net Worth tab (or `POST /plaid/sandbox-link`) to connect "First Platypus Bank" with no login UI.

## Security notes
- Plaid access tokens are **encrypted at rest** (Fernet) and never sent to the client.
- `X-User-Id` header is a placeholder. **Add real auth (Supabase/Firebase JWT) before any real user data.** See `backend/app/deps.py`.

## Roadmap
- [ ] Auth (Supabase)
- [ ] Plaid Link UI in-app (`react-native-plaid-link-sdk`, needs an Expo dev build)
- [ ] Daily net-worth snapshot cron + chart
- [ ] Persist watchlist per user
- [ ] Budgets + bill reminders (push notifications)
- [ ] Chatbot eval set: ~40 questions scored for correct tool use and no invented numbers
- [ ] RAG over IRS/CFPB guides for general finance questions

*Educational project, not financial advice.*

# 💸 SpendWise

An AI-powered personal finance dashboard: **spend smarter**. All your accounts, spending, cards, subscriptions, goals, and stocks in one place, plus **Penny**, an AI assistant that answers money questions using your actual numbers.

Built for the FinTech Club Innovation Series. **All data is fake** (demo data or Plaid Sandbox). Educational only, not financial advice.

## 🚀 Quick start: run it in your browser (nothing to install)

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/YoussefShaaban07/finance-btf)

1. **Sign in to GitHub**, then click the button above (or go to https://codespaces.new/YoussefShaaban07/finance-btf).
2. Click **Create codespace**. Wait 1–2 minutes while it sets up and installs everything.
3. In the **Terminal** panel at the bottom, type this and press Enter:
   ```
   streamlit run app.py
   ```
4. Click **Open in Browser** when the pop-up appears. (Missed it? Open the **Ports** tab and click the 🌐 globe next to port 8501.)
5. When you're done: press **Ctrl+C** in the terminal, then stop the codespace at https://github.com/codespaces so it doesn't use your free hours.

**Turn on the AI in Codespaces (one time):**
1. On this repo: **Settings → Secrets and variables → Codespaces → New repository secret**.
2. Name: `GEMINI_API_KEY`. Value: your key from https://aistudio.google.com/apikey. Click **Add secret**.
3. Restart the codespace (github.com/codespaces → **⋯** → **Stop**, then open it again), and run `streamlit run app.py`.
4. The sidebar should say **🟢 AI assistant: Gemini**.

> Can't find Codespaces? The **`<> Code`** button (green, top right of the file list) has two tabs: **Local** and **Codespaces**. It doesn't appear in the GitHub mobile app, so use a browser.

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

## Run it on your own computer

### Option A: your computer
You need [Python 3.11+](https://www.python.org/downloads/) (on Windows, check **"Add python.exe to PATH"** in the installer) and [Git](https://git-scm.com/downloads).

**1. Get the code**
```
git clone https://github.com/YoussefShaaban07/finance-btf.git
cd finance-btf
```

> ⚠️ **Type or paste ONE line at a time and press Enter after each.** Pasting several lines at once can glue them together (e.g. `cd finance-btfpy -m pip ...`), which causes `The system cannot find the path specified` or `Could not open requirements file: 'requirements.txtcd'`.

**2. Create a virtual environment** (recommended, keeps the packages inside this project)

Windows (Command Prompt):
```
py -m venv .venv
```
```
.venv\Scripts\activate
```
Mac / Linux (Terminal):
```
python3 -m venv .venv
```
```
source .venv/bin/activate
```
You should now see `(.venv)` at the start of your prompt. Every time you open a new terminal, `cd finance-btf` and run the activate line again before starting the app.

**3. Install**

Windows:
```
py -m pip install -r requirements.txt
```
Mac / Linux:
```
python3 -m pip install -r requirements.txt
```
A `[notice] A new release of pip is available` message is harmless; ignore it.

**4. Run**

Windows:
```
py -m streamlit run app.py
```
Mac / Linux:
```
python3 -m streamlit run app.py
```

Your browser opens at http://localhost:8501. It works right away with demo data. Press **Ctrl+C** in the terminal to stop it.

#### Troubleshooting

| Problem | Fix |
|---|---|
| `The system cannot find the path specified` | Two commands got pasted onto one line. Run `cd finance-btf` by itself, then the next command on its own line. |
| `Could not open requirements file: ... 'requirements.txtcd'` | Same thing: a pasted line got glued on. Run `py -m pip install -r requirements.txt` alone. |
| `py is not recognized` | Use `python` instead of `py`. |
| `pip` / `streamlit is not recognized` | Always use the `-m` form shown above (`py -m pip ...`, `py -m streamlit ...`). |
| `.venv\Scripts\activate` is blocked in PowerShell | Use Command Prompt instead, or run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once. |
| A package fails to build during install | You may be on a very new Python (e.g. 3.14). Install Python 3.12, then delete `.venv` and recreate it with `py -3.12 -m venv .venv`. |
| `ModuleNotFoundError` when running the app | The venv isn't active. Run the activate line again (you should see `(.venv)`). |
| First run asks for an email | Just press Enter. |

### Option B: GitHub Codespaces (nothing to install)
See **🚀 Quick start** at the top of this page.

### First change (Event 1, Task 5)
Open `app.py`, find `# TEAM TODO`, and change `TEAM_NAME`. Save, and the page updates.

## Turn on the real stuff (all free)

Create your secrets file and open it:

Windows:
```
copy .streamlit\secrets.toml.example .streamlit\secrets.toml
notepad .streamlit\secrets.toml
```
Mac / Linux:
```
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
open -e .streamlit/secrets.toml
```
Paste each key **between the quotes**, e.g. `GEMINI_API_KEY = "AIza..."`. Save, then **stop the app (Ctrl+C) and start it again**. It only reads keys at startup. The sidebar shows 🟢 for everything that's connected.

In Codespaces, add them as **Codespaces secrets** instead (repo Settings → Secrets and variables → Codespaces).

| Key | Where | Unlocks |
|---|---|---|
| `GEMINI_API_KEY` | [aistudio.google.com/apikey](https://aistudio.google.com/apikey) (**free tier**) | The AI assistant |
| `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com) (paid) | AI assistant, alternative to Gemini (used first if both are set) |
| `PLAID_CLIENT_ID`, `PLAID_SECRET` | [dashboard.plaid.com](https://dashboard.plaid.com) → Developers → Keys (**Sandbox** secret) | Connect sandbox bank button |
| `TOKEN_ENCRYPTION_KEY` | run `py -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` (Mac: `python3 -c ...`) and paste the output | Required with Plaid |
| `FINNHUB_API_KEY` | [finnhub.io](https://finnhub.io) | Live stock prices |

⚠️ **Never commit `secrets.toml` or paste keys into code.** It's already in `.gitignore`.

## How the AI works
Penny gets **tools**, not a pile of data in her prompt. For "Can I afford a $1,200 laptop?" she calls `get_accounts` and `get_spending_summary`, then does the math. Every tool is read-only, so she *can't* move money even if tricked.

Tools: `get_net_worth`, `get_accounts`, `get_credit_cards`, `get_spending_summary`, `get_recent_transactions`, `get_holdings`, `get_subscriptions`, `get_alerts`, `get_savings_goals`, `get_stock_quote`, `get_market_news`.

Her rules are in `backend/app/ai/chat.py`. Works with **Gemini or Claude**: same tools, same rules. **Test her** with `py evals/run_evals.py` (Mac: `python3 ...`) (needs an AI key). It runs 9 graded cases, including refusing to move money and ignoring a prompt-injection attack hidden in a merchant name.

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

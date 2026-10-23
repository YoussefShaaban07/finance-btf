# Demo Night script (≈3 minutes)

**Setup before you present:** app running, sandbox bank connected (or demo mode), AI key set, chat cleared, time range = 30 days.

| Time | Who | Show | Say |
|---|---|---|---|
| 0:00 | Researcher | Title + metrics row | "Most students have money spread across a checking account, a card or two, maybe a Roth. Nobody has one place to see it, or someone to ask. So we built one." |
| 0:20 | Developer | Sidebar → **Connect sandbox bank** | "This is Plaid, the same API real apps like Venmo use. It's a sandbox bank with fake data, but it's the real integration." |
| 0:40 | Designer | **Overview** tab: category chart, daily spending | "Spending by category and by day. The red number up top says this month I spent more than I made." |
| 1:00 | Designer | **Alerts** tab | "It caught a $487 Amazon charge, about 8× what I usually spend there. It also flags a card payment due in 5 days." |
| 1:15 | Designer | **Subscriptions** tab | "It found my subscriptions automatically: about $8,600 a year once you include rent." |
| 1:30 | AI Prompter | **Ask AI** → "Where did my money go this month?" | "The AI doesn't guess. See the 'looked up' line? It called our tools and is answering from the real numbers." |
| 1:55 | AI Prompter | Ask: "Move $500 to savings" | "And it knows its limits. Its tools are read-only, so it can't move money even if someone tricks it." |
| 2:15 | Researcher | `SECURITY.md` / eval results | "We also tested a prompt-injection attack: a fake merchant name telling the AI to ask for your SSN. It ignored it. Keys are never in code, and bank tokens are encrypted." |
| 2:40 | Everyone | Back to Overview | "Next we'd add real login and push notifications. Questions?" |

**If something breaks:** switch to demo mode (it always works) and keep going. Nobody minds.

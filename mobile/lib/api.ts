const BASE = process.env.EXPO_PUBLIC_API_URL ?? "http://localhost:8000";

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", "X-User-Id": "demo-user", ...(init?.headers ?? {}) },
  });
  if (!res.ok) throw new Error(`${res.status}: ${await res.text()}`);
  return res.json() as Promise<T>;
}

export type Account = { id: string; name: string; type: string; subtype?: string; balance: number; limit?: number; institution: string };
export type NetWorth = { assets: number; liabilities: number; net_worth: number; by_type: Record<string, number> };
export type CreditCard = {
  account_id: string; name: string; balance: number; limit: number | null; utilization_pct: number | null;
  apr: number | null; minimum_payment: number | null; next_due_date: string | null;
};
export type Holding = { ticker: string; name: string; quantity: number; price: number; value: number; cost_basis?: number };
export type Quote = { symbol: string; price: number; change: number; change_pct: number; prev_close: number };
export type Transaction = { id: string; date: string; name: string; amount: number; category: string; account_id: string };
export type Spending = { days: number; income: number; spent: number; net: number; by_category: Record<string, number> };
export type ChatMsg = { role: "user" | "assistant"; content: string };
export type Health = { demo_mode: boolean; live_stocks: boolean; chat_enabled: boolean };

export const api = {
  health: () => req<Health>("/health"),
  accounts: () => req<Account[]>("/accounts"),
  netWorth: () => req<NetWorth>("/networth"),
  history: () => req<{ date: string; net_worth: number }[]>("/networth/history"),
  creditCards: () => req<CreditCard[]>("/credit-cards"),
  holdings: () => req<Holding[]>("/holdings"),
  quotes: (symbols: string[]) => req<Quote[]>(`/market/quotes?symbols=${encodeURIComponent(symbols.join(","))}`),
  transactions: (days = 30) => req<Transaction[]>(`/transactions?days=${days}`),
  spending: (days = 30) => req<Spending>(`/spending?days=${days}`),
  sandboxLink: () => req<{ item_id: string; institution: string }>("/plaid/sandbox-link", { method: "POST" }),
  chat: (messages: ChatMsg[]) =>
    req<{ reply: string; tools_used: string[] }>("/chat", { method: "POST", body: JSON.stringify({ messages }) }),
};

export const money = (n: number) =>
  (n < 0 ? "-$" : "$") + Math.abs(n).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

export const prettyCategory = (c: string) =>
  c.toLowerCase().split("_").map((w) => (w === "and" ? "&" : w[0].toUpperCase() + w.slice(1))).join(" ");

"""Stock quotes + market news via Finnhub (free tier), with a demo fallback."""
import hashlib

import httpx

from app.config import get_settings
from app.schemas import NewsItem, Quote

FINNHUB = "https://finnhub.io/api/v1"


def _demo_quote(symbol: str) -> Quote:
    # stable fake price per symbol so the UI doesn't jump around
    seed = int(hashlib.md5(symbol.encode()).hexdigest()[:8], 16)
    prev = 20 + seed % 480
    change = ((seed >> 8) % 800 - 400) / 100
    return Quote(symbol=symbol, price=round(prev + change, 2), change=change,
                 change_pct=round(change / prev * 100, 2), prev_close=float(prev))


def get_quote(symbol: str) -> Quote:
    symbol = symbol.upper().strip()
    key = get_settings().finnhub_api_key
    if not key:
        return _demo_quote(symbol)
    r = httpx.get(f"{FINNHUB}/quote", params={"symbol": symbol, "token": key}, timeout=10)
    r.raise_for_status()
    d = r.json()
    if not d.get("c"):
        raise ValueError(f"No quote found for {symbol}")
    return Quote(symbol=symbol, price=d["c"], change=d.get("d") or 0.0,
                 change_pct=d.get("dp") or 0.0, prev_close=d.get("pc") or 0.0)


def get_news(limit: int = 10) -> list[NewsItem]:
    key = get_settings().finnhub_api_key
    if not key:
        return [NewsItem(headline="Demo mode: add FINNHUB_API_KEY for live market news",
                         source="SpendWise", url="https://finnhub.io")]
    r = httpx.get(f"{FINNHUB}/news", params={"category": "general", "token": key}, timeout=10)
    r.raise_for_status()
    return [NewsItem(headline=n["headline"], source=n.get("source", ""), url=n.get("url", ""),
                     summary=n.get("summary", "")) for n in r.json()[:limit]]

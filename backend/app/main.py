from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db import init_db
from app.routers import chat_routes, finance_routes, market_routes, plaid_routes


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="Finance BFF API", version="0.1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

app.include_router(plaid_routes.router)
app.include_router(finance_routes.router)
app.include_router(market_routes.router)
app.include_router(chat_routes.router)


@app.get("/health")
def health():
    s = get_settings()
    return {
        "ok": True,
        "demo_mode": s.demo_mode,
        "live_stocks": bool(s.finnhub_api_key),
        "chat_enabled": bool(s.anthropic_api_key),
    }

from fastapi import APIRouter, HTTPException, Query

from app.schemas import NewsItem, Quote
from app.services import market

router = APIRouter(prefix="/market", tags=["market"])


@router.get("/quote/{symbol}", response_model=Quote)
def quote(symbol: str):
    try:
        return market.get_quote(symbol)
    except ValueError as e:
        raise HTTPException(404, str(e)) from e


@router.get("/quotes", response_model=list[Quote])
def quotes(symbols: str = Query(..., description="Comma-separated, e.g. AAPL,NVDA,VTI")):
    return [market.get_quote(s) for s in symbols.split(",") if s.strip()][:20]


@router.get("/news", response_model=list[NewsItem])
def news(limit: int = Query(10, ge=1, le=30)):
    return market.get_news(limit)

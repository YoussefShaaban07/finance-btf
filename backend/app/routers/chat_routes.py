from fastapi import APIRouter, Depends, HTTPException

from app.ai.chat import chat
from app.deps import provider_dep
from app.providers.base import FinanceProvider
from app.schemas import ChatRequest, ChatResponse

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(body: ChatRequest, p: FinanceProvider = Depends(provider_dep)):
    if not body.messages or body.messages[-1].role != "user":
        raise HTTPException(400, "Last message must be from the user")
    return chat(body.messages[-20:], p)  # cap history to keep tokens in check

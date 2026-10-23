"""Tool-use loop: the model decides which data it needs, we run the tools, it answers from real numbers."""
from datetime import date

from anthropic import Anthropic

from app.ai.tools import TOOL_SCHEMAS, run_tool
from app.config import get_settings
from app.providers.base import FinanceProvider
from app.schemas import ChatMessage, ChatResponse

MAX_TOOL_ROUNDS = 6

SYSTEM_PROMPT = """You are Penny, a friendly, no-judgment personal finance assistant inside a money-tracking app.

How to work:
- For anything about the user's own money (balances, spending, cards, net worth, investments, "can I afford..."), \
call the tools first. Never invent or estimate the user's numbers — if a tool doesn't return it, say you don't have it.
- For general finance questions (what's a Roth IRA, how credit scores work), answer directly in plain English.
- Show the math when you compute something, briefly.
- Be concise. Short paragraphs or a few bullets. No jargon without a one-line explanation.
- You give education and general guidance, not licensed advice. For big, situation-specific decisions \
(taxes, legal, large investments), suggest checking with a CFP or tax pro — one line, not a lecture.

Today's date is {today}.{demo_note}"""

DEMO_NOTE = "\nThe app is in DEMO MODE: the account data is sample data. Mention that once if relevant."


def chat(messages: list[ChatMessage], provider: FinanceProvider, client: Anthropic | None = None) -> ChatResponse:
    settings = get_settings()
    if client is None:
        if not settings.anthropic_api_key:
            return ChatResponse(reply="The chatbot isn't configured yet — set ANTHROPIC_API_KEY in backend/.env.",
                                tools_used=[])
        client = Anthropic(api_key=settings.anthropic_api_key)

    system = SYSTEM_PROMPT.format(today=date.today().isoformat(), demo_note=DEMO_NOTE if provider.is_demo else "")
    convo: list[dict] = [{"role": m.role, "content": m.content} for m in messages]
    tools_used: list[str] = []

    for _ in range(MAX_TOOL_ROUNDS):
        resp = client.messages.create(
            model=settings.anthropic_model,
            max_tokens=1024,
            system=system,
            tools=TOOL_SCHEMAS,
            messages=convo,
        )
        if resp.stop_reason != "tool_use":
            text = "".join(b.text for b in resp.content if b.type == "text").strip()
            return ChatResponse(reply=text, tools_used=tools_used)

        convo.append({"role": "assistant", "content": resp.content})
        results = []
        for block in resp.content:
            if block.type == "tool_use":
                tools_used.append(block.name)
                results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": run_tool(block.name, block.input or {}, provider),
                })
        convo.append({"role": "user", "content": results})

    return ChatResponse(reply="Sorry, that took too many steps — try asking a more specific question.",
                        tools_used=tools_used)

"""FastAPI orchestrator — POST /webhook is the single inbound handler for every
channel (Twilio in prod; the mock drives `conversation.handle` directly in dev).

Railway runs this via the Procfile; its logs are the live audit stream at demo time.
"""
from __future__ import annotations

from fastapi import FastAPI, Request, Response

from app import conversation
from app.channel import get_adapter
from app.config import config

app = FastAPI(title="claim-an-agent-by-text")


@app.get("/health")
def health() -> dict:
    return {"ok": True, "channel": config.channel}


@app.post("/webhook")
async def webhook(request: Request) -> Response:
    """Twilio posts an inbound WhatsApp message here; we reply on the same channel."""
    form = dict(await request.form())
    adapter = get_adapter()
    inbound = adapter.parse_inbound(form)
    reply = conversation.handle(inbound.from_phone, inbound.text)
    adapter.send(inbound.from_phone, reply)
    # Empty TwiML — we already sent via the REST API, so no body reply needed.
    return Response(content="<Response></Response>", media_type="application/xml")

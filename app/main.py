"""FastAPI orchestrator — POST /webhook is the single inbound handler for every
channel (Twilio in prod; the mock drives `conversation.handle` directly in dev).

Railway runs this via the Procfile; its logs are the live audit stream at demo time.
"""
from __future__ import annotations

from xml.sax.saxutils import escape

from fastapi import FastAPI, Request, Response
from pydantic import BaseModel

from app import conversation
from app.channel import get_adapter
from app.config import config

app = FastAPI(title="claim-an-agent-by-text")


@app.get("/health")
def health() -> dict:
    return {
        "ok": True,
        "channel": config.channel,
        "op": config.op_configured,
        "daytona": config.daytona_configured,
        "nebius": config.nebius_configured,
    }


class SimMessage(BaseModel):
    from_phone: str = "+15555550123"
    text: str


@app.post("/sim")
def sim(msg: SimMessage) -> dict:
    """Drive the conversation over HTTP without a phone (the mock shim, as an endpoint).

    Returns the bot reply in the response body so the whole flow is curl-testable in
    prod. Same code path as /webhook — only the transport differs."""
    reply = conversation.handle(msg.from_phone, msg.text)
    return {"from": msg.from_phone, "reply": reply}


@app.post("/webhook")
async def webhook(request: Request) -> Response:
    """Twilio posts an inbound WhatsApp message here; we reply with TwiML so Twilio
    delivers the response on the same thread — no outbound API call or auth required."""
    form = dict(await request.form())
    inbound = get_adapter().parse_inbound(form)
    reply = conversation.handle(inbound.from_phone, inbound.text)
    twiml = f"<Response><Message>{escape(reply)}</Message></Response>"
    return Response(content=twiml, media_type="application/xml")

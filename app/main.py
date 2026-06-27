"""FastAPI orchestrator — POST /webhook is the single inbound handler for every
channel (Twilio in prod; the mock drives `conversation.handle` directly in dev).

Railway runs this via the Procfile; its logs are the live audit stream at demo time.
The operator view ("/") shows the live chat thread next to the agent's transactions.
"""
from __future__ import annotations

from xml.sax.saxutils import escape

from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from app import conversation, store
from app.channel import get_adapter
from app.config import config
from app.operator import PAGE
from app.registry import hash_phone

app = FastAPI(title="claim-an-agent-by-text")


def _turn(phone: str, text: str) -> str:
    """One conversation turn, recorded for the operator view (inbound + reply)."""
    store.add_message(phone, "in", text)
    reply = conversation.handle(phone, text)
    store.add_message(phone, "out", reply)
    return reply


@app.get("/health")
def health() -> dict:
    return {
        "ok": True,
        "channel": config.channel,
        "op": config.op_configured,
        "daytona": config.daytona_configured,
        "nebius": config.nebius_configured,
        "sandbox_destroy": config.sandbox_destroy,
    }


@app.get("/", response_class=HTMLResponse)
def operator() -> str:
    return PAGE


@app.get("/ops/data")
def ops_data(phone: str | None = None) -> dict:
    """Feed for the operator view: the thread + transactions for one owner."""
    phone = phone or store.latest_phone()
    return store.snapshot(phone, hash_phone(phone) if phone else None)


class SimMessage(BaseModel):
    from_phone: str = "+15555550123"
    text: str


@app.post("/sim")
def sim(msg: SimMessage) -> dict:
    """Drive the conversation over HTTP without a phone (the mock shim, as an endpoint).

    Returns the bot reply in the response body so the whole flow is curl-testable in
    prod. Same code path as /webhook — only the transport differs."""
    return {"from": msg.from_phone, "reply": _turn(msg.from_phone, msg.text)}


@app.post("/webhook")
async def webhook(request: Request) -> Response:
    """Twilio posts an inbound WhatsApp message here; we reply with TwiML so Twilio
    delivers the response on the same thread — no outbound API call or auth required."""
    form = dict(await request.form())
    inbound = get_adapter().parse_inbound(form)
    reply = _turn(inbound.from_phone, inbound.text)
    twiml = f"<Response><Message>{escape(reply)}</Message></Response>"
    return Response(content=twiml, media_type="application/xml")

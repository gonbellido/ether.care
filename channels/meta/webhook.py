import httpx
from fastapi import APIRouter, HTTPException, Request, BackgroundTasks, Response, Depends
from fastapi.responses import PlainTextResponse
from typing import Any, Dict

# This will be available when mounted in crewai app
from src.config import get_settings

router = APIRouter()

N8N_WEBHOOK_URL = "http://n8n:5678/webhook/meta-message"

async def forward_to_n8n(payload: Dict[str, Any]):
    async with httpx.AsyncClient() as client:
        try:
            await client.post(N8N_WEBHOOK_URL, json=payload, timeout=10.0)
        except Exception as e:
            # Silence errors to Meta, but could log internally
            pass

@router.get("/meta/webhook")
async def verify(request: Request, settings=Depends(get_settings)):
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == getattr(settings, "meta_verify_token", None):
        return PlainTextResponse(challenge)

    raise HTTPException(status_code=403, detail="Verification failed")

@router.post("/meta/webhook")
async def handle_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    settings=Depends(get_settings)
):
    try:
        payload = await request.json()
    except Exception:
        return Response(status_code=200, content="EVENT_RECEIVED")

    entries = payload.get("entry", [])
    for entry in entries:
        # WhatsApp logic
        changes = entry.get("changes", [])
        for change in changes:
            if change.get("field") == "messages":
                value = change.get("value", {})
                messages = value.get("messages", [])
                if messages:
                    msg = messages[0]
                    from_id = msg.get("from")
                    msg_type = msg.get("type")
                    text = "[media]"
                    if msg_type == "text":
                        text = msg.get("text", {}).get("body", "[media]")

                    forward_payload = {
                        "user_id": f"wa:{from_id}",
                        "channel": "whatsapp",
                        "text": text,
                        "raw": payload
                    }
                    background_tasks.add_task(forward_to_n8n, forward_payload)

        # Instagram/Facebook logic
        messaging = entry.get("messaging", [])
        for msg_event in messaging:
            sender_id = msg_event.get("sender", {}).get("id")
            if sender_id:
                object_type = payload.get("object")
                channel = "facebook"
                prefix = "fb"
                if object_type == "instagram":
                    channel = "instagram"
                    prefix = "ig"

                msg_text = msg_event.get("message", {}).get("text", "[media]")

                forward_payload = {
                    "user_id": f"{prefix}:{sender_id}",
                    "channel": channel,
                    "text": msg_text,
                    "raw": payload
                }
                background_tasks.add_task(forward_to_n8n, forward_payload)

    return Response(status_code=200, content="EVENT_RECEIVED")

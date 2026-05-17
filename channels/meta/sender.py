import httpx

async def send_whatsapp(phone: str, text: str, settings) -> bool:
    """
    Sends a WhatsApp message via Meta Graph API.
    """
    url = f"https://graph.facebook.com/v19.0/{settings.meta_whatsapp_phone_id}/messages"
    headers = {
        "Authorization": f"Bearer {settings.meta_access_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": phone,
        "type": "text",
        "text": {"body": text}
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, headers=headers)
            return response.status_code == 200
        except Exception:
            return False

async def send_instagram(ig_user_id: str, text: str, settings) -> bool:
    """
    Sends an Instagram DM via Meta Graph API.
    """
    url = "https://graph.facebook.com/v19.0/me/messages"
    headers = {
        "Authorization": f"Bearer {settings.meta_access_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "recipient": {"id": ig_user_id},
        "message": {"text": text}
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, headers=headers)
            return response.status_code == 200
        except Exception:
            return False

async def send_facebook(psid: str, text: str, settings) -> bool:
    """
    Sends a Facebook Messenger message via Meta Graph API.
    """
    # Same as Instagram for FB PSID
    return await send_instagram(psid, text, settings)

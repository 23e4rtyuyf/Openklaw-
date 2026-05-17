import os
import httpx

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")


async def set_webhook(url: str) -> bool:
    if not TELEGRAM_BOT_TOKEN:
        return False
    api_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook"
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(api_url, json={"url": url})
        return resp.status_code == 200


async def send_message(chat_id: str, text: str) -> bool:
    if not TELEGRAM_BOT_TOKEN:
        return False
    api_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(api_url, json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"})
        return resp.status_code == 200


def parse_update(body: dict) -> dict | None:
    message = body.get("message") or body.get("edited_message")
    if not message:
        return None
    return {
        "chat_id": str(message["chat"]["id"]),
        "text": message.get("text", ""),
        "from": message.get("from", {}).get("username", "unknown"),
    }

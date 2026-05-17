import os
import httpx

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")


async def send_notification(message: str, chat_id: str) -> str:
    if not TELEGRAM_BOT_TOKEN or not chat_id:
        return "Notification skipped (Telegram not configured)"
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(url, json={"chat_id": chat_id, "text": message, "parse_mode": "Markdown"})
        if resp.status_code == 200:
            return "Notification sent"
        return f"Notification failed: {resp.text}"

import httpx


async def send_discord_message(text: str, webhook_url: str) -> str:
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(webhook_url, json={"content": text[:2000]})
        return "Discord message sent" if resp.status_code in (200, 204) else f"Discord error: {resp.text}"

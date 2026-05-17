import httpx


async def send_slack_message(text: str, webhook_url: str) -> str:
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(webhook_url, json={"text": text})
        return "Slack message sent" if resp.status_code == 200 else f"Slack error: {resp.text}"


async def send_slack_channel(text: str, channel: str, bot_token: str) -> str:
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            "https://slack.com/api/chat.postMessage",
            headers={"Authorization": f"Bearer {bot_token}"},
            json={"channel": channel, "text": text},
        )
        data = resp.json()
        return "Slack message sent" if data.get("ok") else f"Slack error: {data.get('error')}"


async def read_slack_channel(channel: str, bot_token: str, limit: int = 20) -> list:
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            "https://slack.com/api/conversations.history",
            headers={"Authorization": f"Bearer {bot_token}"},
            params={"channel": channel, "limit": limit},
        )
        data = resp.json()
        if not data.get("ok"):
            return [{"error": data.get("error")}]
        return [{"user": m.get("user"), "text": m.get("text"), "ts": m.get("ts")}
                for m in data.get("messages", [])]


async def read_slack_thread(channel: str, thread_ts: str, bot_token: str) -> list:
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            "https://slack.com/api/conversations.replies",
            headers={"Authorization": f"Bearer {bot_token}"},
            params={"channel": channel, "ts": thread_ts},
        )
        data = resp.json()
        if not data.get("ok"):
            return [{"error": data.get("error")}]
        return [{"user": m.get("user"), "text": m.get("text"), "ts": m.get("ts")}
                for m in data.get("messages", [])]


async def post_slack_reply(channel: str, thread_ts: str, text: str, bot_token: str) -> str:
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            "https://slack.com/api/chat.postMessage",
            headers={"Authorization": f"Bearer {bot_token}"},
            json={"channel": channel, "thread_ts": thread_ts, "text": text},
        )
        data = resp.json()
        return "Reply sent" if data.get("ok") else f"Slack error: {data.get('error')}"

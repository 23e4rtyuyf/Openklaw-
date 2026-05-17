import httpx


async def fetch_url(url: str, headers: dict = None) -> str:
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        resp = await client.get(url, headers=headers or {})
        resp.raise_for_status()
        return resp.text[:8000]


async def http_post(url: str, body: dict = None, headers: dict = None) -> str:
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(url, json=body or {}, headers=headers or {})
        resp.raise_for_status()
        return resp.text[:8000]

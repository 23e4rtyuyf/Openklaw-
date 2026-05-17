import httpx

_BASE = "https://api.notion.com/v1"
_VERSION = "2022-06-28"


def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}", "Notion-Version": _VERSION,
            "Content-Type": "application/json"}


def _extract_text(page: dict) -> str:
    props = page.get("properties", {})
    parts = []
    for key, val in props.items():
        t = val.get("type")
        if t == "title":
            for rt in val.get("title", []):
                parts.append(f"{key}: {rt.get('plain_text', '')}")
        elif t == "rich_text":
            for rt in val.get("rich_text", []):
                parts.append(f"{key}: {rt.get('plain_text', '')}")
        elif t in ("number", "checkbox", "select", "date", "email", "url", "phone_number"):
            parts.append(f"{key}: {val.get(t)}")
    return "\n".join(parts)


async def notion_get_page(page_id: str, token: str) -> dict:
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.get(f"{_BASE}/pages/{page_id}", headers=_headers(token))
        page = r.json()
        return {"id": page.get("id"), "url": page.get("url"), "content": _extract_text(page)}


async def notion_create_page(parent_id: str, title: str, content: str, token: str) -> dict:
    body = {
        "parent": {"page_id": parent_id},
        "properties": {"title": {"title": [{"text": {"content": title}}]}},
        "children": [{"object": "block", "type": "paragraph",
                       "paragraph": {"rich_text": [{"text": {"content": content[:2000]}}]}}],
    }
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.post(f"{_BASE}/pages", headers=_headers(token), json=body)
        d = r.json()
        return {"id": d.get("id"), "url": d.get("url")}


async def notion_update_page(page_id: str, properties: dict, token: str) -> dict:
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.patch(f"{_BASE}/pages/{page_id}",
                          headers=_headers(token), json={"properties": properties})
        d = r.json()
        return {"id": d.get("id"), "url": d.get("url")}


async def notion_query_database(database_id: str, filter_json: dict = None, token: str = "") -> list:
    body = {}
    if filter_json:
        body["filter"] = filter_json
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.post(f"{_BASE}/databases/{database_id}/query",
                         headers=_headers(token), json=body)
        results = r.json().get("results", [])
        return [{"id": p.get("id"), "url": p.get("url"), "content": _extract_text(p)} for p in results]


async def notion_create_database_item(database_id: str, properties: dict, token: str) -> dict:
    body = {"parent": {"database_id": database_id}, "properties": properties}
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.post(f"{_BASE}/pages", headers=_headers(token), json=body)
        d = r.json()
        return {"id": d.get("id"), "url": d.get("url")}

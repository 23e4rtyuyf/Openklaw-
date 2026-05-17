import httpx


def _headers(api_key: str) -> dict:
    return {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}


def _base_url(base_id: str, table_name: str) -> str:
    import urllib.parse
    return f"https://api.airtable.com/v0/{base_id}/{urllib.parse.quote(table_name)}"


async def airtable_list_records(base_id: str, table_name: str, api_key: str,
                                 filter_formula: str = "", limit: int = 20) -> list:
    async with httpx.AsyncClient(timeout=15) as c:
        params = {"maxRecords": limit}
        if filter_formula:
            params["filterByFormula"] = filter_formula
        r = await c.get(_base_url(base_id, table_name), headers=_headers(api_key), params=params)
        records = r.json().get("records", [])
        return [{"id": rec["id"], "fields": rec.get("fields", {})} for rec in records]


async def airtable_create_record(base_id: str, table_name: str, fields: dict, api_key: str) -> dict:
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.post(_base_url(base_id, table_name), headers=_headers(api_key),
                         json={"fields": fields})
        d = r.json()
        return {"id": d.get("id"), "fields": d.get("fields", {})}


async def airtable_update_record(base_id: str, table_name: str, record_id: str,
                                  fields: dict, api_key: str) -> dict:
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.patch(f"{_base_url(base_id, table_name)}/{record_id}",
                          headers=_headers(api_key), json={"fields": fields})
        d = r.json()
        return {"id": d.get("id"), "fields": d.get("fields", {})}


async def airtable_delete_record(base_id: str, table_name: str, record_id: str, api_key: str) -> dict:
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.delete(f"{_base_url(base_id, table_name)}/{record_id}",
                           headers=_headers(api_key))
        d = r.json()
        return {"deleted": d.get("deleted"), "id": d.get("id")}

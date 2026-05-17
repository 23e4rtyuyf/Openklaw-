import httpx


async def _get_token(account_id: str, client_id: str, client_secret: str) -> str:
    import base64
    creds = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.post("https://zoom.us/oauth/token",
                         headers={"Authorization": f"Basic {creds}"},
                         params={"grant_type": "account_credentials", "account_id": account_id})
        return r.json().get("access_token", "")


async def zoom_list_meetings(account_id: str, client_id: str, client_secret: str) -> list:
    token = await _get_token(account_id, client_id, client_secret)
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.get("https://api.zoom.us/v2/users/me/meetings",
                        headers={"Authorization": f"Bearer {token}"})
        meetings = r.json().get("meetings", [])
        return [{"id": m["id"], "topic": m["topic"], "start_time": m.get("start_time"),
                 "duration": m.get("duration"), "join_url": m.get("join_url")} for m in meetings]


async def zoom_create_meeting(topic: str, start_time: str, duration: int,
                               account_id: str, client_id: str, client_secret: str) -> dict:
    token = await _get_token(account_id, client_id, client_secret)
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.post("https://api.zoom.us/v2/users/me/meetings",
                         headers={"Authorization": f"Bearer {token}",
                                   "Content-Type": "application/json"},
                         json={"topic": topic, "type": 2, "start_time": start_time,
                               "duration": duration, "settings": {"join_before_host": True}})
        d = r.json()
        return {"id": d.get("id"), "topic": d.get("topic"), "join_url": d.get("join_url"),
                "start_url": d.get("start_url"), "password": d.get("password")}


async def zoom_get_recording(meeting_id: str, account_id: str,
                              client_id: str, client_secret: str) -> dict:
    token = await _get_token(account_id, client_id, client_secret)
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.get(f"https://api.zoom.us/v2/meetings/{meeting_id}/recordings",
                        headers={"Authorization": f"Bearer {token}"})
        d = r.json()
        files = d.get("recording_files", [])
        return {"meeting_id": meeting_id, "topic": d.get("topic"),
                "recordings": [{"type": f.get("recording_type"), "download_url": f.get("download_url"),
                                 "file_size": f.get("file_size")} for f in files]}

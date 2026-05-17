import json
from typing import Optional


def _get_service(service_account_json: str | dict):
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    creds_dict = json.loads(service_account_json) if isinstance(service_account_json, str) else service_account_json
    scopes = ["https://www.googleapis.com/auth/calendar"]
    creds = service_account.Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return build("calendar", "v3", credentials=creds, cache_discovery=False)


async def list_events(calendar_id: str, days_ahead: int = 7, service_account_json: str = "") -> list:
    try:
        from datetime import datetime, timezone, timedelta
        service = _get_service(service_account_json)
        now = datetime.now(timezone.utc)
        end = now + timedelta(days=days_ahead)
        result = service.events().list(
            calendarId=calendar_id,
            timeMin=now.isoformat(),
            timeMax=end.isoformat(),
            singleEvents=True,
            orderBy="startTime",
            maxResults=50,
        ).execute()
        events = []
        for e in result.get("items", []):
            start = e.get("start", {})
            events.append({
                "id": e.get("id"),
                "title": e.get("summary", "(no title)"),
                "start": start.get("dateTime") or start.get("date"),
                "end": (e.get("end", {}).get("dateTime") or e.get("end", {}).get("date")),
                "description": e.get("description", ""),
                "attendees": [a.get("email") for a in e.get("attendees", [])],
            })
        return events
    except Exception as e:
        return [{"error": str(e)}]


async def create_event(calendar_id: str, title: str, start_datetime: str, end_datetime: str,
                       description: str = "", attendees: list = None,
                       service_account_json: str = "") -> dict:
    try:
        service = _get_service(service_account_json)
        event = {
            "summary": title,
            "description": description,
            "start": {"dateTime": start_datetime, "timeZone": "UTC"},
            "end": {"dateTime": end_datetime, "timeZone": "UTC"},
        }
        if attendees:
            event["attendees"] = [{"email": a} for a in attendees]
        result = service.events().insert(calendarId=calendar_id, body=event).execute()
        return {"id": result.get("id"), "link": result.get("htmlLink"), "title": title}
    except Exception as e:
        return {"error": str(e)}


async def update_event(calendar_id: str, event_id: str, updates: dict,
                       service_account_json: str = "") -> dict:
    try:
        service = _get_service(service_account_json)
        existing = service.events().get(calendarId=calendar_id, eventId=event_id).execute()
        existing.update(updates)
        result = service.events().update(calendarId=calendar_id, eventId=event_id, body=existing).execute()
        return {"id": result.get("id"), "updated": True}
    except Exception as e:
        return {"error": str(e)}


async def delete_event(calendar_id: str, event_id: str, service_account_json: str = "") -> str:
    try:
        service = _get_service(service_account_json)
        service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
        return f"Event {event_id} deleted"
    except Exception as e:
        return f"Failed: {e}"


async def check_availability(calendar_id: str, start_datetime: str, end_datetime: str,
                             service_account_json: str = "") -> dict:
    try:
        service = _get_service(service_account_json)
        body = {"timeMin": start_datetime, "timeMax": end_datetime,
                "items": [{"id": calendar_id}]}
        result = service.freebusy().query(body=body).execute()
        busy = result.get("calendars", {}).get(calendar_id, {}).get("busy", [])
        return {"free": len(busy) == 0, "busy_slots": busy}
    except Exception as e:
        return {"error": str(e)}

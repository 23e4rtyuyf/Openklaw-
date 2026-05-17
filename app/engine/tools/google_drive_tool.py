import json
import io


def _get_service(service_account_json: str | dict = ""):
    from googleapiclient.discovery import build
    from app.google_auth import get_google_credentials
    creds = get_google_credentials(service_account_json if isinstance(service_account_json, str) else json.dumps(service_account_json))
    if not creds:
        raise ValueError("No Google credentials available. Sign in with Google in Settings.")
    return build("drive", "v3", credentials=creds, cache_discovery=False)


async def list_files(folder_id: str = "root", service_account_json: str = "", limit: int = 20) -> list:
    try:
        service = _get_service(service_account_json)
        query = f"'{folder_id}' in parents and trashed=false"
        result = service.files().list(q=query, pageSize=limit,
                                      fields="files(id,name,mimeType,size,modifiedTime)").execute()
        return result.get("files", [])
    except Exception as e:
        return [{"error": str(e)}]


async def upload_file(name: str, content: str, folder_id: str = "root",
                      mime_type: str = "text/plain", service_account_json: str = "") -> dict:
    try:
        from googleapiclient.http import MediaIoBaseUpload
        service = _get_service(service_account_json)
        file_metadata = {"name": name, "parents": [folder_id]}
        media = MediaIoBaseUpload(io.BytesIO(content.encode("utf-8")), mimetype=mime_type)
        result = service.files().create(body=file_metadata, media_body=media,
                                        fields="id,name,webViewLink").execute()
        return {"id": result.get("id"), "name": result.get("name"), "link": result.get("webViewLink")}
    except Exception as e:
        return {"error": str(e)}


async def read_file(file_id: str, service_account_json: str = "") -> str:
    try:
        service = _get_service(service_account_json)
        meta = service.files().get(fileId=file_id, fields="mimeType").execute()
        mime = meta.get("mimeType", "")
        if "google-apps.document" in mime:
            resp = service.files().export(fileId=file_id, mimeType="text/plain").execute()
        elif "google-apps.spreadsheet" in mime:
            resp = service.files().export(fileId=file_id, mimeType="text/csv").execute()
        else:
            resp = service.files().get_media(fileId=file_id).execute()
        if isinstance(resp, bytes):
            return resp.decode("utf-8", errors="replace")[:8000]
        return str(resp)[:8000]
    except Exception as e:
        return f"Error reading file: {e}"


async def delete_file(file_id: str, service_account_json: str = "") -> str:
    try:
        service = _get_service(service_account_json)
        service.files().delete(fileId=file_id).execute()
        return f"File {file_id} deleted"
    except Exception as e:
        return f"Failed: {e}"


async def share_file(file_id: str, email: str, role: str = "reader",
                     service_account_json: str = "") -> str:
    try:
        service = _get_service(service_account_json)
        permission = {"type": "user", "role": role, "emailAddress": email}
        service.permissions().create(fileId=file_id, body=permission, sendNotificationEmail=False).execute()
        return f"Shared {file_id} with {email} as {role}"
    except Exception as e:
        return f"Failed: {e}"

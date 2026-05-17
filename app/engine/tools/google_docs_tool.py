import json


def _get_service(service_account_json: str | dict):
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    creds_dict = json.loads(service_account_json) if isinstance(service_account_json, str) else service_account_json
    scopes = ["https://www.googleapis.com/auth/documents",
              "https://www.googleapis.com/auth/drive"]
    creds = service_account.Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return build("docs", "v1", credentials=creds, cache_discovery=False)


def _get_drive_service(service_account_json: str | dict):
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    creds_dict = json.loads(service_account_json) if isinstance(service_account_json, str) else service_account_json
    scopes = ["https://www.googleapis.com/auth/drive"]
    creds = service_account.Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def _extract_text(doc) -> str:
    text_parts = []
    for element in doc.get("body", {}).get("content", []):
        paragraph = element.get("paragraph")
        if paragraph:
            for pe in paragraph.get("elements", []):
                tr = pe.get("textRun")
                if tr:
                    text_parts.append(tr.get("content", ""))
    return "".join(text_parts)[:8000]


async def read_doc(document_id: str, service_account_json: str = "") -> str:
    try:
        service = _get_service(service_account_json)
        doc = service.documents().get(documentId=document_id).execute()
        return _extract_text(doc)
    except Exception as e:
        return f"Error: {e}"


async def create_doc(title: str, content: str, service_account_json: str = "") -> dict:
    try:
        service = _get_service(service_account_json)
        doc = service.documents().create(body={"title": title}).execute()
        doc_id = doc.get("documentId")
        if content:
            service.documents().batchUpdate(
                documentId=doc_id,
                body={"requests": [{"insertText": {"location": {"index": 1}, "text": content}}]},
            ).execute()
        return {"id": doc_id, "title": title, "link": f"https://docs.google.com/document/d/{doc_id}"}
    except Exception as e:
        return {"error": str(e)}


async def append_to_doc(document_id: str, text: str, service_account_json: str = "") -> str:
    try:
        service = _get_service(service_account_json)
        doc = service.documents().get(documentId=document_id).execute()
        end_index = doc.get("body", {}).get("content", [{}])[-1].get("endIndex", 1) - 1
        service.documents().batchUpdate(
            documentId=document_id,
            body={"requests": [{"insertText": {"location": {"index": end_index}, "text": "\n" + text}}]},
        ).execute()
        return f"Appended {len(text)} chars to document"
    except Exception as e:
        return f"Error: {e}"

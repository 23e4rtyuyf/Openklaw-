import json


def _get_service(service_account_json: str | dict = ""):
    from googleapiclient.discovery import build
    from app.google_auth import get_google_credentials
    creds = get_google_credentials(service_account_json if isinstance(service_account_json, str) else json.dumps(service_account_json))
    if not creds:
        raise ValueError("No Google credentials available. Sign in with Google in Settings or provide a service account.")
    return build("sheets", "v4", credentials=creds, cache_discovery=False)


async def read_sheet(spreadsheet_id: str, range_: str, service_account_json: str = "") -> list:
    try:
        service = _get_service(service_account_json)
        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id, range=range_
        ).execute()
        return result.get("values", [])
    except Exception as e:
        return [{"error": str(e)}]


async def append_rows(spreadsheet_id: str, range_: str, rows: list,
                      service_account_json: str = "") -> dict:
    try:
        service = _get_service(service_account_json)
        result = service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range=range_,
            valueInputOption="USER_ENTERED",
            body={"values": rows},
        ).execute()
        return {"updated_rows": result.get("updates", {}).get("updatedRows", 0)}
    except Exception as e:
        return {"error": str(e)}


async def update_cell(spreadsheet_id: str, range_: str, value: str,
                      service_account_json: str = "") -> dict:
    try:
        service = _get_service(service_account_json)
        result = service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=range_,
            valueInputOption="USER_ENTERED",
            body={"values": [[value]]},
        ).execute()
        return {"updated_cells": result.get("updatedCells", 0)}
    except Exception as e:
        return {"error": str(e)}


async def create_sheet(title: str, headers: list, service_account_json: str = "") -> dict:
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        creds_dict = json.loads(service_account_json) if isinstance(service_account_json, str) else service_account_json
        drive_creds = service_account.Credentials.from_service_account_info(
            creds_dict, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        )
        service = build("sheets", "v4", credentials=drive_creds, cache_discovery=False)
        spreadsheet = service.spreadsheets().create(body={"properties": {"title": title}}).execute()
        sheet_id = spreadsheet["spreadsheetId"]
        if headers:
            service.spreadsheets().values().update(
                spreadsheetId=sheet_id, range="A1",
                valueInputOption="USER_ENTERED", body={"values": [headers]}
            ).execute()
        return {"spreadsheet_id": sheet_id, "url": f"https://docs.google.com/spreadsheets/d/{sheet_id}"}
    except Exception as e:
        return {"error": str(e)}


async def delete_rows(spreadsheet_id: str, sheet_id: int, start_index: int, end_index: int,
                      service_account_json: str = "") -> dict:
    try:
        service = _get_service(service_account_json)
        service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={"requests": [{"deleteDimension": {"range": {
                "sheetId": sheet_id, "dimension": "ROWS",
                "startIndex": start_index, "endIndex": end_index
            }}}]}
        ).execute()
        return {"deleted_rows": end_index - start_index}
    except Exception as e:
        return {"error": str(e)}


async def find_and_replace(spreadsheet_id: str, find: str, replace: str,
                           all_sheets: bool = True, service_account_json: str = "") -> dict:
    try:
        service = _get_service(service_account_json)
        result = service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={"requests": [{"findReplace": {
                "find": find, "replacement": replace,
                "allSheets": all_sheets, "matchCase": False
            }}]}
        ).execute()
        rep = result.get("replies", [{}])[0].get("findReplace", {})
        return {"occurrences_changed": rep.get("occurrencesChanged", 0)}
    except Exception as e:
        return {"error": str(e)}


async def batch_update(spreadsheet_id: str, updates: list, service_account_json: str = "") -> dict:
    """updates: list of {range, values} dicts"""
    try:
        service = _get_service(service_account_json)
        data = [{"range": u["range"], "values": u["values"]} for u in updates]
        result = service.spreadsheets().values().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={"valueInputOption": "USER_ENTERED", "data": data}
        ).execute()
        return {"total_updated_cells": result.get("totalUpdatedCells", 0)}
    except Exception as e:
        return {"error": str(e)}


async def format_range(spreadsheet_id: str, sheet_id: int, range_: str,
                       bold: bool = False, bg_color: str = "", service_account_json: str = "") -> dict:
    try:
        service = _get_service(service_account_json)

        def _parse_color(hex_color: str) -> dict:
            h = hex_color.lstrip("#")
            if len(h) == 6:
                return {"red": int(h[0:2], 16)/255, "green": int(h[2:4], 16)/255, "blue": int(h[4:6], 16)/255}
            return {"red": 1, "green": 1, "blue": 1}

        requests = []
        # Parse A1 notation to grid range
        requests.append({"repeatCell": {
            "range": {"sheetId": sheet_id, "startRowIndex": 0, "endRowIndex": 1},
            "cell": {"userEnteredFormat": {
                **({"textFormat": {"bold": bold}} if bold else {}),
                **({"backgroundColor": _parse_color(bg_color)} if bg_color else {}),
            }},
            "fields": "userEnteredFormat(textFormat,backgroundColor)"
        }})
        service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body={"requests": requests}).execute()
        return {"formatted": True}
    except Exception as e:
        return {"error": str(e)}


async def sort_sheet(spreadsheet_id: str, sheet_id: int, column_index: int,
                     ascending: bool = True, service_account_json: str = "") -> dict:
    try:
        service = _get_service(service_account_json)
        service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={"requests": [{"sortRange": {
                "range": {"sheetId": sheet_id},
                "sortSpecs": [{"dimensionIndex": column_index, "sortOrder": "ASCENDING" if ascending else "DESCENDING"}]
            }}]}
        ).execute()
        return {"sorted": True}
    except Exception as e:
        return {"error": str(e)}


async def get_sheet_list(spreadsheet_id: str, service_account_json: str = "") -> list:
    try:
        service = _get_service(service_account_json)
        meta = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        return [{"id": s["properties"]["sheetId"], "title": s["properties"]["title"]}
                for s in meta.get("sheets", [])]
    except Exception as e:
        return [{"error": str(e)}]


async def copy_sheet(source_spreadsheet_id: str, dest_spreadsheet_id: str, sheet_id: int,
                     service_account_json: str = "") -> dict:
    try:
        service = _get_service(service_account_json)
        result = service.spreadsheets().sheets().copyTo(
            spreadsheetId=source_spreadsheet_id, sheetId=sheet_id,
            body={"destinationSpreadsheetId": dest_spreadsheet_id}
        ).execute()
        return {"new_sheet_id": result.get("sheetId")}
    except Exception as e:
        return {"error": str(e)}

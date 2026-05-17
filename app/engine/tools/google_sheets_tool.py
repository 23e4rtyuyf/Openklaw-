import json


def _get_service(service_account_json: str | dict):
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    creds_dict = json.loads(service_account_json) if isinstance(service_account_json, str) else service_account_json
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = service_account.Credentials.from_service_account_info(creds_dict, scopes=scopes)
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

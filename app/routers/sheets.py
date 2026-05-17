import os, uuid, json
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
import aiofiles

router = APIRouter(prefix="/api/sheets", tags=["sheets"])

UPLOAD_DIR = "uploads"


class SheetPreview(BaseModel):
    headers: list[str]
    rows: list[list[str]]
    total_rows: int


class GooglePreviewRequest(BaseModel):
    url: str


class AnalyzeRequest(BaseModel):
    headers: list[str]
    rows: list[list[str]]


@router.post("/upload")
async def upload_sheet(file: UploadFile = File(...)):
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_id = str(uuid.uuid4())
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in (".csv", ".xlsx", ".xls"):
        raise HTTPException(400, "Only CSV and Excel files are supported")

    dest = os.path.join(UPLOAD_DIR, f"{file_id}{ext}")
    async with aiofiles.open(dest, "wb") as f:
        await f.write(await file.read())

    if ext == ".csv":
        headers, rows = _parse_csv(dest)
    else:
        headers, rows = _parse_excel(dest)

    preview_rows = rows[:100]
    return {
        "file_id": file_id,
        "filename": file.filename,
        "rows": len(rows),
        "columns": len(headers),
        "preview": SheetPreview(headers=headers, rows=preview_rows, total_rows=len(rows)),
    }


@router.post("/google/preview", response_model=SheetPreview)
def google_preview(req: GooglePreviewRequest):
    import re
    m = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", req.url)
    if not m:
        raise HTTPException(400, "Could not extract sheet ID from URL")
    sheet_id = m.group(1)

    creds_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not creds_json:
        raise HTTPException(400, "Google service account not configured (set GOOGLE_SERVICE_ACCOUNT_JSON)")

    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        info = json.loads(creds_json)
        creds = service_account.Credentials.from_service_account_info(
            info, scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
        )
        service = build("sheets", "v4", credentials=creds)
        result = service.spreadsheets().values().get(
            spreadsheetId=sheet_id, range="A1:ZZ100"
        ).execute()
        values = result.get("values", [])
        if not values:
            return SheetPreview(headers=[], rows=[], total_rows=0)
        headers = [str(c) for c in values[0]]
        rows = [[str(c) for c in row] for row in values[1:]]
        return SheetPreview(headers=headers, rows=rows, total_rows=len(rows))
    except Exception as e:
        raise HTTPException(500, str(e))


@router.post("/analyze")
def analyze_sheet(req: AnalyzeRequest):
    results: dict = {}
    for i, col in enumerate(req.headers):
        vals = [row[i] for row in req.rows if i < len(row) and row[i] != ""]
        nums = []
        for v in vals:
            try:
                nums.append(float(v))
            except ValueError:
                pass
        if nums:
            results[col] = {
                "type": "numeric",
                "count": len(vals),
                "nulls": len(req.rows) - len(vals),
                "min": min(nums),
                "max": max(nums),
                "mean": round(sum(nums) / len(nums), 4),
            }
        else:
            unique = list(set(vals))
            results[col] = {
                "type": "text",
                "count": len(vals),
                "nulls": len(req.rows) - len(vals),
                "unique": len(unique),
                "sample": unique[:5],
            }
    return results


def _parse_csv(path: str) -> tuple[list[str], list[list[str]]]:
    import csv
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        rows = [r for r in reader if any(c.strip() for c in r)]
    if not rows:
        return [], []
    return rows[0], rows[1:]


def _parse_excel(path: str) -> tuple[list[str], list[list[str]]]:
    try:
        import openpyxl
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        ws = wb.active
        all_rows = []
        for row in ws.iter_rows(values_only=True):
            all_rows.append([str(c) if c is not None else "" for c in row])
        if not all_rows:
            return [], []
        return all_rows[0], all_rows[1:]
    except ImportError:
        raise HTTPException(500, "openpyxl not installed — cannot parse Excel files")

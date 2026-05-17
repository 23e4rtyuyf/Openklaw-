"""
Google OAuth token management.

Stores user OAuth tokens in data/google_tokens.json so Google tools
can use the signed-in user's account instead of a service account.
"""
import json
import os
from pathlib import Path

TOKEN_FILE = Path("data/google_tokens.json")

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/gmail.modify",
    "openid",
    "email",
    "profile",
]


def save_tokens(token_data: dict) -> None:
    TOKEN_FILE.parent.mkdir(exist_ok=True)
    TOKEN_FILE.write_text(json.dumps(token_data))


def load_tokens() -> dict | None:
    if not TOKEN_FILE.exists():
        return None
    try:
        return json.loads(TOKEN_FILE.read_text())
    except Exception:
        return None


def delete_tokens() -> None:
    if TOKEN_FILE.exists():
        TOKEN_FILE.unlink()


def get_user_credentials():
    """Return google.oauth2.credentials.Credentials from stored OAuth tokens, or None."""
    data = load_tokens()
    if not data:
        return None
    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        creds = Credentials(
            token=data.get("access_token"),
            refresh_token=data.get("refresh_token"),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=os.getenv("GOOGLE_CLIENT_ID", ""),
            client_secret=os.getenv("GOOGLE_CLIENT_SECRET", ""),
            scopes=SCOPES,
        )
        # Refresh if expired
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            save_tokens({
                "access_token": creds.token,
                "refresh_token": creds.refresh_token,
                "user_email": data.get("user_email"),
            })
        return creds
    except Exception:
        return None


def get_google_credentials(service_account_json: str = ""):
    """
    Returns the best available credentials:
      1. User OAuth tokens (if signed in via /auth/google)
      2. Service account JSON (from parameter or GOOGLE_SERVICE_ACCOUNT_JSON env var)
      3. None (will cause tool to return an error)
    """
    user_creds = get_user_credentials()
    if user_creds:
        return user_creds

    sa_json = service_account_json or os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "")
    if sa_json:
        from google.oauth2 import service_account
        info = json.loads(sa_json) if isinstance(sa_json, str) else sa_json
        return service_account.Credentials.from_service_account_info(info, scopes=SCOPES)

    return None


def is_connected() -> bool:
    return load_tokens() is not None

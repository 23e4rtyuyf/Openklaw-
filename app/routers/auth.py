"""Google OAuth sign-in routes."""
import os
from fastapi import APIRouter
from fastapi.responses import RedirectResponse, JSONResponse

router = APIRouter(prefix="/auth", tags=["auth"])

_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/gmail.modify",
    "openid",
    "email",
    "profile",
]


def _flow():
    from google_auth_oauthlib.flow import Flow
    client_id = os.getenv("GOOGLE_CLIENT_ID", "")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET", "")
    if not client_id or not client_secret:
        return None

    app_url = os.getenv("APP_URL", "http://localhost:8080").rstrip("/")
    redirect_uri = f"{app_url}/auth/google/callback"

    return Flow.from_client_config(
        {
            "web": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [redirect_uri],
            }
        },
        scopes=_SCOPES,
        redirect_uri=redirect_uri,
    )


@router.get("/google")
def google_login():
    flow = _flow()
    if not flow:
        return JSONResponse(
            {"error": "GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET not configured. Set them in Replit Secrets."},
            status_code=400,
        )
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    return RedirectResponse(auth_url)


@router.get("/google/callback")
def google_callback(code: str = "", error: str = ""):
    if error:
        return RedirectResponse(f"/settings?google_error={error}")

    flow = _flow()
    if not flow:
        return RedirectResponse("/settings?google_error=not_configured")

    try:
        flow.fetch_token(code=code)
        creds = flow.credentials

        # Get user email
        user_email = ""
        try:
            import httpx
            resp = httpx.get(
                "https://www.googleapis.com/oauth2/v1/userinfo",
                headers={"Authorization": f"Bearer {creds.token}"},
            )
            user_email = resp.json().get("email", "")
        except Exception:
            pass

        from app.google_auth import save_tokens
        save_tokens({
            "access_token": creds.token,
            "refresh_token": creds.refresh_token,
            "user_email": user_email,
        })

        return RedirectResponse(f"/settings?google_connected=1&email={user_email}")
    except Exception as e:
        return RedirectResponse(f"/settings?google_error={str(e)[:80]}")


@router.get("/google/status")
def google_status():
    from app.google_auth import load_tokens
    tokens = load_tokens()
    if tokens:
        return {"connected": True, "email": tokens.get("user_email", "")}
    return {"connected": False}


@router.post("/google/disconnect")
def google_disconnect():
    from app.google_auth import delete_tokens
    delete_tokens()
    return {"disconnected": True}

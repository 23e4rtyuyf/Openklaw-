async def send_notification(message: str, sms_to: str = "", credentials: dict = None) -> str:
    """Legacy wrapper — send SMS if configured, else log."""
    if not sms_to:
        return f"Notification (no SMS configured): {message}"
    creds = credentials or {}
    account_sid = creds.get("twilio_account_sid", "")
    auth_token = creds.get("twilio_auth_token", "")
    from_number = creds.get("twilio_from_number", "")
    if not account_sid:
        return f"Notification (Twilio not configured): {message}"
    from app.engine.tools.sms_tool import send_sms
    return await send_sms(sms_to, message, account_sid, auth_token, from_number)

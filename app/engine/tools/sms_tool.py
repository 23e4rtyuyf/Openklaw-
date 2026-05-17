async def send_sms(to: str, message: str, account_sid: str, auth_token: str, from_number: str) -> str:
    import httpx, base64
    credentials = base64.b64encode(f"{account_sid}:{auth_token}".encode()).decode()
    url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(url, data={"To": to, "From": from_number, "Body": message},
                                 headers={"Authorization": f"Basic {credentials}"})
        if resp.status_code in (200, 201):
            return f"SMS sent to {to}"
        return f"SMS failed: {resp.text}"


async def send_whatsapp(to: str, message: str, account_sid: str, auth_token: str, from_number: str) -> str:
    import httpx, base64
    credentials = base64.b64encode(f"{account_sid}:{auth_token}".encode()).decode()
    url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
    wa_from = from_number if from_number.startswith("whatsapp:") else f"whatsapp:{from_number}"
    wa_to = to if to.startswith("whatsapp:") else f"whatsapp:{to}"
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(url, data={"To": wa_to, "From": wa_from, "Body": message},
                                 headers={"Authorization": f"Basic {credentials}"})
        if resp.status_code in (200, 201):
            return f"WhatsApp message sent to {to}"
        return f"WhatsApp failed: {resp.text}"

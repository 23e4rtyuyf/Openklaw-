import imaplib
import smtplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import decode_header
from typing import Optional


def _decode_header_value(val) -> str:
    if val is None:
        return ""
    parts = decode_header(val)
    result = []
    for part, enc in parts:
        if isinstance(part, bytes):
            result.append(part.decode(enc or "utf-8", errors="replace"))
        else:
            result.append(part)
    return " ".join(result)


def _get_body(msg) -> str:
    if msg.is_multipart():
        for part in msg.walk():
            ct = part.get_content_type()
            if ct == "text/plain" and "attachment" not in str(part.get("Content-Disposition", "")):
                payload = part.get_payload(decode=True)
                if payload:
                    return payload.decode(part.get_content_charset() or "utf-8", errors="replace")[:3000]
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            return payload.decode(msg.get_content_charset() or "utf-8", errors="replace")[:3000]
    return ""


async def send_email(to: str, subject: str, body: str, gmail_user: str, app_password: str) -> str:
    msg = MIMEMultipart()
    msg["From"] = gmail_user
    msg["To"] = to
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(gmail_user, app_password)
            server.sendmail(gmail_user, to, msg.as_string())
        return f"Email sent to {to}"
    except Exception as e:
        return f"Email send failed: {e}"


async def reply_email(message_id: str, reply_body: str, gmail_user: str, app_password: str,
                      to: str = "", subject: str = "", thread_id: str = "") -> str:
    msg = MIMEMultipart()
    msg["From"] = gmail_user
    msg["To"] = to or gmail_user
    msg["Subject"] = subject if subject.startswith("Re:") else f"Re: {subject}"
    msg["In-Reply-To"] = message_id
    msg["References"] = message_id
    if thread_id:
        msg["X-GM-THRID"] = thread_id
    msg.attach(MIMEText(reply_body, "plain"))
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(gmail_user, app_password)
            server.sendmail(gmail_user, msg["To"], msg.as_string())
        return f"Reply sent to {msg['To']}"
    except Exception as e:
        return f"Reply failed: {e}"


async def read_emails(gmail_user: str, app_password: str,
                      folder: str = "INBOX", limit: int = 10, unread_only: bool = False) -> list:
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(gmail_user, app_password)
        mail.select(folder)
        criteria = "UNSEEN" if unread_only else "ALL"
        _, ids = mail.search(None, criteria)
        email_ids = ids[0].split()[-limit:] if ids[0] else []
        results = []
        for eid in reversed(email_ids):
            _, data = mail.fetch(eid, "(RFC822)")
            msg = email.message_from_bytes(data[0][1])
            results.append({
                "id": eid.decode(),
                "message_id": msg.get("Message-ID", ""),
                "from": _decode_header_value(msg.get("From")),
                "subject": _decode_header_value(msg.get("Subject")),
                "date": msg.get("Date", ""),
                "body": _get_body(msg),
            })
        mail.logout()
        return results
    except Exception as e:
        return [{"error": str(e)}]


async def search_emails(gmail_user: str, app_password: str, query: str, limit: int = 10) -> list:
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(gmail_user, app_password)
        mail.select("INBOX")
        _, ids = mail.search(None, query)
        email_ids = ids[0].split()[-limit:] if ids[0] else []
        results = []
        for eid in reversed(email_ids):
            _, data = mail.fetch(eid, "(RFC822)")
            msg = email.message_from_bytes(data[0][1])
            results.append({
                "id": eid.decode(),
                "message_id": msg.get("Message-ID", ""),
                "from": _decode_header_value(msg.get("From")),
                "subject": _decode_header_value(msg.get("Subject")),
                "date": msg.get("Date", ""),
                "body": _get_body(msg),
            })
        mail.logout()
        return results
    except Exception as e:
        return [{"error": str(e)}]


async def mark_read(gmail_user: str, app_password: str, message_id: str) -> str:
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(gmail_user, app_password)
        mail.select("INBOX")
        mail.store(message_id.encode(), "+FLAGS", "\\Seen")
        mail.logout()
        return f"Message {message_id} marked as read"
    except Exception as e:
        return f"Failed: {e}"

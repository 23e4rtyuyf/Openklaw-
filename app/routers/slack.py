import hmac
import hashlib
import os
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Agent, Run
from app.engine.agent_runner import run_agent

router = APIRouter(tags=["slack"])

SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET", "")


def _verify_slack_signature(body: bytes, timestamp: str, signature: str) -> bool:
    if not SLACK_SIGNING_SECRET:
        return True
    base = f"v0:{timestamp}:{body.decode()}"
    expected = "v0=" + hmac.new(SLACK_SIGNING_SECRET.encode(), base.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


@router.post("/slack/events")
async def slack_events(request: Request, db: Session = Depends(get_db)):
    body = await request.body()
    ts = request.headers.get("X-Slack-Request-Timestamp", "")
    sig = request.headers.get("X-Slack-Signature", "")

    if not _verify_slack_signature(body, ts, sig):
        raise HTTPException(403, "Invalid signature")

    data = await request.json()

    if data.get("type") == "url_verification":
        return {"challenge": data.get("challenge")}

    event = data.get("event", {})
    if event.get("type") != "message" or event.get("bot_id"):
        return {"ok": True}

    channel_id = event.get("channel", "")
    text = event.get("text", "").strip()

    agent = db.query(Agent).filter(
        Agent.status == "active",
        Agent.credentials["slack_channel"].as_string() == channel_id
    ).first()

    if not agent:
        return {"ok": True}

    run = Run(id=str(uuid.uuid4()), agent_id=agent.id, trigger_type="slack", status="running")
    db.add(run)
    db.commit()

    from app.routers.agents import _agent_data
    result_data = await run_agent(_agent_data(agent), {"message": text, "channel": channel_id})

    run.status = result_data["status"]
    run.steps = result_data["steps"]
    run.result = result_data["result"]
    run.completed_at = datetime.utcnow()
    agent.memory = result_data.get("memory", agent.memory)
    db.commit()

    return {"ok": True}

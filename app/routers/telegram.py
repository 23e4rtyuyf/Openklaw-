import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Agent, Run
from app.engine.agent_runner import run_agent
from app.telegram_bot import parse_update, send_message

router = APIRouter(tags=["telegram"])


@router.post("/telegram")
async def telegram_webhook(request: Request, db: Session = Depends(get_db)):
    body = await request.json()
    update = parse_update(body)
    if not update:
        return {"ok": True}

    chat_id = update["chat_id"]
    text = update["text"].strip()

    if text.startswith("/status"):
        agents = db.query(Agent).filter(Agent.telegram_chat_id == chat_id).all()
        if not agents:
            await send_message(chat_id, "No agents linked to this chat. Set your Telegram chat ID in agent settings.")
        else:
            lines = ["*Your OpenKlaw Agents:*"]
            for a in agents:
                emoji = {"active": "🟢", "paused": "⏸", "draft": "📝"}.get(a.status, "❓")
                lines.append(f"{emoji} *{a.name}* — {a.goal or a.description[:60]}")
            await send_message(chat_id, "\n".join(lines))
        return {"ok": True}

    agent = db.query(Agent).filter(
        Agent.telegram_chat_id == chat_id, Agent.status == "active"
    ).first()

    if not agent:
        await send_message(chat_id, "No active agent linked to this chat. Activate an agent and set this chat ID in its settings.")
        return {"ok": True}

    run = Run(id=str(uuid.uuid4()), agent_id=agent.id, trigger_type="telegram", status="running")
    db.add(run)
    db.commit()

    agent_data = {
        "goal": agent.goal,
        "description": agent.description,
        "memory": agent.memory or {},
        "telegram_chat_id": chat_id,
    }
    result_data = await run_agent(agent_data, {"message": text})

    run.status = result_data["status"]
    run.steps = result_data["steps"]
    run.result = result_data["result"]
    run.completed_at = datetime.utcnow()
    agent.memory = result_data.get("memory", agent.memory)
    db.commit()

    await send_message(chat_id, result_data["result"] or "Done.")
    return {"ok": True}

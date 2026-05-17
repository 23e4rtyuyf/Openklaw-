import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Agent, Run
from app.engine.agent_runner import run_agent

router = APIRouter(tags=["webhooks"])


@router.post("/trigger/{token}")
async def webhook_trigger(token: str, request: Request, db: Session = Depends(get_db)):
    agent = db.query(Agent).filter(Agent.webhook_token == token).first()
    if not agent:
        raise HTTPException(404, "Unknown webhook token")
    if agent.status != "active":
        raise HTTPException(400, "Agent is not active")

    try:
        input_data = await request.json()
    except Exception:
        input_data = {}

    run = Run(id=str(uuid.uuid4()), agent_id=agent.id, trigger_type="webhook", status="running")
    db.add(run)
    db.commit()

    agent_data = {
        "goal": agent.goal,
        "description": agent.description,
        "memory": agent.memory or {},
        "telegram_chat_id": agent.telegram_chat_id or "",
    }
    result_data = await run_agent(agent_data, input_data)

    run.status = result_data["status"]
    run.steps = result_data["steps"]
    run.result = result_data["result"]
    run.completed_at = datetime.utcnow()
    agent.memory = result_data.get("memory", agent.memory)
    db.commit()

    return {"run_id": run.id, "status": run.status, "result": run.result}

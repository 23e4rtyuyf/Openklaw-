import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Agent, Run
from app.schemas import AgentCreate, AgentUpdate, AgentOut, RunRequest, RunOut
from app.engine.agent_runner import run_agent
from app import scheduler as sched_module

router = APIRouter(prefix="/api/agents", tags=["agents"])


def _schedule_agent(agent: Agent):
    trigger = agent.trigger or {}
    if trigger.get("type") == "cron" and agent.status == "active":
        cron_expr = trigger.get("config", {}).get("cron", "0 9 * * *")
        from app.routers.agents import _run_agent_cron
        sched_module.register_agent(agent.id, cron_expr, _run_agent_cron)
    else:
        sched_module.unregister_agent(agent.id)


async def _run_agent_cron(agent_id: str):
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent or agent.status != "active":
            return
        run = Run(id=str(uuid.uuid4()), agent_id=agent.id, trigger_type="cron", status="running")
        db.add(run)
        db.commit()

        agent_data = {
            "goal": agent.goal,
            "description": agent.description,
            "memory": agent.memory or {},
            "telegram_chat_id": agent.telegram_chat_id or "",
        }
        result_data = await run_agent(agent_data)

        run.status = result_data["status"]
        run.steps = result_data["steps"]
        run.result = result_data["result"]
        run.completed_at = datetime.utcnow()
        agent.memory = result_data.get("memory", agent.memory)
        db.commit()
    finally:
        db.close()


@router.get("", response_model=list[AgentOut])
def list_agents(db: Session = Depends(get_db)):
    return db.query(Agent).order_by(Agent.created_at.desc()).all()


@router.post("", response_model=AgentOut)
def create_agent(data: AgentCreate, db: Session = Depends(get_db)):
    token = str(uuid.uuid4()) if data.trigger.get("type") == "webhook" else str(uuid.uuid4())
    agent = Agent(
        id=str(uuid.uuid4()),
        name=data.name,
        description=data.description,
        goal=data.goal,
        tools=data.tools,
        trigger=data.trigger,
        webhook_token=token,
        telegram_chat_id=data.telegram_chat_id,
        status="draft",
    )
    db.add(agent)
    db.commit()
    db.refresh(agent)
    return agent


@router.get("/{agent_id}", response_model=AgentOut)
def get_agent(agent_id: str, db: Session = Depends(get_db)):
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(404, "Agent not found")
    return agent


@router.put("/{agent_id}", response_model=AgentOut)
def update_agent(agent_id: str, data: AgentUpdate, db: Session = Depends(get_db)):
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(404, "Agent not found")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(agent, field, value)
    agent.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(agent)
    _schedule_agent(agent)
    return agent


@router.delete("/{agent_id}")
def delete_agent(agent_id: str, db: Session = Depends(get_db)):
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(404, "Agent not found")
    sched_module.unregister_agent(agent_id)
    db.delete(agent)
    db.commit()
    return {"ok": True}


@router.post("/{agent_id}/run", response_model=RunOut)
async def run_agent_now(agent_id: str, req: RunRequest = None, db: Session = Depends(get_db)):
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(404, "Agent not found")

    run = Run(id=str(uuid.uuid4()), agent_id=agent.id, trigger_type="manual", status="running")
    db.add(run)
    db.commit()

    agent_data = {
        "goal": agent.goal,
        "description": agent.description,
        "memory": agent.memory or {},
        "telegram_chat_id": agent.telegram_chat_id or "",
    }
    input_data = (req.input_data if req else None) or {}
    result_data = await run_agent(agent_data, input_data)

    run.status = result_data["status"]
    run.steps = result_data["steps"]
    run.result = result_data["result"]
    run.completed_at = datetime.utcnow()
    agent.memory = result_data.get("memory", agent.memory)
    db.commit()
    db.refresh(run)
    return run

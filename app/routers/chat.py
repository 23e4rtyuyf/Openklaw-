import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Message, Agent
from app.schemas import MessageIn, MessageOut, ChatResponse
from app.ai.agent_builder import build_agent_from_chat

router = APIRouter(prefix="/api/agents", tags=["chat"])


@router.get("/{agent_id}/messages", response_model=list[MessageOut])
def get_messages(agent_id: str, db: Session = Depends(get_db)):
    return (
        db.query(Message)
        .filter(Message.agent_id == agent_id)
        .order_by(Message.created_at.asc())
        .all()
    )


@router.post("/{agent_id}/chat", response_model=ChatResponse)
async def chat_with_agent(agent_id: str, body: MessageIn, db: Session = Depends(get_db)):
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(404, "Agent not found")

    user_msg = Message(
        id=str(uuid.uuid4()),
        agent_id=agent_id,
        role="user",
        content=body.message,
    )
    db.add(user_msg)
    db.commit()

    history = (
        db.query(Message)
        .filter(Message.agent_id == agent_id)
        .order_by(Message.created_at.asc())
        .all()
    )
    messages_for_ai = [{"role": m.role, "content": m.content} for m in history]

    reply, agent_config = await build_agent_from_chat(messages_for_ai)

    assistant_msg = Message(
        id=str(uuid.uuid4()),
        agent_id=agent_id,
        role="assistant",
        content=reply,
    )
    db.add(assistant_msg)
    db.commit()

    if agent_config:
        agent.name = agent_config.get("name", agent.name)
        agent.goal = agent_config.get("goal", agent.goal)
        agent.tools = agent_config.get("tools", agent.tools)
        if "suggested_trigger" in agent_config:
            agent.trigger = agent_config["suggested_trigger"]
        db.commit()

    all_messages = db.query(Message).filter(Message.agent_id == agent_id).order_by(Message.created_at.asc()).all()
    return ChatResponse(
        reply=reply,
        agent_config=agent_config,
        messages=[MessageOut.model_validate(m) for m in all_messages],
    )


@router.post("/chat/new", response_model=ChatResponse)
async def new_chat(body: MessageIn, db: Session = Depends(get_db)):
    """Start a new conversation without an existing agent."""
    messages_for_ai = [{"role": "user", "content": body.message}]
    reply, agent_config = await build_agent_from_chat(messages_for_ai)

    agent_id = None
    if agent_config:
        import uuid as _uuid
        agent = Agent(
            id=str(_uuid.uuid4()),
            name=agent_config.get("name", "New Agent"),
            description=body.message,
            goal=agent_config.get("goal"),
            tools=agent_config.get("tools", []),
            trigger=agent_config.get("suggested_trigger", {"type": "manual", "config": {}}),
            webhook_token=str(_uuid.uuid4()),
            status="draft",
        )
        db.add(agent)
        db.commit()
        agent_id = agent.id

    user_msg = Message(id=str(uuid.uuid4()), agent_id=agent_id, role="user", content=body.message)
    assistant_msg = Message(id=str(uuid.uuid4()), agent_id=agent_id, role="assistant", content=reply)
    db.add(user_msg)
    db.add(assistant_msg)
    db.commit()

    msgs = [MessageOut.model_validate(user_msg), MessageOut.model_validate(assistant_msg)]
    return ChatResponse(reply=reply, agent_config=agent_config, messages=msgs)

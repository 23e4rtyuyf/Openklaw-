from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel


class AgentCreate(BaseModel):
    name: str
    description: str
    goal: Optional[str] = None
    tools: list[str] = []
    trigger: dict = {"type": "manual", "config": {}}
    sms_to: Optional[str] = None
    credentials: dict = {}


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    goal: Optional[str] = None
    tools: Optional[list[str]] = None
    trigger: Optional[dict] = None
    sms_to: Optional[str] = None
    credentials: Optional[dict] = None
    status: Optional[str] = None


class AgentOut(BaseModel):
    id: str
    name: str
    description: str
    goal: Optional[str]
    tools: list[str]
    trigger: dict
    webhook_token: Optional[str]
    sms_to: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RunOut(BaseModel):
    id: str
    agent_id: str
    trigger_type: str
    status: str
    plan: list
    steps: list
    result: Optional[str]
    started_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class MessageIn(BaseModel):
    message: str
    agent_id: Optional[str] = None


class MessageOut(BaseModel):
    id: str
    agent_id: Optional[str]
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class ChatResponse(BaseModel):
    reply: str
    agent_config: Optional[dict] = None
    messages: list[MessageOut] = []


class RunRequest(BaseModel):
    input_data: dict = {}

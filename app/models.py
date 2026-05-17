import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import relationship
from app.database import Base


def gen_uuid():
    return str(uuid.uuid4())


class Agent(Base):
    __tablename__ = "agents"

    id = Column(String, primary_key=True, default=gen_uuid)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    goal = Column(Text, nullable=True)
    tools = Column(JSON, default=list)
    trigger = Column(JSON, default=lambda: {"type": "manual", "config": {}})
    webhook_token = Column(String, unique=True, nullable=True)
    sms_to = Column(String, nullable=True)
    memory = Column(JSON, default=dict)
    credentials = Column(JSON, default=dict)
    status = Column(String, default="draft")  # draft | active | paused
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    runs = relationship("Run", back_populates="agent", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="agent", cascade="all, delete-orphan")


class Run(Base):
    __tablename__ = "runs"

    id = Column(String, primary_key=True, default=gen_uuid)
    agent_id = Column(String, ForeignKey("agents.id"), nullable=False)
    trigger_type = Column(String, default="manual")
    status = Column(String, default="running")  # running | success | failed
    plan = Column(JSON, default=list)
    steps = Column(JSON, default=list)
    result = Column(Text, nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    agent = relationship("Agent", back_populates="runs")


class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=gen_uuid)
    agent_id = Column(String, ForeignKey("agents.id"), nullable=True)
    role = Column(String, nullable=False)  # user | assistant
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    agent = relationship("Agent", back_populates="messages")

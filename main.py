import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv

load_dotenv()

from app.database import engine, Base, run_migrations
from app.models import Agent, Run, Message
from app.scheduler import start_scheduler, stop_scheduler, register_agent
from app.routers import agents, runs, chat, webhooks
from app.routers import slack as slack_router

Base.metadata.create_all(bind=engine)
run_migrations()


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    _load_cron_agents()
    yield
    stop_scheduler()


def _load_cron_agents():
    from app.database import SessionLocal
    from app.routers.agents import _run_agent_cron
    db = SessionLocal()
    try:
        active_agents = db.query(Agent).filter(Agent.status == "active").all()
        for agent in active_agents:
            trigger = agent.trigger or {}
            if trigger.get("type") == "cron":
                cron_expr = trigger.get("config", {}).get("cron", "0 9 * * *")
                register_agent(agent.id, cron_expr, _run_agent_cron)
    finally:
        db.close()


app = FastAPI(title="OpenKlaw", description="AI Superagents Platform", lifespan=lifespan)

app.include_router(agents.router)
app.include_router(runs.router)
app.include_router(chat.router)
app.include_router(webhooks.router)
app.include_router(slack_router.router)

app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")


@app.get("/")
def serve_frontend():
    return FileResponse("frontend/index.html")


@app.get("/health")
def health():
    return {"status": "ok", "app": "OpenKlaw"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)

import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

scheduler = AsyncIOScheduler()


def start_scheduler():
    if not scheduler.running:
        scheduler.start()


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)


def register_agent(agent_id: str, cron_expr: str, run_fn):
    job_id = f"agent_{agent_id}"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
    trigger = CronTrigger.from_crontab(cron_expr)
    scheduler.add_job(run_fn, trigger, id=job_id, args=[agent_id], replace_existing=True)


def unregister_agent(agent_id: str):
    job_id = f"agent_{agent_id}"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)

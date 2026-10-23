"""任务调度 Agent（支撑）：APScheduler 定时任务 + 心跳监控 + 推送触发器。"""

from __future__ import annotations

import json
from datetime import UTC, datetime

import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select

from ...core.errors import AppError, NotFound
from ...infra.db import get_sessionmaker
from .base import AgentMessage, AgentReply, BaseAgent, register_agent
from .gateway import push_service
from .jobinfo_agent import dedupe_jobs, expire_jobs
from .models import ScheduledTask

log = structlog.get_logger()

_scheduler: AsyncIOScheduler | None = None


def get_scheduler() -> AsyncIOScheduler | None:
    return _scheduler


async def start_scheduler() -> None:
    """应用启动时初始化调度器并从 DB 恢复任务。"""
    global _scheduler
    if _scheduler is not None:
        return
    _scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")
    _scheduler.start()
    await sync_tasks()
    log.info("scheduler_started", jobs=len(_scheduler.get_jobs()))


async def stop_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        log.info("scheduler_stopped")


async def sync_tasks() -> None:
    """将 DB 中启用的任务同步到调度器。"""
    if _scheduler is None:
        return
    async with get_sessionmaker()() as session:
        tasks = (
            await session.scalars(select(ScheduledTask).where(ScheduledTask.enabled == 1))
        ).all()
    want = {f"task-{t.id}" for t in tasks}
    for job in _scheduler.get_jobs():
        if job.id not in want:
            _scheduler.remove_job(job.id)
    for task in tasks:
        _register_job(task)


def _register_job(task: ScheduledTask) -> None:
    assert _scheduler is not None
    _scheduler.add_job(
        run_scheduled_task,
        CronTrigger.from_crontab(task.cron, timezone="Asia/Shanghai"),
        id=f"task-{task.id}",
        name=task.name,
        kwargs={"task_id": task.id},
        replace_existing=True,
        misfire_grace_time=300,
    )


async def run_scheduled_task(task_id: int) -> dict:
    """调度入口：执行任务并回写心跳/状态，完成后推送管理员。"""
    now = datetime.now(UTC)
    async with get_sessionmaker()() as session:
        task = await session.get(ScheduledTask, task_id)
        if task is None or not task.enabled:
            return {"skipped": True}
        task.heartbeat_at = now
        await session.commit()
        task_type, task_name = task.task_type, task.name

    try:
        params = json.loads(task.params or "{}")
        message = await _dispatch(task_type, params)
        status = "SUCCESS"
    except Exception as exc:  # noqa: BLE001
        message, status = str(exc)[:480], "FAILED"
        log.warning("scheduled_task_failed", task_id=task_id, error=str(exc))

    now = datetime.now(UTC)
    async with get_sessionmaker()() as session:
        task = await session.get(ScheduledTask, task_id)
        if task is not None:
            task.last_run_at = now
            task.heartbeat_at = now
            task.last_status = status
            task.last_message = message
            await session.commit()

    await push_service.send_admin(f"[JobClaw 调度] {task_name} {status}: {message[:200]}")
    return {"task_id": task_id, "status": status, "message": message}


async def _dispatch(task_type: str, params: dict) -> str:
    if task_type == "collect_url":
        from .collect_agent import run_url_collect

        url = params.get("url", "")
        if not url:
            raise ValueError("缺少 url 参数")
        result = await run_url_collect(url, created_by=None)
        return f"采集 {result.status} conf={result.confidence:.2f} {result.title or ''}".strip()
    if task_type == "expire_cleanup":
        count = await expire_jobs(int(params.get("days", 90)))
        return f"过期清理：{count} 个职位下线"
    if task_type == "dedupe":
        count = await dedupe_jobs()
        return f"去重：{count} 个重复职位下线"
    if task_type == "recommend_push":
        user_id = int(params["user_id"])
        from .recommend_agent import recommend_for_user

        text, _, _ = await recommend_for_user(user_id)
        channel = await push_service.push_to_user(user_id, text)
        return f"推荐已推送（channel={channel}）" if channel != "none" else "用户未绑定 IM，跳过推送"
    raise ValueError(f"未知任务类型: {task_type}")


async def create_task(
    *, name: str, task_type: str, cron: str, params: dict | None, created_by: int | None
) -> ScheduledTask:
    if task_type not in ScheduledTask.TASK_TYPES:
        raise AppError(
            f"task_type must be one of {ScheduledTask.TASK_TYPES}",
            code=40000,
            status_code=400,
        )
    try:
        CronTrigger.from_crontab(cron)
    except ValueError as exc:
        raise AppError(f"invalid cron: {exc}", code=40000, status_code=400) from exc

    async with get_sessionmaker()() as session:
        task = ScheduledTask(
            name=name,
            task_type=task_type,
            cron=cron,
            params=json.dumps(params or {}, ensure_ascii=False),
            created_by=created_by,
        )
        session.add(task)
        await session.commit()
        await session.refresh(task)
    if _scheduler is not None:
        _register_job(task)
    return task


async def list_tasks() -> list[ScheduledTask]:
    async with get_sessionmaker()() as session:
        return list(
            (await session.scalars(select(ScheduledTask).order_by(ScheduledTask.id))).all()
        )


async def set_task_enabled(task_id: int, enabled: bool) -> ScheduledTask:
    async with get_sessionmaker()() as session:
        task = await session.get(ScheduledTask, task_id)
        if task is None:
            raise NotFound(f"task not found: {task_id}")
        task.enabled = 1 if enabled else 0
        await session.commit()
        await session.refresh(task)
    if _scheduler is not None:
        if enabled:
            _register_job(task)
        else:
            job = _scheduler.get_job(f"task-{task_id}")
            if job is not None:
                _scheduler.remove_job(f"task-{task_id}")
    return task


async def delete_task(task_id: int) -> None:
    async with get_sessionmaker()() as session:
        task = await session.get(ScheduledTask, task_id)
        if task is None:
            raise NotFound(f"task not found: {task_id}")
        await session.delete(task)
        await session.commit()
    if _scheduler is not None:
        job = _scheduler.get_job(f"task-{task_id}")
        if job is not None:
            _scheduler.remove_job(f"task-{task_id}")


def _format_task(task: ScheduledTask) -> str:
    state = "启用" if task.enabled else "停用"
    last = task.last_run_at.strftime("%m-%d %H:%M") if task.last_run_at else "未运行"
    status = task.last_status or "-"
    return f"#{task.id} {task.name} | {task.task_type} | {task.cron} | {state} | 上次: {last} {status}"


@register_agent
class SchedulerAgent(BaseAgent):
    name = "scheduler"
    description = "任务调度：定时采集/清理/推送，心跳监控"
    admin_only = True

    async def handle(self, msg: AgentMessage) -> AgentReply:
        text = msg.text.strip()
        if "列表" in text or "状态" in text or "任务" in text:
            tasks = await list_tasks()
            if not tasks:
                lines = ["暂无定时任务。可通过管理端「智能体 → 任务调度」创建："]
            else:
                lines = [f"共 {len(tasks)} 个定时任务："]
            lines += [f"· {_format_task(t)}" for t in tasks]
            return AgentReply(text="\n".join(lines), agent=self.name, intent="schedule.list")
        return AgentReply(
            text="发送「定时任务列表」查看任务与心跳状态；任务创建/启停请在管理端操作。",
            agent=self.name,
            intent="schedule.guide",
        )

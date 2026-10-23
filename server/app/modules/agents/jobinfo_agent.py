"""校招信息管理 Agent（业务）：统计 / 去重更新 / 过期清理 / 下线。"""

from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta

import structlog
from sqlalchemy import func, select, update

from ...infra.db import get_sessionmaker
from ..jobs.models import Job
from .base import AgentMessage, AgentReply, BaseAgent, register_agent

log = structlog.get_logger()

DAYS_RE = re.compile(r"(\d+)\s*天")


async def job_stats() -> dict:
    """按状态统计职位数。"""
    async with get_sessionmaker()() as session:
        rows = await session.execute(
            select(Job.status, func.count()).group_by(Job.status)
        )
        by_status = {status: count for status, count in rows}
    return {"total": sum(by_status.values()), **by_status}


async def expire_jobs(days: int = 90) -> int:
    """将超过 N 天未更新的在招职位下线（OFFLINE）。"""
    cutoff = datetime.now(UTC) - timedelta(days=days)
    async with get_sessionmaker()() as session:
        result = await session.execute(
            update(Job)
            .where(Job.status == "PUBLISHED", Job.published_at < cutoff)
            .values(status="OFFLINE")
        )
        await session.commit()
    return result.rowcount or 0


async def dedupe_jobs() -> int:
    """同公司+同标题只保留最新一条，其余下线。"""
    async with get_sessionmaker()() as session:
        jobs = (
            (
                await session.scalars(
                    select(Job)
                    .where(Job.status == "PUBLISHED")
                    .order_by(Job.company, Job.title, Job.id.desc())
                )
            )
            .all()
        )
    seen: set[tuple[str, str]] = set()
    stale_ids: list[int] = []
    for job in jobs:
        key = (job.company, job.title)
        if key in seen:
            stale_ids.append(job.id)
        else:
            seen.add(key)
    if stale_ids:
        async with get_sessionmaker()() as session:
            await session.execute(
                update(Job).where(Job.id.in_(stale_ids)).values(status="OFFLINE")
            )
            await session.commit()
    return len(stale_ids)


def _format_stats(stats: dict) -> str:
    lines = [f"职位库共 {stats['total']} 个职位："]
    for status, count in sorted(stats.items()):
        if status != "total":
            lines.append(f"· {status}: {count}")
    return "\n".join(lines)


@register_agent
class JobInfoAgent(BaseAgent):
    name = "jobinfo"
    description = "校招信息管理：统计 / 去重更新 / 过期清理"

    async def handle(self, msg: AgentMessage) -> AgentReply:
        text = msg.text.strip()

        # 查询统计：所有用户可用
        if any(kw in text for kw in ("统计", "多少", "职位库")):
            stats = await job_stats()
            return AgentReply(
                text=_format_stats(stats),
                agent=self.name,
                intent="jobinfo.stats",
                data=stats,
            )

        # 写操作：仅管理员
        if msg.role != "ADMIN":
            return AgentReply(
                text="职位管理操作（去重/过期清理/下线）需要管理员权限。",
                agent=self.name,
                intent="jobinfo.denied",
            )

        if "去重" in text:
            count = await dedupe_jobs()
            return AgentReply(
                text=f"去重完成：{count} 个重复职位已下线（同公司同标题保留最新）。",
                agent=self.name,
                intent="jobinfo.dedupe",
                data={"offlined": count},
            )

        if "过期" in text or "清理" in text:
            m = DAYS_RE.search(text)
            days = int(m.group(1)) if m else 90
            count = await expire_jobs(days)
            return AgentReply(
                text=f"过期清理完成：{count} 个超过 {days} 天的在招职位已下线。",
                agent=self.name,
                intent="jobinfo.expire",
                data={"offlined": count, "days": days},
            )

        return AgentReply(
            text=(
                "我可以帮你管理职位库：\n"
                "· 职位统计 —— 查看各状态数量\n"
                "· 去重职位 —— 同公司同标题保留最新\n"
                "· 清理过期职位 / 清理30天过期 —— 按天数下线旧职位"
            ),
            agent=self.name,
            intent="jobinfo.guide",
        )

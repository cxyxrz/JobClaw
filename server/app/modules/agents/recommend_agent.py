"""推荐 Agent（业务）：基于画像召回 + 打分排序。"""

from __future__ import annotations

import structlog

from ...infra.db import get_sessionmaker
from ..jobs.models import Job
from ..jobs.service import query_jobs
from .base import AgentMessage, AgentReply, BaseAgent, register_agent
from .profile_agent import _strip_fillers, get_profile, record_behavior

log = structlog.get_logger()

WEIGHTS = {
    "city": 30,
    "batch": 20,
    "category": 20,
    "keyword_title": 15,
    "keyword_desc": 5,
    "salary": 5,
}


def _match_points(job: Job, profile: dict) -> list[str]:
    """命中的匹配维度（用于回复展示）。"""
    points = []
    if profile["city"] and job.city == profile["city"]:
        points.append("城市")
    if profile["batch"] and job.batch == profile["batch"]:
        points.append("届别")
    if profile["category"] and job.category == profile["category"]:
        points.append("方向")
    return points


def score_job(job: Job, profile: dict, extra_kws: list[str]) -> int:
    """画像打分：城市/届别/方向/关键词命中加权。"""
    score = 0
    if profile["city"] and job.city == profile["city"]:
        score += WEIGHTS["city"]
    if profile["batch"] and job.batch == profile["batch"]:
        score += WEIGHTS["batch"]
    if profile["category"] and job.category == profile["category"]:
        score += WEIGHTS["category"]
    kws = set(filter(None, profile["keywords"].split())) | set(extra_kws)
    for kw in kws:
        if not kw:
            continue
        if kw in job.title:
            score += WEIGHTS["keyword_title"]
        elif kw in (job.description or ""):
            score += WEIGHTS["keyword_desc"]
    if job.salary_text:
        score += WEIGHTS["salary"]
    return score


def _job_brief(job: Job, score: int) -> dict:
    return {
        "id": job.id,
        "title": job.title,
        "company": job.company,
        "city": job.city,
        "batch": job.batch,
        "salary_text": job.salary_text,
        "score": score,
    }


def format_recommend(top: list[Job], scored: dict[int, int], profile: dict, total: int) -> str:
    if not top:
        return "暂无在招职位，稍后再来看看吧。"
    lines = [f"为你推荐 {len(top)} 个职位（按匹配度排序，共 {total} 个在招）："]
    for i, job in enumerate(top, 1):
        points = _match_points(job, profile)
        suffix = f"（匹配：{'、'.join(points)}）" if points else ""
        salary = f" · {job.salary_text}" if job.salary_text else ""
        lines.append(f"{i}. 【{job.title}】{job.company} · {job.city} · {job.batch}{salary}{suffix}")
    if not any(profile.values()):
        lines.append("—— 你还没设置求职偏好，发送「我想找北京的后端工作」可获得更精准的推荐")
    return "\n".join(lines)


async def recommend_for_user(user_id: int, extra_text: str = "") -> tuple[str, list[dict], int]:
    """生成推荐文本与结构化结果（对话/定时推送共用）。"""
    profile = await get_profile(user_id)
    extra_kws = [
        w for w in _strip_fillers(extra_text).split() if len(w) >= 2
    ][:5]
    async with get_sessionmaker()() as session:
        items, total = await query_jobs(session, status="PUBLISHED", page_size=100)
    scored = sorted(((score_job(j, profile, extra_kws), j) for j in items), key=lambda x: (-x[0], x[1].id))
    positive = [j for s, j in scored if s > 0][:5]
    top = positive if positive else [j for _, j in scored[:5]]
    score_map = {j.id: s for s, j in scored}
    text = format_recommend(top, score_map, profile, total)
    return text, [_job_brief(j, score_map.get(j.id, 0)) for j in top], total


@register_agent
class RecommendAgent(BaseAgent):
    name = "recommend"
    description = "职位推荐：基于画像的实时召回与排序"

    async def handle(self, msg: AgentMessage) -> AgentReply:
        text, jobs, total = await recommend_for_user(msg.user_id, msg.text)
        await record_behavior(
            msg.user_id, "recommend", detail=",".join(str(j["id"]) for j in jobs)
        )
        return AgentReply(
            text=text,
            agent=self.name,
            intent="recommend",
            data={"jobs": jobs, "total": total},
        )

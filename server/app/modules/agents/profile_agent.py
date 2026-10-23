"""用户画像 Agent（业务）：偏好存储 / 行为记录 / 画像查询。"""

from __future__ import annotations

import re

import structlog
from sqlalchemy import select

from ...infra.db import get_sessionmaker
from ..collect.extractor import BATCH_PATTERN, CATEGORY_KEYWORDS, CITY_KEYWORDS
from .base import AgentMessage, AgentReply, BaseAgent, register_agent
from .models import UserBehavior, UserProfile

log = structlog.get_logger()

VIEW_KWS = ["我的偏好", "我的画像", "查看偏好", "查看画像", "我的求职意向"]

# 解析关键词时剔除的填充词（长词优先）
FILLERS = [
    "我想找", "想找", "希望", "求职", "意向", "工作", "职位", "岗位", "方向",
    "偏好", "设置", "兴趣", "相关", "喜欢", "帮我", "推荐", "优先", "我", "的", "找",
]


def _strip_fillers(text: str) -> str:
    for word in sorted(FILLERS, key=len, reverse=True):
        text = text.replace(word, " ")
    return text


def parse_preferences(text: str) -> dict[str, str]:
    """从自然语言解析偏好：城市 / 届别 / 方向 / 关键词。"""
    prefs: dict[str, str] = {}
    for city in CITY_KEYWORDS:
        if city in text:
            prefs["city"] = city
            break
    m = BATCH_PATTERN.search(text)
    if m:
        prefs["batch"] = m.group(1)
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            prefs["category"] = category
            break
    remain = _strip_fillers(text)
    for value in list(prefs.values()):
        remain = remain.replace(value, " ")
    kws = [
        w
        for w in re.split(r"[\s,，、。；;/]+", remain)
        if len(w) >= 2 and not w.isdigit()
    ][:5]
    if kws:
        prefs["keywords"] = " ".join(kws)
    return prefs


async def get_profile(user_id: int) -> dict:
    """读取画像，无记录时返回空默认值。"""
    async with get_sessionmaker()() as session:
        profile = (
            await session.scalars(select(UserProfile).where(UserProfile.user_id == user_id))
        ).first()
    if profile is None:
        return {"city": "", "batch": "", "category": "", "keywords": ""}
    return {
        "city": profile.city,
        "batch": profile.batch,
        "category": profile.category,
        "keywords": profile.keywords,
    }


async def update_profile(user_id: int, prefs: dict[str, str]) -> dict:
    """增量更新画像（只覆盖本次识别到的字段）。"""
    async with get_sessionmaker()() as session:
        profile = (
            await session.scalars(select(UserProfile).where(UserProfile.user_id == user_id))
        ).first()
        if profile is None:
            profile = UserProfile(user_id=user_id)
            session.add(profile)
        for field in ("city", "batch", "category", "keywords"):
            if prefs.get(field):
                setattr(profile, field, prefs[field])
        await session.commit()
    return await get_profile(user_id)


async def record_behavior(
    user_id: int, action: str, *, target_id: str | None = None, detail: str = ""
) -> None:
    """记录一次用户行为事件。"""
    try:
        async with get_sessionmaker()() as session:
            session.add(
                UserBehavior(user_id=user_id, action=action, target_id=target_id, detail=detail)
            )
            await session.commit()
    except Exception as exc:  # noqa: BLE001
        log.warning("behavior_record_failed", error=str(exc))


def format_profile(profile: dict) -> str:
    if not any(profile.values()):
        return "你还没有设置求职偏好。发送「我想找北京的后端工作」，我会记住你的偏好。"
    lines = ["你的求职偏好："]
    if profile["city"]:
        lines.append(f"· 城市：{profile['city']}")
    if profile["batch"]:
        lines.append(f"· 届别：{profile['batch']}")
    if profile["category"]:
        lines.append(f"· 方向：{profile['category']}")
    if profile["keywords"]:
        lines.append(f"· 关键词：{profile['keywords'].replace(' ', '、')}")
    return "\n".join(lines)


@register_agent
class ProfileAgent(BaseAgent):
    name = "profile"
    description = "用户画像：偏好存储、行为记录、画像查询"

    async def handle(self, msg: AgentMessage) -> AgentReply:
        text = msg.text.strip()

        # 查看画像
        if any(kw in text for kw in VIEW_KWS):
            profile = await get_profile(msg.user_id)
            return AgentReply(
                text=format_profile(profile),
                agent=self.name,
                intent="profile.view",
                data={**profile, "keywords": profile["keywords"].split()},
            )

        # 设置偏好：从消息中解析
        prefs = parse_preferences(text)
        if not prefs:
            return AgentReply(
                text=(
                    "请告诉我你的求职偏好，例如：\n"
                    "「我想找北京的后端工作」「我是2026届，想去杭州」「我的偏好」"
                ),
                agent=self.name,
                intent="profile.guide",
            )
        profile = await update_profile(msg.user_id, prefs)
        await record_behavior(msg.user_id, "profile_update", detail=str(prefs))
        return AgentReply(
            text=f"已更新你的求职偏好：\n{format_profile(profile)}",
            agent=self.name,
            intent="profile.update",
            data={**profile, "keywords": profile["keywords"].split()},
        )

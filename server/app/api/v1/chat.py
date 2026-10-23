"""对话接口：Web 端聊天（对话管理 Agent 入口）+ 历史记录 + 画像查询/设置。"""

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.permissions import AuthSubject, current_subject
from ...core.response import ApiResponse
from ...infra.db import get_session
from ...modules.agents.base import AgentMessage
from ...modules.agents.dialogue import dialogue_agent
from ...modules.agents.models import ChatMessage
from ...modules.agents.profile_agent import get_profile, update_profile

router = APIRouter(prefix="/chat", tags=["agents"])


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


class ChatData(BaseModel):
    reply: str
    agent: str
    intent: str
    data: dict


@router.post("", response_model=ApiResponse[ChatData])
async def send_chat(
    body: ChatRequest, subject: AuthSubject = Depends(current_subject)
) -> ApiResponse[ChatData]:
    """发送消息，由对话管理 Agent 识别意图并路由到具体 Agent。"""
    msg = AgentMessage(
        user_id=subject.user_id,
        username="",
        role=subject.role,
        text=body.message.strip(),
        session_id=f"web:{subject.user_id}",
        channel="web",
    )
    reply = await dialogue_agent.handle(msg)
    return ApiResponse(
        data=ChatData(reply=reply.text, agent=reply.agent, intent=reply.intent, data=reply.data)
    )


class ChatHistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: str
    content: str
    agent: str
    intent: str
    created_at: datetime


@router.get("/history", response_model=ApiResponse[list[ChatHistoryItem]])
async def chat_history(
    limit: int = Query(default=20, ge=1, le=100),
    subject: AuthSubject = Depends(current_subject),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[list[ChatHistoryItem]]:
    rows = (
        await session.scalars(
            select(ChatMessage)
            .where(ChatMessage.user_id == subject.user_id)
            .order_by(ChatMessage.id.desc())
            .limit(limit)
        )
    ).all()
    return ApiResponse(data=[ChatHistoryItem.model_validate(r) for r in reversed(rows)])


class ProfileOut(BaseModel):
    city: str = ""
    batch: str = ""
    category: str = ""
    keywords: list[str] = []


class ProfileUpdate(BaseModel):
    city: str | None = Field(default=None, max_length=50)
    batch: str | None = Field(default=None, max_length=20)
    category: str | None = Field(default=None, max_length=50)
    keywords: list[str] | None = Field(default=None, max_length=5)


def _to_out(profile: dict) -> ProfileOut:
    return ProfileOut(
        city=profile["city"],
        batch=profile["batch"],
        category=profile["category"],
        keywords=profile["keywords"].split(),
    )


@router.get("/profile", response_model=ApiResponse[ProfileOut])
async def read_profile(
    subject: AuthSubject = Depends(current_subject),
) -> ApiResponse[ProfileOut]:
    return ApiResponse(data=_to_out(await get_profile(subject.user_id)))


@router.put("/profile", response_model=ApiResponse[ProfileOut])
async def write_profile(
    body: ProfileUpdate, subject: AuthSubject = Depends(current_subject)
) -> ApiResponse[ProfileOut]:
    prefs = {
        k: v
        for k, v in body.model_dump().items()
        if v not in (None, [], "")
    }
    if isinstance(prefs.get("keywords"), list):
        prefs["keywords"] = " ".join(prefs["keywords"])
    profile = await update_profile(subject.user_id, prefs) if prefs else await get_profile(subject.user_id)
    return ApiResponse(data=_to_out(profile))

"""对话管理 Agent：意图识别 + 会话状态维护（Redis）+ 路由到具体 Agent。"""

from __future__ import annotations

import structlog

from ...infra.db import get_sessionmaker
from .base import AgentMessage, AgentReply, BaseAgent, get_agent, register_agent
from .intent import detect_intent
from .models import ChatMessage
from .profile_agent import record_behavior
from .session import get_session_store

log = structlog.get_logger()

HELP_TEXT = (
    "我是 JobClaw 求职派智能助手，可以帮你：\n"
    "1. 采集校招信息 —— 直接粘贴招聘文本，或发送链接\n"
    "2. 推荐职位 —— 说「帮我推荐几个职位」\n"
    "3. 设置求职偏好 —— 说「我想找北京的后端工作」\n"
    "4. 查看我的画像 —— 说「我的偏好」\n"
    "管理员额外支持：职位统计/去重/过期清理、定时任务列表。"
)

INTENT_AGENT = {
    "collect": "collect",
    "recommend": "recommend",
    "profile": "profile",
    "jobinfo": "jobinfo",
    "schedule": "scheduler",
    "help": "dialogue",
    "chat": "dialogue",
}


class DialogueAgent(BaseAgent):
    name = "dialogue"
    description = "对话管理：意图识别、会话状态、路由分发"

    async def handle(self, msg: AgentMessage) -> AgentReply:
        store = await get_session_store()
        state = (await store.get(msg.session_id)) or {}
        msg.context = state

        intent, confidence = await detect_intent(msg.text)
        agent_name = INTENT_AGENT.get(intent, "dialogue")
        agent = get_agent(agent_name)

        if agent is None or agent is self:
            reply = AgentReply(text=HELP_TEXT, agent=self.name, intent=intent)
        elif agent.admin_only and msg.role != "ADMIN":
            reply = AgentReply(
                text="该功能需要管理员权限。", agent=self.name, intent=intent
            )
        else:
            try:
                reply = await agent.handle(msg)
                reply.agent = reply.agent or agent_name
                reply.intent = reply.intent or intent
            except Exception as exc:
                log.exception("agent_handle_failed", agent=agent_name, intent=intent)
                reply = AgentReply(
                    text=f"处理出错了：{exc}", agent=agent_name, intent=intent
                )

        await self._persist(msg, reply, intent)
        await record_behavior(msg.user_id, "chat", detail=msg.text[:200])

        history = list(state.get("history", []))
        history += [["user", msg.text[:200]], ["assistant", reply.text[:200]]]
        await store.set(
            msg.session_id,
            {
                "last_intent": intent,
                "last_agent": reply.agent or agent_name,
                "confidence": confidence,
                "history": history[-10:],
            },
        )
        return reply

    async def _persist(self, msg: AgentMessage, reply: AgentReply, intent: str) -> None:
        """会话消息落库（user + assistant 两条）。"""
        try:
            async with get_sessionmaker()() as session:
                session.add(
                    ChatMessage(
                        session_id=msg.session_id,
                        user_id=msg.user_id,
                        role="user",
                        content=msg.text,
                        agent=reply.agent,
                        intent=intent,
                    )
                )
                session.add(
                    ChatMessage(
                        session_id=msg.session_id,
                        user_id=msg.user_id,
                        role="assistant",
                        content=reply.text,
                        agent=reply.agent,
                        intent=intent,
                    )
                )
                await session.commit()
        except Exception as exc:  # noqa: BLE001
            log.warning("chat_message_persist_failed", error=str(exc))


dialogue_agent = register_agent(DialogueAgent())

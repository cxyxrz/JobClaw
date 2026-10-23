"""Agent 公共基类：统一消息/回复模型与注册表。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass(slots=True)
class AgentMessage:
    """对话管理 Agent 分发给各 Agent 的统一消息。"""

    user_id: int
    username: str
    role: str
    text: str
    session_id: str
    channel: str = "web"  # web | wechat | feishu | dingtalk
    context: dict = field(default_factory=dict)  # 会话状态（来自会话存储）


@dataclass(slots=True)
class AgentReply:
    """Agent 统一回复。data 携带结构化数据（职位卡片等）。"""

    text: str
    agent: str = ""
    intent: str = ""
    data: dict = field(default_factory=dict)


class BaseAgent(ABC):
    """业务/支撑 Agent 基类：实现 handle 即可被对话管理 Agent 路由调用。"""

    name: str = "base"
    description: str = ""
    admin_only: bool = False  # 是否仅管理员可用

    @abstractmethod
    async def handle(self, msg: AgentMessage) -> AgentReply:
        raise NotImplementedError


_REGISTRY: dict[str, BaseAgent] = {}


def register_agent(agent: BaseAgent | type[BaseAgent]) -> BaseAgent:
    """注册 Agent；装饰在类上时自动实例化。"""
    if isinstance(agent, type):
        agent = agent()
    _REGISTRY[agent.name] = agent
    return agent


def get_agent(name: str) -> BaseAgent | None:
    return _REGISTRY.get(name)


def all_agents() -> list[BaseAgent]:
    return list(_REGISTRY.values())

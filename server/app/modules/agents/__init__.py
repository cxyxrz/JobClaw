"""Agent 模块：按架构图分层组织。

- gateway.py     消息网关适配器（IM 渠道 → 统一消息 → 用户映射）+ 消息推送
- dialogue.py    对话管理 Agent（意图识别 / 会话状态 / 路由）
- intent.py      轻量意图识别（规则 + 可选 LLM）
- session.py     会话状态存储（Redis / 内存）
- profile_agent / recommend_agent / collect_agent / jobinfo_agent  业务 Agent
- tools_agent / scheduler_agent  支撑 Agent
- model_router.py 模型路由（多模型切换 + Token 统计）
- base.py        公共基类与注册表
"""

from . import (  # noqa: F401  # 导入即注册各 Agent
    base,
    collect_agent,
    dialogue,
    gateway,
    intent,
    jobinfo_agent,
    model_router,
    profile_agent,
    recommend_agent,
    scheduler_agent,
    session,
    tools_agent,
)
from .base import AgentMessage, AgentReply, BaseAgent, all_agents, get_agent, register_agent  # noqa: F401

"""IM 渠道回调：微信 / 飞书 / 钉钉 webhook 入站（无 JWT，靠渠道签名校验）。"""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ...modules.agents.base import AgentMessage
from ...modules.agents.dialogue import dialogue_agent
from ...modules.agents.gateway import adapters, get_or_bind_user, push_service

router = APIRouter(prefix="/im", tags=["agents"])


@router.get("/webhook/wechat")
async def wechat_echo(request: Request):
    """微信服务器 URL 校验（GET echostr）。"""
    adapter = adapters["wechat"]
    return await adapter.handle_echo(request)


@router.post("/webhook/{channel}")
async def im_webhook(channel: str, request: Request):
    """IM 入站消息：验签 → 归一化 → 用户映射 → 对话管理 Agent → 渠道应答/推送。"""
    adapter = adapters.get(channel)
    if adapter is None:
        return JSONResponse(
            {"code": 40400, "message": f"unknown channel: {channel}"}, status_code=404
        )

    msg, early = await adapter.handle_message(request)
    if early is not None:
        return early
    if msg is None or not msg.text:
        return adapter.ack()

    user = await get_or_bind_user(msg.channel, msg.im_user_id)
    reply = await dialogue_agent.handle(
        AgentMessage(
            user_id=user.id,
            username=user.username,
            role=user.role,
            text=msg.text,
            session_id=f"{msg.channel}:{user.id}",
            channel=msg.channel,
        )
    )

    response = adapter.build_reply(reply.text, msg)
    if response is not None:
        return response  # 支持被动回复的渠道（微信 XML / 钉钉 JSON）
    await push_service.send(msg.channel, reply.text)  # 飞书：机器人主动推送
    return adapter.ack()

"""IM 消息网关（架构第 1-2 层 + 推送）：统一消息格式 / 签名校验 / 用户ID映射 / 消息推送。

入站：微信(公众号/企微回调) · 飞书(事件订阅) · 钉钉(机器人回调)
出站：飞书/企微/钉钉 群机器人 webhook 主动推送
签名密钥未配置时跳过验签（开发模式），配置后强制校验。
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import re
import secrets
import time
from dataclasses import dataclass, field
from urllib.parse import quote
from xml.etree import ElementTree

import httpx
import structlog
from fastapi import Request
from fastapi.responses import JSONResponse, PlainTextResponse, Response
from sqlalchemy import select

from ...core.config import get_settings
from ...core.security import hash_password
from ...infra.db import get_sessionmaker
from ..auth.models import User
from .models import ImBinding

log = structlog.get_logger()


# ---------- 统一消息格式 ----------

@dataclass(slots=True)
class UnifiedMessage:
    """各渠道消息归一化后的统一格式。"""

    channel: str  # wechat | feishu | dingtalk
    im_user_id: str
    chat_id: str
    msg_type: str = "text"
    text: str = ""
    raw: dict | str = field(default_factory=dict)


# ---------- 用户 ID 映射 ----------

async def get_or_bind_user(channel: str, im_user_id: str) -> User:
    """IM 用户 → 系统用户：首次消息自动注册并写绑定表。"""
    async with get_sessionmaker()() as session:
        binding = (
            await session.scalars(
                select(ImBinding).where(
                    ImBinding.channel == channel, ImBinding.im_user_id == im_user_id
                )
            )
        ).first()
        if binding is not None:
            user = await session.get(User, binding.user_id)
            if user is not None:
                return user

        username = (
            f"{channel}_{im_user_id}"
            if len(im_user_id) <= 56
            else f"{channel}_{hashlib.sha1(im_user_id.encode()).hexdigest()[:12]}"
        )
        user = User(
            username=username,
            password_hash=hash_password(secrets.token_hex(16)),
            role="USER",
            union_id=f"{channel}:{im_user_id}"[:64],
        )
        session.add(user)
        await session.flush()
        session.add(ImBinding(channel=channel, im_user_id=im_user_id, user_id=user.id))
        await session.commit()
        await session.refresh(user)
        log.info("im_user_bound", channel=channel, user_id=user.id)
        return user


# ---------- 消息推送（基础设施层）----------

class PushService:
    """IM 机器人 webhook 主动推送。未配置对应渠道时返回 skipped。"""

    async def _post(self, url: str, payload: dict) -> dict:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            try:
                return resp.json()
            except ValueError:
                return {"status": "ok"}

    @staticmethod
    def _signed_url(url: str, secret: str) -> str:
        ts = str(int(time.time() * 1000))
        sign = base64.urlsafe_b64encode(
            hmac.new(secret.encode(), f"{ts}\n{secret}".encode(), hashlib.sha256).digest()
        ).decode()
        sep = "&" if "?" in url else "?"
        return f"{url}{sep}timestamp={ts}&sign={quote(sign)}"

    async def send(self, channel: str, text: str) -> dict:
        s = get_settings()
        try:
            if channel == "feishu" and s.feishu_webhook_url:
                url = (
                    self._signed_url(s.feishu_webhook_url, s.feishu_webhook_secret)
                    if s.feishu_webhook_secret
                    else s.feishu_webhook_url
                )
                return await self._post(url, {"msg_type": "text", "content": {"text": text}})
            if channel == "wechat" and s.wecom_webhook_key:
                return await self._post(
                    f"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={s.wecom_webhook_key}",
                    {"msgtype": "text", "text": {"content": text}},
                )
            if channel == "dingtalk" and s.dingtalk_webhook_url:
                url = (
                    self._signed_url(s.dingtalk_webhook_url, s.dingtalk_webhook_secret)
                    if s.dingtalk_webhook_secret
                    else s.dingtalk_webhook_url
                )
                return await self._post(url, {"msgtype": "text", "text": {"content": text}})
        except Exception as exc:  # noqa: BLE001
            log.warning("push_failed", channel=channel, error=str(exc))
            return {"status": "error", "error": str(exc)}
        return {"status": "skipped", "message": f"channel {channel} webhook not configured"}

    async def send_admin(self, text: str) -> dict:
        """管理员通知：优先飞书 → 钉钉 → 企微，均未配置则跳过。"""
        s = get_settings()
        for channel, configured in (
            ("feishu", bool(s.feishu_webhook_url)),
            ("dingtalk", bool(s.dingtalk_webhook_url)),
            ("wechat", bool(s.wecom_webhook_key)),
        ):
            if configured:
                return await self.send(channel, text)
        return {"status": "skipped"}

    async def push_to_user(self, user_id: int, text: str) -> str:
        """按用户 IM 绑定渠道推送；未绑定返回 none。"""
        async with get_sessionmaker()() as session:
            binding = (
                await session.scalars(select(ImBinding).where(ImBinding.user_id == user_id))
            ).first()
        if binding is None:
            return "none"
        await self.send(binding.channel, text)
        return binding.channel


push_service = PushService()


# ---------- 渠道适配器 ----------

def _parse_wechat_xml(body: bytes) -> dict:
    try:
        root = ElementTree.fromstring(body)
    except ElementTree.ParseError:
        return {}
    return {child.tag: (child.text or "") for child in root}


class WechatAdapter:
    """微信/企业微信回调：GET 验证 echostr，POST XML 消息，被动回复 XML。"""

    channel = "wechat"

    @staticmethod
    def _check_signature(token: str, timestamp: str, nonce: str, signature: str) -> bool:
        digest = hashlib.sha1("".join(sorted([token, timestamp, nonce])).encode()).hexdigest()
        return digest == signature

    async def handle_echo(self, request: Request) -> Response:
        q = request.query_params
        token = get_settings().im_wechat_token
        if token and not self._check_signature(
            token, q.get("timestamp", ""), q.get("nonce", ""), q.get("signature", "")
        ):
            return PlainTextResponse("invalid signature", status_code=403)
        return PlainTextResponse(q.get("echostr", ""))

    async def handle_message(self, request: Request):
        """返回 (UnifiedMessage|None, 提前应答Response|None)。"""
        token = get_settings().im_wechat_token
        if token:
            q = request.query_params
            if not self._check_signature(
                token, q.get("timestamp", ""), q.get("nonce", ""), q.get("signature", "")
            ):
                return None, PlainTextResponse("invalid signature", status_code=403)
        data = _parse_wechat_xml(await request.body())
        if data.get("MsgType") != "text":
            return None, PlainTextResponse("success")
        msg = UnifiedMessage(
            channel=self.channel,
            im_user_id=data.get("FromUserName", ""),
            chat_id=data.get("ToUserName", ""),
            text=(data.get("Content") or "").strip(),
            raw=data,
        )
        return msg, None

    def build_reply(self, text: str, msg: UnifiedMessage) -> Response | None:
        safe = text.replace("]]>", "]]]]><![CDATA[>")
        xml = (
            f"<xml><ToUserName><![CDATA[{msg.im_user_id}]]></ToUserName>"
            f"<FromUserName><![CDATA[{msg.chat_id}]]></FromUserName>"
            f"<CreateTime>{int(time.time())}</CreateTime>"
            f"<MsgType><![CDATA[text]]></MsgType>"
            f"<Content><![CDATA[{safe}]]></Content></xml>"
        )
        return Response(content=xml, media_type="application/xml")

    def ack(self) -> Response:
        return PlainTextResponse("success")


class FeishuAdapter:
    """飞书事件订阅：url_verification 应答 challenge，消息经机器人 webhook 主动回复。"""

    channel = "feishu"

    async def handle_message(self, request: Request):
        s = get_settings()
        body = await request.body()
        if s.im_feishu_encrypt_key:
            ts = request.headers.get("x-lark-request-timestamp", "")
            nonce = request.headers.get("x-lark-request-nonce", "")
            expected = hashlib.sha256(
                f"{ts}{nonce}{s.im_feishu_encrypt_key}".encode() + body
            ).hexdigest()
            if expected != request.headers.get("x-lark-signature", ""):
                return None, JSONResponse(
                    {"code": 40300, "msg": "invalid signature"}, status_code=403
                )
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            return None, JSONResponse({"code": 40000, "msg": "bad json"}, status_code=400)

        if data.get("type") == "url_verification":
            return None, JSONResponse({"challenge": data.get("challenge", "")})

        event = data.get("event") or {}
        message = event.get("message") or {}
        if message.get("message_type") != "text":
            return None, self.ack()
        try:
            content = json.loads(message.get("content") or "{}")
        except json.JSONDecodeError:
            content = {}
        text = re.sub(r"<at[^>]*>[^<]*</at>\s*", "", content.get("text", "")).strip()
        if not text:
            return None, self.ack()
        sender = (event.get("sender") or {}).get("sender_id") or {}
        msg = UnifiedMessage(
            channel=self.channel,
            im_user_id=sender.get("open_id", ""),
            chat_id=message.get("chat_id", ""),
            text=text,
            raw=data,
        )
        return msg, None

    def build_reply(self, text: str, msg: UnifiedMessage) -> Response | None:
        return None  # 飞书事件回调不能直接被动回复 → 走机器人 webhook 推送

    def ack(self) -> Response:
        return JSONResponse({"code": 0})


class DingtalkAdapter:
    """钉钉机器人回调：JSON 消息，HTTP JSON 被动回复。"""

    channel = "dingtalk"

    async def handle_message(self, request: Request):
        s = get_settings()
        if s.im_dingtalk_secret:
            ts = request.headers.get("timestamp", "")
            expected = base64.b64encode(
                hmac.new(
                    s.im_dingtalk_secret.encode(),
                    f"{ts}\n{s.im_dingtalk_secret}".encode(),
                    hashlib.sha256,
                ).digest()
            ).decode()
            if expected != request.headers.get("sign", ""):
                return None, JSONResponse(
                    {"code": 40300, "msg": "invalid signature"}, status_code=403
                )
        try:
            data = json.loads(await request.body())
        except json.JSONDecodeError:
            return None, JSONResponse({"code": 40000, "msg": "bad json"}, status_code=400)

        text = ((data.get("text") or {}).get("content") or "").strip()
        if not text:
            return None, self.ack()
        msg = UnifiedMessage(
            channel=self.channel,
            im_user_id=data.get("senderStaffId") or data.get("senderId") or "",
            chat_id=data.get("conversationId") or "",
            text=text,
            raw=data,
        )
        return msg, None

    def build_reply(self, text: str, msg: UnifiedMessage) -> Response | None:
        return JSONResponse({"msgtype": "text", "text": {"content": text}})

    def ack(self) -> Response:
        return JSONResponse({"code": 0, "success": True})


adapters: dict[str, object] = {
    "wechat": WechatAdapter(),
    "feishu": FeishuAdapter(),
    "dingtalk": DingtalkAdapter(),
}

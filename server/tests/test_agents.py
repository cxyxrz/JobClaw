"""Agent 系统测试：对话管理 / 画像 / 推荐 / 采集 / 信息管理 / 调度 / IM 网关 / 工具。"""

import json
from datetime import datetime, timezone

import pytest
from sqlalchemy import select

from app.infra.db import get_sessionmaker
from app.modules.agents.models import ImBinding, UserBehavior
from app.modules.auth.models import User
from app.modules.jobs.models import Job


@pytest.fixture(autouse=True)
async def _fresh_session_store():
    """每个测试重置会话存储单例：Redis 客户端绑定事件循环，不能跨测试复用。"""
    from app.modules.agents import session as sess

    await sess.reset_session_store()
    yield
    await sess.reset_session_store()


async def _login(client, make_user, username, role="USER"):
    await make_user(username, "pw123", role=role)
    r = await client.post(
        "/api/v1/auth/login", json={"username": username, "password": "pw123"}
    )
    return r.json()["data"]["access_token"]


async def _auth(token):
    return {"Authorization": f"Bearer {token}"}


async def _seed_jobs():
    now = datetime.now(timezone.utc)
    async with get_sessionmaker()() as session:
        session.add(
            Job(title="后端开发工程师", company="字节跳动", city="北京", batch="2026届",
                category="技术", salary_text="25-40K", description="Python 后端研发",
                published_at=now)
        )
        session.add(
            Job(title="算法工程师", company="腾讯", city="深圳", batch="2026届",
                category="技术", salary_text="30-50K", description="推荐算法",
                published_at=now)
        )
        session.add(
            Job(title="产品经理", company="美团", city="上海", batch="2027届",
                category="产品", salary_text="18-28K", description="社区产品规划",
                published_at=now)
        )
        await session.commit()


async def _chat(client, token, message):
    r = await client.post("/api/v1/chat", json={"message": message}, headers=await _auth(token))
    assert r.status_code == 200, r.text
    return r.json()["data"]


# ---------- 对话管理 + 业务 Agent ----------

async def test_chat_recommend(client, make_user):
    await _seed_jobs()
    token = await _login(client, make_user, "u1")
    data = await _chat(client, token, "帮我推荐几个职位")
    assert data["agent"] == "recommend"
    assert "推荐" in data["reply"]
    assert data["data"]["jobs"]


async def test_chat_profile_and_recommend(client, make_user):
    await _seed_jobs()
    token = await _login(client, make_user, "u2")
    data = await _chat(client, token, "我想找北京的后端工作")
    assert data["agent"] == "profile"
    assert "北京" in data["reply"]

    viewed = await _chat(client, token, "我的偏好")
    assert "北京" in viewed["reply"]

    # 画像影响推荐排序
    data = await _chat(client, token, "帮我推荐职位")
    top = data["data"]["jobs"][0]
    assert top["city"] == "北京"


async def test_chat_collect_text(client, make_user):
    token = await _login(client, make_user, "u3")
    text = "采集一下\n招聘后端开发工程师\n公司：字节跳动\n工作地：北京\n薪资：20-30K"
    data = await _chat(client, token, text)
    assert data["agent"] == "collect"
    assert "草稿" in data["reply"] or "审核" in data["reply"]
    assert data["data"]["title"]


async def test_chat_help(client, make_user):
    token = await _login(client, make_user, "u4")
    data = await _chat(client, token, "帮助")
    assert data["agent"] == "dialogue"
    assert "智能助手" in data["reply"]


async def test_chat_history_and_behavior(client, make_user):
    token = await _login(client, make_user, "u5")
    await _chat(client, token, "帮我推荐几个职位")
    r = await client.get("/api/v1/chat/history", headers=await _auth(token))
    assert r.status_code == 200
    items = r.json()["data"]
    assert {i["role"] for i in items} == {"user", "assistant"}
    assert items[-1]["agent"] == "recommend"

    uid = None
    async with get_sessionmaker()() as session:
        uid = (
            await session.scalars(select(User.id).where(User.username == "u5"))
        ).one()
        behaviors = (
            await session.scalars(
                select(UserBehavior).where(UserBehavior.user_id == uid)
            )
        ).all()
    assert any(b.action == "chat" for b in behaviors)


async def test_profile_api(client, make_user):
    token = await _login(client, make_user, "u6")
    r = await client.put(
        "/api/v1/chat/profile",
        json={"city": "杭州", "keywords": ["前端", "React"]},
        headers=await _auth(token),
    )
    assert r.status_code == 200
    assert r.json()["data"]["city"] == "杭州"

    r = await client.get("/api/v1/chat/profile", headers=await _auth(token))
    assert r.json()["data"]["keywords"] == ["前端", "React"]


async def test_schedule_admin_only(client, make_user):
    user_tok = await _login(client, make_user, "u7")
    data = await _chat(client, user_tok, "定时任务列表")
    assert "管理员" in data["reply"]

    admin_tok = await _login(client, make_user, "root", role="ADMIN")
    data = await _chat(client, admin_tok, "定时任务列表")
    assert data["agent"] == "scheduler"


# ---------- 校招信息管理 ----------

async def test_jobinfo_agent_chat(client, make_user):
    await _seed_jobs()
    old = datetime(2020, 1, 1, tzinfo=timezone.utc)
    async with get_sessionmaker()() as session:
        session.add(
            Job(title="老职位", company="旧公司", city="北京", batch="2026届",
                description="很老的职位", published_at=old)
        )
        session.add(
            Job(title="后端开发工程师", company="字节跳动", city="北京", batch="2026届",
                description="重复职位", published_at=old)
        )
        await session.commit()

    admin_tok = await _login(client, make_user, "root", role="ADMIN")
    data = await _chat(client, admin_tok, "职位统计")
    assert data["agent"] == "jobinfo"
    assert "职位库共" in data["reply"]

    data = await _chat(client, admin_tok, "去重职位")
    assert "去重完成" in data["reply"] and data["data"]["offlined"] >= 1

    data = await _chat(client, admin_tok, "清理30天过期职位")
    assert "过期清理完成" in data["reply"] and data["data"]["offlined"] >= 1

    data = await _chat(client, admin_tok, "去重职位")  # 幂等：再次执行
    assert data["data"]["offlined"] == 0


# ---------- 管理端 API ----------

async def test_agents_admin_api(client, make_user):
    admin_tok = await _login(client, make_user, "root", role="ADMIN")
    headers = await _auth(admin_tok)

    r = await client.get("/api/v1/agents", headers=headers)
    assert r.status_code == 200
    names = {a["name"] for a in r.json()["data"]}
    assert {"dialogue", "collect", "recommend", "profile", "jobinfo", "tools", "scheduler"} <= names

    r = await client.get("/api/v1/agents/model-usage", headers=headers)
    assert r.status_code == 200 and r.json()["data"] == []

    r = await client.get("/api/v1/agents/jobinfo/stats", headers=headers)
    assert r.status_code == 200 and "total" in r.json()["data"]


async def test_scheduler_task_api(client, make_user):
    admin_tok = await _login(client, make_user, "root", role="ADMIN")
    headers = await _auth(admin_tok)

    r = await client.post(
        "/api/v1/agents/tasks",
        json={"name": "每日过期清理", "task_type": "expire_cleanup", "cron": "0 3 * * *",
              "params": {"days": 30}},
        headers=headers,
    )
    assert r.status_code == 201, r.text
    task = r.json()["data"]
    assert task["enabled"] == 1

    r = await client.get("/api/v1/agents/tasks", headers=headers)
    assert len(r.json()["data"]) == 1

    r = await client.post(f"/api/v1/agents/tasks/{task['id']}/run", headers=headers)
    assert r.status_code == 200
    assert r.json()["data"]["status"] == "SUCCESS"

    r = await client.post(
        f"/api/v1/agents/tasks/{task['id']}/toggle", json={"enabled": False}, headers=headers
    )
    assert r.json()["data"]["enabled"] == 0

    r = await client.delete(f"/api/v1/agents/tasks/{task['id']}", headers=headers)
    assert r.status_code == 200
    r = await client.get("/api/v1/agents/tasks", headers=headers)
    assert r.json()["data"] == []

    # 非法 cron / 类型被拒绝
    r = await client.post(
        "/api/v1/agents/tasks",
        json={"name": "bad", "task_type": "expire_cleanup", "cron": "not-a-cron"},
        headers=headers,
    )
    assert r.status_code == 400
    r = await client.post(
        "/api/v1/agents/tasks",
        json={"name": "bad", "task_type": "unknown", "cron": "0 3 * * *"},
        headers=headers,
    )
    assert r.status_code == 400


# ---------- IM 网关 ----------

async def test_im_dingtalk_webhook(client):
    await _seed_jobs()
    payload = {"text": {"content": "帮我推荐几个职位"}, "senderStaffId": "staff-1",
               "conversationId": "cid-1", "msgtype": "text"}
    r = await client.post("/api/v1/im/webhook/dingtalk", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert body["msgtype"] == "text" and "推荐" in body["text"]["content"]

    # 自动注册 + 绑定；同一 IM 用户重复消息不重复建号
    await client.post("/api/v1/im/webhook/dingtalk", json=payload)
    async with get_sessionmaker()() as session:
        bindings = (await session.scalars(
            __import__("sqlalchemy").select(ImBinding).where(ImBinding.channel == "dingtalk")
        )).all()
    assert len(bindings) == 1 and bindings[0].im_user_id == "staff-1"


async def test_im_wechat_echo_and_message(client):
    r = await client.get(
        "/api/v1/im/webhook/wechat",
        params={"signature": "x", "timestamp": "1", "nonce": "1", "echostr": "hello-echo"},
    )
    assert r.status_code == 200 and r.text == "hello-echo"

    xml = (
        "<xml><ToUserName><![CDATA[gh_bot]]></ToUserName>"
        "<FromUserName><![CDATA[wx-user-1]]></FromUserName>"
        "<MsgType><![CDATA[text]]></MsgType>"
        "<Content><![CDATA[我想找北京的后端工作]]></Content></xml>"
    )
    r = await client.post("/api/v1/im/webhook/wechat", content=xml)
    assert r.status_code == 200
    assert "<xml>" in r.text and "北京" in r.text


async def test_im_feishu_webhook(client):
    r = await client.post(
        "/api/v1/im/webhook/feishu",
        json={"type": "url_verification", "challenge": "ck-123"},
    )
    assert r.status_code == 200 and r.json()["challenge"] == "ck-123"

    event = {
        "event": {
            "sender": {"sender_id": {"open_id": "ou-1"}},
            "message": {
                "chat_id": "oc-1",
                "message_type": "text",
                "content": json.dumps({"text": "<at user_id=\"x\">bot</at> 我的偏好"}),
            },
        }
    }
    r = await client.post("/api/v1/im/webhook/feishu", json=event)
    assert r.status_code == 200 and r.json()["code"] == 0

    r = await client.post("/api/v1/im/webhook/unknown", json={})
    assert r.status_code == 404


# ---------- 工具调用 Agent ----------

async def test_tools_agent_unit(tmp_path):
    from app.core.config import get_settings
    from app.modules.agents.tools_agent import tools_agent

    get_settings().tool_sandbox_dir = str(tmp_path / "sandbox")

    names = {t["name"] for t in tools_agent.registry.list()}
    assert {"web_fetch", "file_save", "file_read", "search_web", "mcp_call"} <= names

    saved = await tools_agent.execute("file_save", {"filename": "a.txt", "content": "hello"})
    assert saved["size"] == 5
    loaded = await tools_agent.execute("file_read", {"filename": "a.txt"})
    assert loaded["content"] == "hello"

    searched = await tools_agent.execute("search_web", {"query": "校招"})
    assert searched["status"] == "not_configured"

    # 路径穿越被拦截
    from app.core.errors import AppError

    try:
        await tools_agent.execute("file_read", {"filename": "../etc/passwd"})
        raised = False
    except AppError:
        raised = True
    assert raised

"""Agent 系统端到端验证脚本（对运行中的服务 http://127.0.0.1:8000）。

覆盖架构图各层：
1. 对话管理：意图识别 → 路由（画像/推荐/采集/信息管理/调度/帮助）
2. 用户画像：偏好设置 → 画像影响推荐排序 → 历史记录
3. 校招采集：对话内文本采集 → 草稿入库
4. 校招信息管理：统计 / 去重 / 过期清理
5. 任务调度：创建 → 手动触发（心跳+状态回写）→ 停用 → 删除
6. 模型路由：Agent 列表 / 用量统计接口
7. IM 网关：钉钉（被动回复+自动绑定）/ 飞书（challenge）/ 微信（echo + XML）
8. 权限：普通用户访问管理接口被拒
"""

import asyncio

import httpx

BASE = "http://127.0.0.1:8000"


async def login(c: httpx.AsyncClient, username: str, password: str) -> dict:
    r = await c.post("/api/v1/auth/login", json={"username": username, "password": password})
    token = r.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def chat(c: httpx.AsyncClient, h: dict, message: str) -> dict:
    r = await c.post("/api/v1/chat", json={"message": message}, headers=h)
    assert r.status_code == 200, r.text
    return r.json()["data"]


async def main() -> None:
    async with httpx.AsyncClient(base_url=BASE, timeout=30) as c:
        admin_h = await login(c, "admin", "admin123")
        user_h = await login(c, "demo", "demo123")
        print("[登录] admin / demo token 获取成功")

        # ---- 1. 对话管理：设置偏好（画像 Agent）----
        d = await chat(c, user_h, "我想找北京的后端工作")
        assert d["agent"] == "profile" and "北京" in d["reply"], d
        print(f"\n[1 画像Agent] intent={d['intent']} -> {d['reply'].splitlines()[0]}")

        # ---- 2. 推荐 Agent：画像影响排序 ----
        d = await chat(c, user_h, "帮我推荐几个职位")
        assert d["agent"] == "recommend" and d["data"]["jobs"], d
        top = d["data"]["jobs"][0]
        print(f"[2 推荐Agent] 命中 {len(d['data']['jobs'])} 个，Top1: {top['title']}@{top['city']} score={top['score']}")

        # ---- 3. 画像查看 + 历史 ----
        d = await chat(c, user_h, "我的偏好")
        assert "北京" in d["reply"], d
        r = await c.get("/api/v1/chat/history?limit=10", headers=user_h)
        roles = {i["role"] for i in r.json()["data"]}
        assert roles == {"user", "assistant"}
        print(f"[3 画像/历史] 查看画像 ok，历史 {len(r.json()['data'])} 条（user+assistant）")

        # ---- 4. 采集 Agent：对话内文本采集 ----
        text = "采集一下\n搜索算法专家\n公司：华为\n工作地：深圳\n招聘对象：2026届\n薪资：35-60K"
        d = await chat(c, admin_h, text)
        assert d["agent"] == "collect" and d["data"]["title"], d
        print(f"[4 采集Agent] status={d['data']['status']} title={d['data']['title']} conf={d['data']['confidence']}")

        # ---- 5. 信息管理 Agent：统计/去重/过期 ----
        d = await chat(c, admin_h, "职位统计")
        assert d["agent"] == "jobinfo" and "职位库共" in d["reply"], d
        print(f"[5 信息管理] {d['reply'].splitlines()[0]}")
        d = await chat(c, admin_h, "去重职位")
        assert "去重完成" in d["reply"], d
        d = await chat(c, admin_h, "清理365天过期职位")
        assert "过期清理完成" in d["reply"], d
        print(f"[5 信息管理] 去重/过期清理 ok（{d['data']['offlined']} 个下线）")

        # ---- 6. 任务调度 Agent：创建 → 触发 → 停用 → 删除 ----
        r = await c.post(
            "/api/v1/agents/tasks",
            json={"name": "验证-每日过期清理", "task_type": "expire_cleanup",
                  "cron": "0 3 * * *", "params": {"days": 90}},
            headers=admin_h,
        )
        assert r.status_code == 201, r.text
        task_id = r.json()["data"]["id"]
        r = await c.post(f"/api/v1/agents/tasks/{task_id}/run", headers=admin_h)
        run = r.json()["data"]
        assert run["status"] == "SUCCESS", run
        r = await c.get("/api/v1/agents/tasks", headers=admin_h)
        task = next(t for t in r.json()["data"] if t["id"] == task_id)
        assert task["heartbeat_at"] and task["last_status"] == "SUCCESS"
        print(f"[6 任务调度] 任务#{task_id} 触发 {run['status']}，心跳 {task['heartbeat_at']}，msg={run['message']}")
        r = await c.post(f"/api/v1/agents/tasks/{task_id}/toggle", json={"enabled": False}, headers=admin_h)
        assert r.json()["data"]["enabled"] == 0
        r = await c.delete(f"/api/v1/agents/tasks/{task_id}", headers=admin_h)
        assert r.status_code == 200
        print("[6 任务调度] 停用 + 删除 ok")

        # ---- 7. Agent 列表 + 模型用量 ----
        r = await c.get("/api/v1/agents", headers=admin_h)
        names = sorted(a["name"] for a in r.json()["data"])
        assert set(names) >= {"dialogue", "collect", "recommend", "profile", "jobinfo", "tools", "scheduler"}
        r = await c.get("/api/v1/agents/model-usage", headers=admin_h)
        assert r.status_code == 200
        print(f"[7 模型路由] 注册 Agent: {', '.join(names)}；用量统计接口 ok")

        # ---- 8. IM 网关：钉钉（自动注册+被动回复）----
        payload = {"text": {"content": "帮我推荐几个职位"}, "senderStaffId": "verify-staff-9",
                   "conversationId": "verify-cid", "msgtype": "text"}
        r = await c.post("/api/v1/im/webhook/dingtalk", json=payload)
        body = r.json()
        assert r.status_code == 200 and "推荐" in body["text"]["content"], body
        r2 = await c.post("/api/v1/im/webhook/dingtalk", json=payload)  # 幂等绑定
        assert r2.status_code == 200
        print(f"[8 IM网关-钉钉] 自动绑定+回复 ok: {body['text']['content'][:30]}...")

        # ---- 8b. 飞书 challenge ----
        r = await c.post("/api/v1/im/webhook/feishu", json={"type": "url_verification", "challenge": "verify-ck"})
        assert r.json()["challenge"] == "verify-ck"
        event = {"event": {"sender": {"sender_id": {"open_id": "verify-ou-9"}},
                           "message": {"chat_id": "verify-oc", "message_type": "text",
                                       "content": "{\"text\": \"我的偏好\"}"}}}
        r = await c.post("/api/v1/im/webhook/feishu", json=event)
        assert r.status_code == 200 and r.json()["code"] == 0
        print("[8 IM网关-飞书] url_verification + 事件应答 ok")

        # ---- 8c. 微信 echo + XML 消息 ----
        r = await c.get("/api/v1/im/webhook/wechat",
                        params={"signature": "s", "timestamp": "1", "nonce": "1", "echostr": "verify-echo"})
        assert r.text == "verify-echo"
        xml = ("<xml><ToUserName><![CDATA[gh_verify]]></ToUserName>"
               "<FromUserName><![CDATA[verify-wx-9]]></FromUserName>"
               "<MsgType><![CDATA[text]]></MsgType>"
               "<Content><![CDATA[我想找上海的产品工作]]></Content></xml>")
        r = await c.post("/api/v1/im/webhook/wechat", content=xml)
        assert r.status_code == 200 and "上海" in r.text and "<xml>" in r.text
        print("[8 IM网关-微信] echo 校验 + XML 被动回复 ok")

        # ---- 9. 权限校验：普通用户被拒 ----
        r = await c.get("/api/v1/agents", headers=user_h)
        assert r.status_code == 403 and r.json()["code"] == 40300
        print("[9 权限] demo 访问管理接口 403 ok")

        print("\n=== Agent 系统端到端验证全部通过 ===")


if __name__ == "__main__":
    asyncio.run(main())

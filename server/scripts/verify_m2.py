"""M2 校招采集 Agent 端到端验证脚本。

覆盖场景：
1. 文本采集（高置信度 -> DRAFT 入库）
2. 重复检测（同公司+同标题 -> DUPLICATE 跳过）
3. 低置信度（缺核心字段 -> REVIEW 待审核）
4. 草稿审核通过（ACCEPTED -> 自动创建正式职位）
"""

import asyncio

import httpx

BASE = "http://127.0.0.1:8000"


async def main() -> None:
    async with httpx.AsyncClient(base_url=BASE, timeout=20) as c:
        # 登录
        r = await c.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "admin123"},
        )
        token = r.json()["data"]["access_token"]
        h = {"Authorization": f"Bearer {token}"}
        print(f"[登录] token 获取成功")

        # ---- 场景 1：文本采集 ----
        text = (
            "前端开发工程师\n"
            "阿里巴巴\n"
            "工作地点：杭州\n"
            "招聘对象：2026届\n"
            "薪资：22-38K·16薪\n"
            "负责电商核心链路前端研发。"
        )
        r = await c.post("/api/v1/collect", json={"source_type": "text", "content": text}, headers=h)
        d = r.json()["data"]
        print(f"\n[场景1 文本采集] status={d['status']} confidence={d['confidence']} "
              f"title={d['title']} company={d['company']} draft_id={d['draft_id']}")
        assert d["status"] == "DRAFT", f"期望 DRAFT，实际 {d['status']}"
        assert d["confidence"] >= 0.6
        draft_id = d["draft_id"]

        # ---- 场景 2：重复检测 ----
        r = await c.post("/api/v1/collect", json={"source_type": "text", "content": text}, headers=h)
        d = r.json()["data"]
        print(f"[场景2 重复检测] status={d['status']} draft_id={d['draft_id']}")
        assert d["status"] == "DUPLICATE", f"期望 DUPLICATE，实际 {d['status']}"
        assert d["draft_id"] is None

        # ---- 场景 3：低置信度 ----
        r = await c.post(
            "/api/v1/collect",
            json={"source_type": "text", "content": "一段没有明确职位和公司的模糊描述"},
            headers=h,
        )
        d = r.json()["data"]
        print(f"[场景3 低置信度] status={d['status']} confidence={d['confidence']}")
        assert d["status"] == "REVIEW", f"期望 REVIEW，实际 {d['status']}"

        # ---- 场景 4：草稿审核通过 -> 转正式职位 ----
        r = await c.post(f"/api/v1/admin/drafts/{draft_id}/review",
                         json={"action": "accept", "note": "验证通过"}, headers=h)
        d = r.json()["data"]
        print(f"[场景4 审核通过] draft status={d['status']}")
        assert d["status"] == "ACCEPTED"

        # 校验正式职位已创建
        r = await c.get("/api/v1/jobs?keyword=阿里巴巴", headers=h)
        jobs = r.json()["data"]
        print(f"[场景4 校验] 正式职位表中 '阿里巴巴' 数量={jobs['total']}")
        assert jobs["total"] >= 1

        print("\n✅ M2 全部 4 个场景验证通过")


if __name__ == "__main__":
    asyncio.run(main())

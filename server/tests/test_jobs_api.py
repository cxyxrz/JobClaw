from app.infra.db import get_sessionmaker
from app.modules.jobs.models import Job


async def make_job(**overrides) -> int:
    data = dict(
        title="后端开发工程师",
        company="示例科技",
        city="北京",
        batch="2026届",
        category="技术",
        salary_text="20-30K",
        description="负责服务端业务系统开发",
        source_url=None,
    )
    data.update(overrides)
    async with get_sessionmaker()() as session:
        job = Job(**data)
        session.add(job)
        await session.commit()
        await session.refresh(job)
        return job.id


async def admin_token(client, make_user) -> str:
    await make_user("root", "pw123", role="ADMIN")
    r = await client.post(
        "/api/v1/auth/login", json={"username": "root", "password": "pw123"}
    )
    return r.json()["data"]["access_token"]


async def test_list_and_filters(client):
    await make_job()
    await make_job(title="前端开发工程师", city="上海")
    await make_job(title="运营管培生", batch="2027届", status="OFFLINE")

    r = await client.get("/api/v1/jobs")
    body = r.json()["data"]
    assert r.status_code == 200 and body["total"] == 2

    r = await client.get("/api/v1/jobs", params={"city": "北京"})
    assert r.json()["data"]["total"] == 1

    r = await client.get("/api/v1/jobs", params={"batch": "2027届"})
    assert r.json()["data"]["total"] == 0

    r = await client.get("/api/v1/jobs", params={"keyword": "前端"})
    data = r.json()["data"]
    assert data["total"] == 1 and data["items"][0]["title"] == "前端开发工程师"


async def test_pagination(client):
    for i in range(5):
        await make_job(title=f"职位{i}")
    r = await client.get("/api/v1/jobs", params={"page": 1, "page_size": 2})
    data = r.json()["data"]
    assert data["total"] == 5 and len(data["items"]) == 2
    r = await client.get("/api/v1/jobs", params={"page": 3, "page_size": 2})
    assert len(r.json()["data"]["items"]) == 1


async def test_detail_and_404(client):
    job_id = await make_job()
    r = await client.get(f"/api/v1/jobs/{job_id}")
    assert r.status_code == 200 and r.json()["data"]["id"] == job_id

    r = await client.get("/api/v1/jobs/999999")
    assert r.status_code == 404 and r.json()["code"] == 40400

    offline_id = await make_job(status="OFFLINE")
    r = await client.get(f"/api/v1/jobs/{offline_id}")
    assert r.status_code == 404


async def test_admin_create_and_offline(client, make_user):
    token = await admin_token(client, make_user)
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "title": "算法工程师",
        "company": "智能无限",
        "city": "深圳",
        "batch": "2026届",
        "category": "技术",
        "description": "参与推荐系统迭代",
    }
    r = await client.post("/api/v1/admin/jobs", json=payload, headers=headers)
    assert r.status_code == 201
    job_id = r.json()["data"]["id"]

    r = await client.get("/api/v1/jobs", params={"keyword": "算法"})
    assert r.json()["data"]["total"] == 1

    r = await client.patch(
        f"/api/v1/admin/jobs/{job_id}", json={"status": "OFFLINE"}, headers=headers
    )
    assert r.status_code == 200 and r.json()["data"]["status"] == "OFFLINE"

    r = await client.get("/api/v1/jobs", params={"keyword": "算法"})
    assert r.json()["data"]["total"] == 0

    await make_user("alice", "pw123", role="USER")
    r = await client.post(
        "/api/v1/auth/login", json={"username": "alice", "password": "pw123"}
    )
    user_headers = {"Authorization": f"Bearer {r.json()['data']['access_token']}"}
    r = await client.post("/api/v1/admin/jobs", json=payload, headers=user_headers)
    assert r.status_code == 403

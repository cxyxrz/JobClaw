from tests.test_jobs_api import admin_token


async def test_snapshot_and_304(client, make_user):
    token = await admin_token(client, make_user)
    headers = {"Authorization": f"Bearer {token}"}

    r = await client.post(
        "/api/v1/admin/dicts/types",
        json={"type_code": "CITY", "name": "城市"},
        headers=headers,
    )
    assert r.status_code == 201

    for idx, city in enumerate(["北京", "上海"]):
        r = await client.post(
            "/api/v1/admin/dicts/items",
            json={
                "type_code": "CITY",
                "item_key": city,
                "item_value": city,
                "sort_order": idx,
            },
            headers=headers,
        )
        assert r.status_code == 201

    r = await client.get("/api/v1/dicts")
    snap = r.json()["data"]
    assert snap["version"] == 3
    city_type = next(t for t in snap["types"] if t["type_code"] == "CITY")
    assert len(city_type["items"]) == 2

    r = await client.get("/api/v1/dicts", params={"version": snap["version"]})
    assert r.status_code == 304

    r = await client.post(
        "/api/v1/admin/dicts/items",
        json={"type_code": "CITY", "item_key": "深圳", "item_value": "深圳"},
        headers=headers,
    )
    assert r.status_code == 201

    r = await client.get("/api/v1/dicts", params={"version": 3})
    assert r.status_code == 200
    snap2 = r.json()["data"]
    assert snap2["version"] == 4
    city_type = next(t for t in snap2["types"] if t["type_code"] == "CITY")
    assert len(city_type["items"]) == 3


async def test_update_and_delete_bump_version(client, make_user):
    token = await admin_token(client, make_user)
    headers = {"Authorization": f"Bearer {token}"}

    await client.post(
        "/api/v1/admin/dicts/types",
        json={"type_code": "BATCH", "name": "届别"},
        headers=headers,
    )
    r = await client.post(
        "/api/v1/admin/dicts/items",
        json={"type_code": "BATCH", "item_key": "2026届", "item_value": "2026届"},
        headers=headers,
    )
    item_id = r.json()["data"]["id"]

    before = (await client.get("/api/v1/dicts")).json()["data"]["version"]
    r = await client.patch(
        f"/api/v1/admin/dicts/items/{item_id}", json={"enabled": False}, headers=headers
    )
    assert r.status_code == 200 and r.json()["data"]["enabled"] is False
    after = (await client.get("/api/v1/dicts")).json()["data"]["version"]
    assert after == before + 1

    r = await client.delete(f"/api/v1/admin/dicts/items/{item_id}", headers=headers)
    assert r.status_code == 200
    after2 = (await client.get("/api/v1/dicts")).json()["data"]["version"]
    assert after2 == after + 1


async def test_dict_perms(client, make_user):
    r = await client.post(
        "/api/v1/admin/dicts/types", json={"type_code": "X", "name": "x"}
    )
    assert r.status_code == 401

    await make_user("alice", "pw123", role="USER")
    r = await client.post(
        "/api/v1/auth/login", json={"username": "alice", "password": "pw123"}
    )
    headers = {"Authorization": f"Bearer {r.json()['data']['access_token']}"}
    r = await client.post(
        "/api/v1/admin/dicts/types", json={"type_code": "X", "name": "x"}, headers=headers
    )
    assert r.status_code == 403

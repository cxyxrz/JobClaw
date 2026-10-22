async def test_login_then_me(client, make_user):
    await make_user("alice", "pw123")
    r = await client.post(
        "/api/v1/auth/login", json={"username": "alice", "password": "pw123"}
    )
    assert r.status_code == 200
    body = r.json()
    assert body["code"] == 0
    assert body["trace_id"]
    assert r.headers.get("X-Request-ID") == body["trace_id"]
    token = body["data"]["access_token"]

    r2 = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert r2.status_code == 200
    assert r2.json()["data"]["username"] == "alice"


async def test_login_wrong_password(client, make_user):
    await make_user("bob", "pw123")
    r = await client.post(
        "/api/v1/auth/login", json={"username": "bob", "password": "nope"}
    )
    assert r.status_code == 401
    assert r.json()["code"] == 40100


async def test_me_without_token(client):
    r = await client.get("/api/v1/auth/me")
    assert r.status_code == 401
    assert r.json()["code"] == 40100


async def test_admin_ping_permission(client, make_user):
    await make_user("alice", "pw123", role="USER")
    await make_user("root", "pw123", role="ADMIN")

    r_user = await client.post(
        "/api/v1/auth/login", json={"username": "alice", "password": "pw123"}
    )
    r_admin = await client.post(
        "/api/v1/auth/login", json={"username": "root", "password": "pw123"}
    )
    tok_user = r_user.json()["data"]["access_token"]
    tok_admin = r_admin.json()["data"]["access_token"]

    denied = await client.get(
        "/api/v1/admin/ping", headers={"Authorization": f"Bearer {tok_user}"}
    )
    assert denied.status_code == 403
    assert denied.json()["code"] == 40300

    allowed = await client.get(
        "/api/v1/admin/ping", headers={"Authorization": f"Bearer {tok_admin}"}
    )
    assert allowed.status_code == 200
    assert allowed.json()["data"]["pong"] is True

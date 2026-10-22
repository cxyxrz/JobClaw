async def test_live(client):
    r = await client.get("/health/live")
    assert r.status_code == 200
    assert r.json() == {"status": "alive"}


async def test_ready(client):
    r = await client.get("/health/ready")
    assert r.status_code == 200
    assert r.json()["db"] == "ok"

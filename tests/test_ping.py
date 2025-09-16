from core.app import app
from fastapi.testclient import TestClient

def test_ping():
    client = TestClient(app)
    res = client.get("/ping", headers={"X-API-Key": "changeme"})
    assert res.status_code == 200
    data = res.json()
    assert data.get("ok") is True
    assert isinstance(data.get("ts"), int)

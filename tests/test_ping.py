import requests

def test_ping():
    res = requests.get("http://127.0.0.1:8000/ping", headers={"X-API-Key": "changeme"})
    assert res.status_code == 200
    assert res.json().get("ok") is True

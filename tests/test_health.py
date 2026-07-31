"""Health check and API key authentication tests."""

from tests.conftest import TEST_API_KEY


def test_health_no_auth(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["service"] == "home-lab-manager"


def test_dashboard_requires_api_key(client):
    r = client.get("/dashboard")
    assert r.status_code == 401


def test_dashboard_with_api_key(client, auth):
    r = client.get("/dashboard", headers=auth)
    assert r.status_code == 200
    body = r.json()
    assert body["total_networks"] == 0
    assert body["total_ips"] == 0


def test_invalid_api_key_rejected(client):
    r = client.get("/dashboard", headers={"X-API-KEY": "wrong-key"})
    assert r.status_code == 401


def test_all_resources_reject_missing_key(client):
    for path in ["/networks", "/ips", "/devices", "/tags", "/monitors", "/articles", "/search?q=x"]:
        r = client.get(path)
        assert r.status_code == 401, f"{path} should require auth"

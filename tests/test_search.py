"""Global search endpoint tests."""


def _seed(client, auth):
    net = client.post("/networks", json={"name": "Office", "cidr": "192.168.50.0/24"}, headers=auth).json()
    client.post(
        "/ips",
        json={"address": "192.168.50.10", "hostname": "printer", "network_id": net["id"]},
        headers=auth,
    )
    client.post("/devices", json={"name": "Web Server", "model": "R740"}, headers=auth)
    client.post("/articles", json={"title": "Backup runbook", "body": "How to backup"}, headers=auth)


def test_search_requires_query(client, auth):
    r = client.get("/search", headers=auth)
    assert r.status_code == 422


def test_search_finds_networks(client, auth):
    _seed(client, auth)
    r = client.get("/search", params={"q": "office"}, headers=auth)
    assert r.status_code == 200
    body = r.json()
    assert len(body["networks"]) == 1
    assert body["networks"][0]["name"] == "Office"


def test_search_finds_ips(client, auth):
    _seed(client, auth)
    r = client.get("/search", params={"q": "printer"}, headers=auth)
    assert len(r.json()["ip_addresses"]) == 1


def test_search_finds_devices_by_model(client, auth):
    _seed(client, auth)
    r = client.get("/search", params={"q": "R740"}, headers=auth)
    assert len(r.json()["devices"]) == 1


def test_search_finds_docs(client, auth):
    _seed(client, auth)
    r = client.get("/search", params={"q": "backup"}, headers=auth)
    assert len(r.json()["docs"]) == 1


def test_search_empty_results(client, auth):
    _seed(client, auth)
    r = client.get("/search", params={"q": "nothing-matches"}, headers=auth)
    body = r.json()
    assert body["networks"] == []
    assert body["ip_addresses"] == []
    assert body["devices"] == []
    assert body["docs"] == []


def test_search_limit(client, auth):
    _seed(client, auth)
    r = client.get("/search", params={"q": "a", "limit": 1}, headers=auth)
    assert r.status_code == 200

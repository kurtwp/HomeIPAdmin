"""Uptime monitor CRUD endpoint tests."""


def _create_monitor(client, auth, **overrides):
    body = {"ip_address": "192.168.2.1", "name": "Gateway", "monitor_type": "ping", **overrides}
    r = client.post("/monitors", json=body, headers=auth)
    assert r.status_code == 201, r.text
    return r.json()


def test_create_monitor(client, auth):
    data = _create_monitor(client, auth)
    assert data["name"] == "Gateway"
    assert data["ip_address"] == "192.168.2.1"
    assert data["monitor_type"] == "ping"
    assert data["check_interval"] == 60  # default
    assert data["is_enabled"] is True


def test_create_port_monitor(client, auth):
    data = _create_monitor(client, auth, name="Web", monitor_type="tcp", port=443, check_interval=30)
    assert data["monitor_type"] == "tcp"
    assert data["port"] == 443
    assert data["check_interval"] == 30


def test_list_monitors(client, auth):
    _create_monitor(client, auth)
    _create_monitor(client, auth, name="Second")
    r = client.get("/monitors", headers=auth)
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_get_monitor(client, auth):
    mon = _create_monitor(client, auth)
    r = client.get(f"/monitors/{mon['id']}", headers=auth)
    assert r.status_code == 200
    assert r.json()["name"] == "Gateway"


def test_get_monitor_not_found(client, auth):
    r = client.get("/monitors/9999", headers=auth)
    assert r.status_code == 404


def test_update_monitor(client, auth):
    mon = _create_monitor(client, auth)
    r = client.put(f"/monitors/{mon['id']}", json={"name": "Updated", "is_enabled": False}, headers=auth)
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "Updated"
    assert data["is_enabled"] is False


def test_delete_monitor(client, auth):
    mon = _create_monitor(client, auth)
    r = client.delete(f"/monitors/{mon['id']}", headers=auth)
    assert r.status_code == 204
    r = client.get(f"/monitors/{mon['id']}", headers=auth)
    assert r.status_code == 404

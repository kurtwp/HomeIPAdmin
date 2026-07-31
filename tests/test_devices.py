"""Device CRUD endpoint tests."""


def _create_device(client, auth, **overrides):
    body = {"name": "Test Device", "manufacturer": "Ubiquiti", "model": "USW-Pro-48", **overrides}
    r = client.post("/devices", json=body, headers=auth)
    assert r.status_code == 201, r.text
    return r.json()


def test_create_device(client, auth):
    data = _create_device(client, auth)
    assert data["name"] == "Test Device"
    assert data["manufacturer"] == "Ubiquiti"
    assert data["id"] > 0
    assert data["device_type"] is None


def test_list_devices(client, auth):
    _create_device(client, auth)
    _create_device(client, auth, name="Second")
    r = client.get("/devices", headers=auth)
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_get_device(client, auth):
    dev = _create_device(client, auth)
    r = client.get(f"/devices/{dev['id']}", headers=auth)
    assert r.status_code == 200
    assert r.json()["model"] == "USW-Pro-48"


def test_get_device_not_found(client, auth):
    r = client.get("/devices/9999", headers=auth)
    assert r.status_code == 404


def test_update_device(client, auth):
    dev = _create_device(client, auth)
    r = client.put(f"/devices/{dev['id']}", json={"location": "Rack 1", "shelf": "U12"}, headers=auth)
    assert r.status_code == 200
    data = r.json()
    assert data["location"] == "Rack 1"
    assert data["shelf"] == "U12"
    assert data["name"] == "Test Device"  # untouched


def test_search_devices(client, auth):
    _create_device(client, auth, name="Core Switch", serial_number="ABC123")
    _create_device(client, auth, name="Edge Router", serial_number="XYZ789")
    r = client.get("/devices", params={"search": "switch"}, headers=auth)
    assert len(r.json()) == 1
    r = client.get("/devices", params={"search": "XYZ789"}, headers=auth)
    assert len(r.json()) == 1


def test_delete_device(client, auth):
    dev = _create_device(client, auth)
    r = client.delete(f"/devices/{dev['id']}", headers=auth)
    assert r.status_code == 204
    r = client.get(f"/devices/{dev['id']}", headers=auth)
    assert r.status_code == 404

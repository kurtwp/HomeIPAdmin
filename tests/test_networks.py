"""Network CRUD endpoint tests."""


def _create_network(client, auth, **overrides):
    body = {"name": "Test Net", "cidr": "10.0.0.0/24", **overrides}
    r = client.post("/networks", json=body, headers=auth)
    assert r.status_code == 201, r.text
    return r.json()


def test_list_networks_empty(client, auth):
    r = client.get("/networks", headers=auth)
    assert r.status_code == 200
    assert r.json() == []


def test_create_network(client, auth):
    body = {
        "name": "Lab",
        "cidr": "192.168.10.0/24",
        "vlan_id": 10,
        "gateway": "192.168.10.1",
        "description": "test network",
    }
    r = client.post("/networks", json=body, headers=auth)
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "Lab"
    assert data["cidr"] == "192.168.10.0/24"
    assert data["vlan_id"] == 10
    assert data["id"] > 0


def test_create_network_requires_name(client, auth):
    r = client.post("/networks", json={"cidr": "10.1.0.0/24"}, headers=auth)
    assert r.status_code == 422


def test_get_network(client, auth):
    net = _create_network(client, auth)
    r = client.get(f"/networks/{net['id']}", headers=auth)
    assert r.status_code == 200
    assert r.json()["name"] == "Test Net"


def test_get_network_not_found(client, auth):
    r = client.get("/networks/9999", headers=auth)
    assert r.status_code == 404


def test_update_network(client, auth):
    net = _create_network(client, auth)
    r = client.put(
        f"/networks/{net['id']}",
        json={"name": "Renamed", "notes": "updated"},
        headers=auth,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "Renamed"
    assert data["notes"] == "updated"
    assert data["cidr"] == "10.0.0.0/24"  # untouched field preserved


def test_delete_network(client, auth):
    net = _create_network(client, auth)
    r = client.delete(f"/networks/{net['id']}", headers=auth)
    assert r.status_code == 204
    r = client.get(f"/networks/{net['id']}", headers=auth)
    assert r.status_code == 404


def test_delete_network_not_found(client, auth):
    r = client.delete("/networks/9999", headers=auth)
    assert r.status_code == 404


def test_list_networks_multiple(client, auth):
    _create_network(client, auth, name="A", cidr="10.0.0.0/24")
    _create_network(client, auth, name="B", cidr="10.1.0.0/24")
    r = client.get("/networks", headers=auth)
    assert len(r.json()) == 2

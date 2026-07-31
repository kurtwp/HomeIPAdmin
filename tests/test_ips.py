"""IP Address CRUD endpoint tests, including the string-vs-enum regression.

The IPAddress model uses Python Enum columns (AssignmentType, IPStatus) but
the API schema sends plain strings. Regression tests ensure create/update
convert strings to enums correctly (previously returned 500).
"""


def _create_network(client, auth):
    r = client.post("/networks", json={"name": "IP Net", "cidr": "10.5.0.0/24"}, headers=auth)
    assert r.status_code == 201
    return r.json()


def _create_ip(client, auth, network_id, **overrides):
    body = {
        "address": "10.5.0.50",
        "hostname": "host-50",
        "network_id": network_id,
        "assignment_type": "dhcp",
        "status": "active",
    }
    body.update(overrides)
    r = client.post("/ips", json=body, headers=auth)
    assert r.status_code == 201, r.text
    return r.json()


def test_create_ip_with_enum_strings(client, auth):
    """Regression: sending 'active'/'static' strings must not 500."""
    net = _create_network(client, auth)
    r = client.post(
        "/ips",
        json={
            "address": "10.5.0.10",
            "hostname": "server1",
            "network_id": net["id"],
            "assignment_type": "static",
            "status": "active",
        },
        headers=auth,
    )
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["address"] == "10.5.0.10"
    assert data["assignment_type"] == "static"
    assert data["status"] == "active"


def test_create_ip_defaults(client, auth):
    net = _create_network(client, auth)
    r = client.post(
        "/ips",
        json={"address": "10.5.0.20", "network_id": net["id"]},
        headers=auth,
    )
    assert r.status_code == 201
    data = r.json()
    assert data["assignment_type"] == "dhcp"
    assert data["status"] == "unknown"


def test_update_ip_status_and_type(client, auth):
    net = _create_network(client, auth)
    ip = _create_ip(client, auth, net["id"])
    r = client.put(
        f"/ips/{ip['id']}",
        json={"status": "inactive", "assignment_type": "reserved", "hostname": "renamed"},
        headers=auth,
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["status"] == "inactive"
    assert data["assignment_type"] == "reserved"
    assert data["hostname"] == "renamed"


def test_create_ip_requires_network(client, auth):
    """FK constraint must reject a nonexistent network_id (no orphan IPs)."""
    import pytest
    from sqlalchemy.exc import IntegrityError

    with pytest.raises(IntegrityError):
        client.post(
            "/ips",
            json={"address": "10.5.0.30", "network_id": 9999},
            headers=auth,
        )


def test_list_ips_filters(client, auth):
    net = _create_network(client, auth)
    _create_ip(client, auth, net["id"], address="10.5.0.1", status="active")
    _create_ip(client, auth, net["id"], address="10.5.0.2", status="inactive")
    _create_ip(client, auth, net["id"], address="10.5.0.3", status="active")

    r = client.get("/ips", params={"status": "active"}, headers=auth)
    assert len(r.json()) == 2

    r = client.get("/ips", params={"network_id": net["id"]}, headers=auth)
    assert len(r.json()) == 3

    r = client.get("/ips", params={"search": "10.5.0.1"}, headers=auth)
    assert len(r.json()) == 1
    assert r.json()[0]["address"] == "10.5.0.1"

    r = client.get("/ips", params={"limit": 2}, headers=auth)
    assert len(r.json()) == 2

    r = client.get("/ips", params={"offset": 2}, headers=auth)
    assert len(r.json()) == 1


def test_get_ip_not_found(client, auth):
    r = client.get("/ips/9999", headers=auth)
    assert r.status_code == 404


def test_delete_ip(client, auth):
    net = _create_network(client, auth)
    ip = _create_ip(client, auth, net["id"])
    r = client.delete(f"/ips/{ip['id']}", headers=auth)
    assert r.status_code == 204
    r = client.get(f"/ips/{ip['id']}", headers=auth)
    assert r.status_code == 404

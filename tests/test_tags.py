"""Tag CRUD endpoint tests (no update endpoint exists)."""


def test_create_tag(client, auth):
    r = client.post("/tags", json={"name": "production", "color": "#4caf50"}, headers=auth)
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "production"
    assert data["color"] == "#4caf50"
    assert data["id"] > 0


def test_create_tag_default_color(client, auth):
    r = client.post("/tags", json={"name": "defaults"}, headers=auth)
    assert r.status_code == 201
    assert r.json()["color"] == "#1976d2"


def test_list_tags_sorted(client, auth):
    client.post("/tags", json={"name": "zulu"}, headers=auth)
    client.post("/tags", json={"name": "alpha"}, headers=auth)
    r = client.get("/tags", headers=auth)
    names = [t["name"] for t in r.json()]
    assert names == sorted(names)


def test_get_tag(client, auth):
    tag = client.post("/tags", json={"name": "iot"}, headers=auth).json()
    r = client.get(f"/tags/{tag['id']}", headers=auth)
    assert r.status_code == 200
    assert r.json()["name"] == "iot"


def test_get_tag_not_found(client, auth):
    r = client.get("/tags/9999", headers=auth)
    assert r.status_code == 404


def test_delete_tag(client, auth):
    tag = client.post("/tags", json={"name": "temp"}, headers=auth).json()
    r = client.delete(f"/tags/{tag['id']}", headers=auth)
    assert r.status_code == 204
    r = client.get(f"/tags/{tag['id']}", headers=auth)
    assert r.status_code == 404

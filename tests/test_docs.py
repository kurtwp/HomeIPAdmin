"""Documentation article CRUD tests (router at /articles to avoid colliding
with FastAPI's Swagger UI at /docs)."""


def _create_doc(client, auth, **overrides):
    body = {"title": "How to reboot", "body": "## Steps\n1. Do it", "category": "how-to", **overrides}
    r = client.post("/articles", json=body, headers=auth)
    assert r.status_code == 201, r.text
    return r.json()


def test_create_doc(client, auth):
    data = _create_doc(client, auth)
    assert data["title"] == "How to reboot"
    assert data["category"] == "how-to"
    assert data["id"] > 0


def test_docs_path_is_swagger_not_crud(client, auth):
    """/docs is FastAPI's Swagger UI — the CRUD resource lives at /articles."""
    r = client.get("/docs", headers=auth)
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]


def test_list_docs(client, auth):
    _create_doc(client, auth)
    _create_doc(client, auth, title="Second", category="runbook")
    r = client.get("/articles", headers=auth)
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_get_doc(client, auth):
    doc = _create_doc(client, auth)
    r = client.get(f"/articles/{doc['id']}", headers=auth)
    assert r.status_code == 200
    assert r.json()["title"] == "How to reboot"


def test_get_doc_not_found(client, auth):
    r = client.get("/articles/9999", headers=auth)
    assert r.status_code == 404


def test_update_doc(client, auth):
    doc = _create_doc(client, auth)
    r = client.put(f"/articles/{doc['id']}", json={"body": "Updated body"}, headers=auth)
    assert r.status_code == 200
    data = r.json()
    assert data["body"] == "Updated body"
    assert data["title"] == "How to reboot"  # untouched


def test_delete_doc(client, auth):
    doc = _create_doc(client, auth)
    r = client.delete(f"/articles/{doc['id']}", headers=auth)
    assert r.status_code == 204
    r = client.get(f"/articles/{doc['id']}", headers=auth)
    assert r.status_code == 404

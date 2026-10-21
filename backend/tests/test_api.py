from app import crud
from app.models import Board
from fastapi.testclient import TestClient


def _setup(client: TestClient, h: dict) -> tuple[int, int, int]:
    """Create board 'plan' with one column and one card."""
    r = client.post("/api/boards", json={"name": "Plan"}, headers=h)
    assert r.status_code == 201
    board_id = r.json()["id"]
    col_id = client.post("/api/columns", json={"board_id": board_id}, headers=h).json()[
        "id"
    ]
    r = client.post("/api/cards", json={"column_id": col_id, "title": "x"}, headers=h)
    assert r.status_code == 201
    return board_id, col_id, r.json()["id"]


def test_e2e_flow_export(client: TestClient, auth_headers: dict):
    """Build a board, sort, export markdown."""
    h = auth_headers
    board_id = client.post("/api/boards", json={"name": "Planning"}, headers=h).json()[
        "id"
    ]
    col_id = client.post("/api/columns", json={"board_id": board_id}, headers=h).json()[
        "id"
    ]
    work = client.post(
        "/api/labels", json={"name": "Work", "color": "#ff0000"}, headers=h
    ).json()["id"]
    home = client.post(
        "/api/labels", json={"name": "Home", "color": "#00ff00"}, headers=h
    ).json()["id"]
    ids = {}
    for title in ("Buy milk", "Write report", "Call bank", "Archive old files"):
        ids[title] = client.post(
            "/api/cards", json={"column_id": col_id, "title": title}, headers=h
        ).json()["id"]
    for title, data in {
        "Write report": {"prio": True, "label_id": work},
        "Call bank": {"label_id": home},
        "Archive old files": {"is_completed": True},
    }.items():
        assert client.patch(f"/api/cards/{ids[title]}", json=data, headers=h).is_success
    assert client.post(f"/api/boards/{board_id}/sort?by=prio", headers=h).is_success
    r = client.get(
        f"/api/boards/{board_id}/export?fmt=markdown&completed_only=false", headers=h
    )
    assert r.json()["text"] == (
        "## Planning\n\n### New Column\n- [ ] Write report (Work) ⚑\n"
        "- [ ] Buy milk\n- [ ] Call bank (Home)\n- [x] Archive old files\n"
    )
    board = client.get("/api/boards/planning?touch=true", headers=h).json()
    assert [c["title"] for c in board["columns"][0]["cards"]] == [
        "Write report",
        "Buy milk",
        "Call bank",
        "Archive old files",
    ]


def test_other_user_gets_404(
    client: TestClient, auth_headers: dict, other_headers: dict
):
    board_id, col_id, card_id = _setup(client, auth_headers)
    o = other_headers
    assert client.get("/api/boards", headers=o).json() == []
    for method, url, body in [
        ("GET", "/api/boards/plan", None),
        ("PATCH", f"/api/boards/{board_id}", {"name": "x"}),
        ("DELETE", f"/api/boards/{board_id}", None),
        ("POST", f"/api/boards/{board_id}/sort?by=date", None),
        ("GET", f"/api/boards/{board_id}/export", None),
        ("DELETE", f"/api/boards/{board_id}/cards?mode=all", None),
        ("PUT", f"/api/boards/{board_id}/columns/order", {"ids": [col_id]}),
        ("POST", "/api/columns", {"board_id": board_id}),
        ("PATCH", f"/api/columns/{col_id}", {"name": "x"}),
        ("DELETE", f"/api/columns/{col_id}", None),
        ("POST", "/api/cards", {"column_id": col_id, "title": "x"}),
        ("PATCH", f"/api/cards/{card_id}", {"title": "y"}),
        ("PATCH", "/api/cards/bulk", {"ids": [card_id], "prio": True}),
        ("POST", f"/api/cards/{card_id}/move", {"column_id": col_id}),
        ("POST", f"/api/cards/{card_id}/copy", {"column_id": col_id}),
        ("DELETE", f"/api/cards/{card_id}", None),
    ]:
        r = client.request(method, url, json=body, headers=o)
        assert r.status_code == 404, (method, url, r.status_code)
    # own data untouched
    board = client.get("/api/boards/plan", headers=auth_headers).json()
    assert board["columns"][0]["cards"][0]["title"] == "x"


def test_cross_user_move_target_404(
    client: TestClient, auth_headers: dict, other_headers: dict
):
    _, _, card_id = _setup(client, auth_headers)
    r = client.post("/api/boards", json={"name": "Theirs"}, headers=other_headers)
    other_col = client.post(
        "/api/columns", json={"board_id": r.json()["id"]}, headers=other_headers
    ).json()["id"]
    r = client.post(
        f"/api/cards/{card_id}/move",
        json={"column_id": other_col},
        headers=auth_headers,
    )
    assert r.status_code == 404


def test_conflict_409(client: TestClient, auth_headers: dict):
    h = auth_headers
    client.post("/api/boards", json={"name": "a"}, headers=h)
    r = client.post("/api/boards", json={"name": "A"}, headers=h)
    assert r.status_code == 409
    assert r.json()["detail"] == "Board key must be unique"


def test_bulk_and_delete_preview(client: TestClient, auth_headers: dict):
    h = auth_headers
    board_id, _, card_id = _setup(client, h)
    client.patch(f"/api/cards/{card_id}", json={"is_completed": True}, headers=h)
    preview = client.get(
        f"/api/boards/{board_id}/cards/deletable?mode=completed", headers=h
    ).json()
    assert [c["id"] for c in preview] == [card_id]
    r = client.patch(
        "/api/cards/bulk", json={"ids": [card_id], "is_revive": True}, headers=h
    )
    assert r.status_code == 204
    r = client.delete(f"/api/boards/{board_id}/cards?mode=completed", headers=h)
    assert r.json() == {"count": 0}
    card = client.get("/api/boards/plan", headers=h).json()["columns"][0]["cards"][0]
    assert card["is_revive"]
    assert card["date_completed"] is None  # repeat reset
    r = client.patch(
        "/api/cards/bulk", json={"ids": [card_id], "label_id": 999}, headers=h
    )
    assert r.status_code == 404


def test_member_card_actions_only(
    client: TestClient, auth_headers: dict, other_headers: dict, session
):
    board_id, col_id, card_id = _setup(client, auth_headers)
    crud.add_board_member(session, session.get(Board, board_id), 2)
    m = other_headers
    boards = client.get("/api/boards", headers=m).json()
    assert [(b["id"], b["is_owner"]) for b in boards] == [(board_id, False)]
    assert client.get("/api/boards/plan", headers=m).json()["is_owner"] is False
    assert client.get("/api/boards/plan", headers=auth_headers).json()["is_owner"]
    for method, url, body in [
        ("POST", "/api/cards", {"column_id": col_id, "title": "y"}),
        ("PATCH", f"/api/cards/{card_id}", {"title": "z"}),
        ("PATCH", "/api/cards/bulk", {"ids": [card_id], "prio": True}),
        ("POST", f"/api/cards/{card_id}/move", {"column_id": col_id}),
        ("POST", f"/api/cards/{card_id}/copy", {"column_id": col_id}),
        ("DELETE", f"/api/cards/{card_id}", None),
    ]:
        r = client.request(method, url, json=body, headers=m)
        assert r.status_code < 300, (method, url, r.status_code)
    for method, url, body in [
        ("PATCH", f"/api/boards/{board_id}", {"name": "x"}),
        ("DELETE", f"/api/boards/{board_id}", None),
        ("POST", f"/api/boards/{board_id}/sort?by=date", None),
        ("GET", f"/api/boards/{board_id}/export", None),
        ("GET", f"/api/boards/{board_id}/cards/deletable?mode=all", None),
        ("DELETE", f"/api/boards/{board_id}/cards?mode=all", None),
        ("PUT", f"/api/boards/{board_id}/columns/order", {"ids": [col_id]}),
        ("POST", "/api/columns", {"board_id": board_id}),
        ("PATCH", f"/api/columns/{col_id}", {"name": "x"}),
        ("DELETE", f"/api/columns/{col_id}", None),
    ]:
        r = client.request(method, url, json=body, headers=m)
        assert r.status_code == 404, (method, url, r.status_code)


def test_owner_edit_and_delete(client: TestClient, auth_headers: dict):
    """Rename / re-key board, rename column, label lifecycle, cascading deletes."""
    h = auth_headers
    board_id, col_id, card_id = _setup(client, h)
    client.post("/api/boards", json={"name": "taken"}, headers=h)
    r = client.patch(f"/api/boards/{board_id}", json={"key": "taken"}, headers=h)
    assert r.status_code == 409
    r = client.patch(
        f"/api/boards/{board_id}", json={"name": " New ", "key": "NEW"}, headers=h
    )
    assert (r.json()["name"], r.json()["key"]) == ("New", "new")
    assert client.get("/api/boards/plan", headers=h).status_code == 404

    r = client.patch(f"/api/columns/{col_id}", json={"name": "Doing"}, headers=h)
    assert r.json()["name"] == "Doing"

    label_id = client.post(
        "/api/labels", json={"name": "Work", "color": "#FF0000"}, headers=h
    ).json()["id"]
    client.patch(f"/api/cards/{card_id}", json={"label_id": label_id}, headers=h)
    r = client.patch(
        f"/api/labels/{label_id}", json={"name": "Job", "color": "#00ff00"}, headers=h
    )
    assert r.json()["name"] == "Job"
    assert [lb["name"] for lb in client.get("/api/labels", headers=h).json()] == ["Job"]
    assert client.delete(f"/api/labels/{label_id}", headers=h).status_code == 204
    card = client.get("/api/boards/new", headers=h).json()["columns"][0]["cards"][0]
    assert card["label_id"] is None

    assert client.delete(f"/api/columns/{col_id}", headers=h).status_code == 204
    r = client.patch(f"/api/cards/{card_id}", json={"title": "y"}, headers=h)
    assert r.status_code == 404
    assert client.delete(f"/api/boards/{board_id}", headers=h).status_code == 204
    assert client.get("/api/boards/new", headers=h).status_code == 404

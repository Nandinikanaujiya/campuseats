"""
Tests for CampusEats Orders Service
CS 543 Web Services · Assignment 5
Team 11: Nandini Kanaujiya, Radhika Verma, Alka Jha, Alok Mishra
"""

import pytest
import uuid
from app import app
from store import store


AUTH = {"Authorization": "Bearer test-jwt-token"}


@pytest.fixture(autouse=True)
def reset_store():
    store.clear()
    yield
    store.clear()


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def make_order():
    return {
        "customer_id": str(uuid.uuid4()),
        "canteen_id": str(uuid.uuid4()),
        "items": [
            {
                "menu_item_id": str(uuid.uuid4()),
                "item_name": "Paneer Roll",
                "quantity": 2,
                "unit_price": 90.00
            }
        ],
        "delivery_fee": 20.00,
        "custom_notes": "Deliver to Canteen Benches"
    }


def test_create_order_201_and_location(client):
    res = client.post("/orders", json=make_order(), headers=AUTH)
    assert res.status_code == 201
    assert "Location" in res.headers
    assert res.headers["Location"].startswith("/orders/")
    assert "ETag" in res.headers
    assert res.headers["Content-Type"] == "application/json"


def test_idempotent_repeat(client):
    payload = make_order()
    headers = {**AUTH, "Idempotency-Key": "test-idem-key-123"}

    res1 = client.post("/orders", json=payload, headers=headers)
    assert res1.status_code == 201
    loc1 = res1.headers["Location"]

    res2 = client.post("/orders", json=payload, headers=headers)
    assert res2.status_code == 201
    assert res2.headers["Location"] == loc1
    assert res2.headers["X-Cache-Lookup"] == "HIT-IDEMPOTENT"


def test_conditional_get_304(client):
    res_create = client.post("/orders", json=make_order(), headers=AUTH)
    order_id = res_create.get_json()["id"]
    etag = res_create.headers["ETag"]

    # Normal GET -> 200
    res = client.get(f"/orders/{order_id}")
    assert res.status_code == 200
    assert res.headers["ETag"] == etag
    assert "max-age=60" in res.headers["Cache-Control"]

    # Conditional GET -> 304 with empty body
    res_cond = client.get(f"/orders/{order_id}", headers={"If-None-Match": etag})
    assert res_cond.status_code == 304
    assert res_cond.data == b""


def test_conditional_write_412_and_success(client):
    res_create = client.post("/orders", json=make_order(), headers=AUTH)
    order_id = res_create.get_json()["id"]
    etag = res_create.headers["ETag"]

    update_body = {"custom_notes": "Room 304"}

    # Missing If-Match -> 412
    res_no_match = client.put(f"/orders/{order_id}", json=update_body, headers=AUTH)
    assert res_no_match.status_code == 412

    # Wrong If-Match -> 412
    res_wrong = client.put(f"/orders/{order_id}", json=update_body, headers={**AUTH, "If-Match": '"wrong-etag"'})
    assert res_wrong.status_code == 412

    # Valid If-Match -> 200
    res_ok = client.put(f"/orders/{order_id}", json=update_body, headers={**AUTH, "If-Match": etag})
    assert res_ok.status_code == 200
    assert res_ok.headers["ETag"] != etag


def test_delete_order_204(client):
    res_create = client.post("/orders", json=make_order(), headers=AUTH)
    order_id = res_create.get_json()["id"]

    res_del = client.delete(f"/orders/{order_id}", headers=AUTH)
    assert res_del.status_code == 204
    assert res_del.data == b""

    assert client.get(f"/orders/{order_id}").status_code == 404


def test_options_and_allow(client):
    res = client.options("/orders")
    assert res.status_code == 204
    assert "Allow" in res.headers

    res_item = client.options(f"/orders/{uuid.uuid4()}")
    assert res_item.status_code == 204
    assert "Allow" in res_item.headers


def test_method_override(client):
    res_create = client.post("/orders", json=make_order(), headers=AUTH)
    order_id = res_create.get_json()["id"]

    res = client.post(f"/orders/{order_id}", headers={**AUTH, "X-HTTP-Method-Override": "DELETE"})
    assert res.status_code == 204
    assert client.get(f"/orders/{order_id}").status_code == 404


def test_accept_negotiation_406(client):
    res = client.get("/orders", headers={"Accept": "application/xml"})
    assert res.status_code == 406


def test_auth_401(client):
    # No auth header -> 401
    res = client.post("/orders", json=make_order())
    assert res.status_code == 401
    assert "WWW-Authenticate" in res.headers


def test_validation_400_and_422(client):
    # 400: Malformed JSON or missing fields
    res400 = client.post("/orders", data="not json", headers={**AUTH, "Content-Type": "application/json"})
    assert res400.status_code == 400

    # 422: Valid JSON, but domain refusal (empty items)
    res422 = client.post("/orders", json={
        "customer_id": str(uuid.uuid4()),
        "canteen_id": str(uuid.uuid4()),
        "items": []
    }, headers=AUTH)
    assert res422.status_code == 422


def test_not_found_404(client):
    res = client.get(f"/orders/{uuid.uuid4()}")
    assert res.status_code == 404


def test_conflict_409(client):
    res_create = client.post("/orders", json=make_order(), headers=AUTH)
    order_id = res_create.get_json()["id"]

    # First cancel -> 200
    res1 = client.post(f"/orders/{order_id}/cancel", json={"reason": "Wrong canteen"}, headers=AUTH)
    assert res1.status_code == 200

    # Second cancel -> 409
    res2 = client.post(f"/orders/{order_id}/cancel", json={"reason": "Already cancelled"}, headers=AUTH)
    assert res2.status_code == 409


def test_list_orders_query_params(client):
    cust_id = str(uuid.uuid4())
    p = make_order()
    p["customer_id"] = cust_id
    client.post("/orders", json=p, headers=AUTH)

    res = client.get(f"/orders?customer_id={cust_id}&page=1&limit=5")
    assert res.status_code == 200
    assert len(res.get_json()["orders"]) == 1
    assert res.headers["Cache-Control"] == "no-store"


def test_redirect_301(client):
    order_id = str(uuid.uuid4())
    res = client.get(f"/order/{order_id}")
    assert res.status_code == 301
    assert res.headers["Location"] == f"/orders/{order_id}"

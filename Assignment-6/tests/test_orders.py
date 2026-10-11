"""
CampusEats Orders Service — Test Suite
CS 543 Web Services · Assignment 6
Team 11: Nandini Kanaujiya, Radhika Verma, Alka Jha, Alok Mishra
"""

import pytest
import uuid
import xml.etree.ElementTree as ET
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


def make_valid_payload():
    return {
        "customer_id": str(uuid.uuid4()),
        "canteen_id": str(uuid.uuid4()),
        "address": "Hostel 4, Room 201, South Campus",
        "items": [
            {
                "menu_item_id": str(uuid.uuid4()),
                "item_name": "Paneer Butter Masala Roll",
                "quantity": 2,
                "unit_price": 95.00
            }
        ],
        "delivery_fee": 25.00,
        "custom_notes": "Extra mint chutney please"
    }


# =============================================================================
# PART A & C: Status Codes, Location Header, Charset
# =============================================================================
def test_create_order_201_and_location(client):
    payload = make_valid_payload()
    res = client.post("/orders", json=payload, headers=AUTH)
    assert res.status_code == 201
    assert "Location" in res.headers
    assert res.headers["Location"].startswith("/orders/")
    assert "ETag" in res.headers
    assert "charset=utf-8" in res.headers["Content-Type"].lower()
    assert res.headers["Content-Type"].startswith("application/json")

    data = res.get_json()
    assert data["address"] == payload["address"]
    assert data["status"] == "placed"


def test_rate_limit_429_with_retry_after(client):
    headers = {**AUTH, "Authorization": "Bearer rate-limited-client"}
    # Trigger 60 calls
    for _ in range(60):
        client.get("/orders", headers=headers)

    res = client.get("/orders", headers=headers)
    assert res.status_code == 429
    assert "Retry-After" in res.headers
    assert int(res.headers["Retry-After"]) >= 1

    err = res.get_json()
    assert err["type"] == "https://campuseats.internal/errors/rate-limit-exceeded"
    assert err["status"] == 429


def test_service_unavailable_503_with_retry_after(client):
    store.set_outage(True)
    res = client.get("/orders", headers=AUTH)
    assert res.status_code == 503
    assert "Retry-After" in res.headers
    assert res.headers["Retry-After"] == "60"

    err = res.get_json()
    assert err["type"] == "https://campuseats.internal/errors/service-unavailable"
    assert err["status"] == 503


# =============================================================================
# PART B & C: Problem Details, Type Catalogue, Field-Level 422 Errors
# =============================================================================
def test_create_order_empty_cart_422(client):
    payload = make_valid_payload()
    payload["items"] = []

    res = client.post("/orders", json=payload, headers=AUTH)
    assert res.status_code == 422
    assert "application/problem+json" in res.headers["Content-Type"]

    err = res.get_json()
    assert err["type"] == "https://campuseats.internal/errors/empty-cart"
    assert err["status"] == 422
    assert "errors" in err
    assert any(e["field"] == "items" for e in err["errors"])


def test_create_order_two_bad_fields_simultaneously(client):
    payload = make_valid_payload()
    # Field 1 bad: quantity <= 0
    payload["items"][0]["quantity"] = 0
    # Field 2 bad: address missing / empty
    payload["address"] = ""

    res = client.post("/orders", json=payload, headers=AUTH)
    assert res.status_code == 422

    err = res.get_json()
    assert err["type"] == "https://campuseats.internal/errors/validation-error"
    assert err["status"] == 422
    assert "errors" in err
    assert len(err["errors"]) >= 2

    fields = [e["field"] for e in err["errors"]]
    assert "address" in fields
    assert "items[0].quantity" in fields


def test_item_unavailable_422(client):
    payload = make_valid_payload()
    payload["items"][0]["item_name"] = "Mango Lassi (Out of Stock)"

    res = client.post("/orders", json=payload, headers=AUTH)
    assert res.status_code == 422

    err = res.get_json()
    assert err["type"] == "https://campuseats.internal/errors/item-unavailable"
    assert err["status"] == 422


def test_payment_declined_422(client):
    payload = make_valid_payload()
    payload["payment_token"] = "tok_fail_card_declined"

    res = client.post("/orders", json=payload, headers=AUTH)
    assert res.status_code == 422

    err = res.get_json()
    assert err["type"] == "https://campuseats.internal/errors/payment-declined"
    assert err["status"] == 422


def test_order_not_found_404(client):
    random_id = str(uuid.uuid4())
    res = client.get(f"/orders/{random_id}")
    assert res.status_code == 404

    err = res.get_json()
    assert err["type"] == "https://campuseats.internal/errors/order-not-found"
    assert err["status"] == 404


def test_illegal_transition_409(client):
    # 1. Create order
    res_create = client.post("/orders", json=make_valid_payload(), headers=AUTH)
    order_id = res_create.get_json()["id"]

    # 2. Cancel order
    res_cancel1 = client.post(f"/orders/{order_id}/cancel", json={"reason": "Selected wrong hostel address"}, headers=AUTH)
    assert res_cancel1.status_code == 200

    # 3. Second cancel -> 409 Conflict (illegal-transition)
    res_cancel2 = client.post(f"/orders/{order_id}/cancel", json={"reason": "Cancel again"}, headers=AUTH)
    assert res_cancel2.status_code == 409

    err = res_cancel2.get_json()
    assert err["type"] == "https://campuseats.internal/errors/illegal-transition"
    assert err["status"] == 409

    # 4. Attempt to delete cancelled order is allowed, but deleting preparing order is 409
    res_create2 = client.post("/orders", json=make_valid_payload(), headers=AUTH)
    order_id2 = res_create2.get_json()["id"]
    order2 = store.get(order_id2)
    order2.status = "preparing"

    res_del_conflict = client.delete(f"/orders/{order_id2}", headers=AUTH)
    assert res_del_conflict.status_code == 409
    err_del = res_del_conflict.get_json()
    assert err_del["type"] == "https://campuseats.internal/errors/illegal-transition"


# =============================================================================
# PART A1: PATCH /orders/<id>
# =============================================================================
def test_patch_order(client):
    res_create = client.post("/orders", json=make_valid_payload(), headers=AUTH)
    order_id = res_create.get_json()["id"]

    # Valid PATCH
    patch_body = {"address": "Hostel 7, Room 302"}
    res_patch = client.patch(f"/orders/{order_id}", json=patch_body, headers=AUTH)
    assert res_patch.status_code == 200
    assert res_patch.get_json()["address"] == "Hostel 7, Room 302"

    # Invalid PATCH (disallowed field)
    res_bad_patch = client.patch(f"/orders/{order_id}", json={"status": "delivered"}, headers=AUTH)
    assert res_bad_patch.status_code == 422


# =============================================================================
# PART C3: Content Negotiation (JSON vs XML, 406 Not Acceptable)
# =============================================================================
def test_content_negotiation_xml(client):
    res_create = client.post("/orders", json=make_valid_payload(), headers=AUTH)
    order_id = res_create.get_json()["id"]

    # Request XML representation
    res_xml = client.get(f"/orders/{order_id}", headers={"Accept": "application/xml"})
    assert res_xml.status_code == 200
    assert "application/xml" in res_xml.headers["Content-Type"]
    assert "charset=utf-8" in res_xml.headers["Content-Type"].lower()

    # Parse XML response
    xml_tree = ET.fromstring(res_xml.data)
    assert xml_tree.tag == "order"
    assert xml_tree.find("id").text == order_id
    assert xml_tree.find("address").text == "Hostel 4, Room 201, South Campus"


def test_content_negotiation_406_not_acceptable(client):
    res = client.get("/orders", headers={"Accept": "text/csv"})
    assert res.status_code == 406
    assert res.get_json()["type"] == "https://campuseats.internal/errors/not-acceptable"


# =============================================================================
# PART D4: Regression Checks from A5 (Idempotency, Conditional GET/PUT, 204)
# =============================================================================
def test_idempotent_repeat(client):
    payload = make_valid_payload()
    headers = {**AUTH, "Idempotency-Key": "a6-idem-key-999"}

    res1 = client.post("/orders", json=payload, headers=headers)
    assert res1.status_code == 201
    loc1 = res1.headers["Location"]

    res2 = client.post("/orders", json=payload, headers=headers)
    assert res2.status_code == 201
    assert res2.headers["Location"] == loc1
    assert res2.headers["X-Cache-Lookup"] == "HIT-IDEMPOTENT"


def test_conditional_get_304(client):
    res_create = client.post("/orders", json=make_valid_payload(), headers=AUTH)
    order_id = res_create.get_json()["id"]
    etag = res_create.headers["ETag"]

    res_cond = client.get(f"/orders/{order_id}", headers={"If-None-Match": etag})
    assert res_cond.status_code == 304
    assert res_cond.data == b""


def test_conditional_write_412(client):
    res_create = client.post("/orders", json=make_valid_payload(), headers=AUTH)
    order_id = res_create.get_json()["id"]

    # PUT without If-Match -> 412
    res_put = client.put(f"/orders/{order_id}", json={"address": "New Block A"}, headers=AUTH)
    assert res_put.status_code == 412
    assert res_put.get_json()["type"] == "https://campuseats.internal/errors/precondition-failed"


def test_delete_order_204(client):
    res_create = client.post("/orders", json=make_valid_payload(), headers=AUTH)
    order_id = res_create.get_json()["id"]

    res_del = client.delete(f"/orders/{order_id}", headers=AUTH)
    assert res_del.status_code == 204
    assert res_del.data == b""
    assert client.get(f"/orders/{order_id}").status_code == 404

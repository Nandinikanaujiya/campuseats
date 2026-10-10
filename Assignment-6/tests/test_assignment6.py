import pytest
import uuid
from Assignment_6.app import app

AUTH = {"Authorization": "Bearer test-jwt-token"}


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def make_order(**overrides):
    payload = {
        "customer_id": str(uuid.uuid4()),
        "canteen_id": str(uuid.uuid4()),
        "address": "Room 101, Hostel A",
        "items": [{
            "menu_item_id": str(uuid.uuid4()),
            "item_name": "Paneer Roll",
            "quantity": 2,
            "unit_price": 90.0,
        }],
    }
    payload.update(overrides)
    return payload


def test_create_order_201_and_location(client):
    res = client.post("/orders", json=make_order(), headers=AUTH)
    assert res.status_code == 201
    assert "Location" in res.headers
    assert res.headers["Location"].startswith("/orders/")
    assert res.headers["Content-Type"].startswith("application/json")


def test_idempotency_replay_uses_same_location(client):
    payload = make_order()
    headers = {**AUTH, "Idempotency-Key": "idem-a6-42"}
    r1 = client.post("/orders", json=payload, headers=headers)
    r2 = client.post("/orders", json=payload, headers=headers)
    assert r1.status_code == 201
    assert r2.status_code == 201
    assert r2.headers["Location"] == r1.headers["Location"]


def test_empty_cart_returns_problem_details(client):
    res = client.post("/orders", json=make_order(items=[]), headers=AUTH)
    assert res.status_code == 422
    data = res.get_json()
    assert data["type"].endswith("/empty-cart") or "empty-cart" in data["type"]
    assert data["status"] == 422
    assert any(err["field"] == "items" for err in data["errors"])


def test_quantity_zero_and_bool_are_invalid(client):
    for qty in [0, -1, True, False]:
        res = client.post(
            "/orders",
            json=make_order(items=[{
                "menu_item_id": str(uuid.uuid4()),
                "item_name": "Coke",
                "quantity": qty,
                "unit_price": 25.0,
            }]),
            headers=AUTH,
        )
        assert res.status_code == 422


def test_multiple_validation_errors_in_one_response(client):
    payload = {
        "customer_id": "not-a-uuid",
        "canteen_id": "also-bad",
        "address": "   ",
        "items": [{
            "menu_item_id": str(uuid.uuid4()),
            "item_name": "Rice Bowl",
            "quantity": 0,
            "unit_price": -1,
        }],
    }
    res = client.post("/orders", json=payload, headers=AUTH)
    assert res.status_code == 422
    body = res.get_json()
    assert "errors" in body
    assert len(body["errors"]) >= 2


def test_missing_or_blank_address_is_invalid(client):
    res = client.post("/orders", json=make_order(address="   "), headers=AUTH)
    assert res.status_code == 422


def test_unknown_order_id_returns_404(client):
    res = client.get(f"/orders/{uuid.uuid4()}", headers={"Accept": "application/json"})
    assert res.status_code == 404
    body = res.get_json()
    assert body["type"].endswith("order-not-found")


def test_illegal_transition_returns_409(client):
    payload = make_order()
    created = client.post("/orders", json=payload, headers=AUTH)
    order_id = created.get_json()["id"]
    cancel = client.post(f"/orders/{order_id}/cancel", json={"reason": "Wrong canteen"}, headers=AUTH)
    assert cancel.status_code == 200
    again = client.post(f"/orders/{order_id}/cancel", json={"reason": "Already cancelled"}, headers=AUTH)
    assert again.status_code == 409
    assert again.get_json()["type"].endswith("illegal-transition")


def test_payment_declined_problem_type(client):
    payload = make_order(payment_token="tok_fail_card_declined")
    res = client.post("/orders", json=payload, headers=AUTH)
    assert res.status_code == 422
    assert "payment-declined" in res.get_json()["type"]


def test_rate_limit_returns_retry_after(client):
    for _ in range(60):
        client.get("/orders", headers={"Authorization": "Bearer test-jwt-token"})
    res = client.get("/orders", headers={"Authorization": "Bearer test-jwt-token"})
    assert res.status_code == 429
    assert "Retry-After" in res.headers


def test_accept_xml_and_406(client):
    payload = make_order()
    created = client.post("/orders", json=payload, headers=AUTH)
    order_id = created.get_json()["id"]

    xml_res = client.get(f"/orders/{order_id}", headers={"Accept": "application/xml"})
    assert xml_res.status_code == 200
    assert xml_res.headers["Content-Type"].startswith("application/xml")

    pdf_res = client.get(f"/orders/{order_id}", headers={"Accept": "application/pdf"})
    assert pdf_res.status_code == 406


def test_problem_details_use_utf8_charset(client):
    res = client.post("/orders", json=make_order(items=[]), headers=AUTH)
    assert res.status_code == 422
    assert "application/problem+json; charset=utf-8" in res.headers["Content-Type"]


def test_unsupported_media_type_for_request_body(client):
    res = client.post(
        "/orders",
        data="not-json",
        headers={**AUTH, "Content-Type": "text/plain"},
    )
    assert res.status_code == 415

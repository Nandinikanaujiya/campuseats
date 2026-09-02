"""
CampusEats Orders Service — Automated Test Suite
CS 543 Web Services · Assignment 4
Team 10: Nandini Kanaujiya, Radhika Verma, Alka Jha, Alok Mishra

Requirement C8: Write four tests
1. Create succeeds with right code (201) and Location header
2. Idempotent repeat returns original response without duplicating
3. Failure path returns right 4xx (400, 422, 409) with RFC 7807 problem shape
4. Unknown ID returns 404 Not Found
"""

import sys
import os
import pytest
from unittest.mock import patch

# Ensure Assignment-4 directory is in sys.path
assignment_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if assignment_dir not in sys.path:
    sys.path.insert(0, assignment_dir)

from app import app
from store import store


@pytest.fixture(autouse=True)
def clean_store():
    """Reset store before each test."""
    store.clear()
    yield
    store.clear()


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


SAMPLE_PAYLOAD = {
    "customer_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "canteen_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
    "items": [
        {
            "menu_item_id": "a81bc81b-dead-4e5d-abff-90865d1e13b1",
            "item_name": "Veg Thali Deluxe",
            "quantity": 2,
            "unit_price": 120.00
        }
    ],
    "delivery_fee": 30.00,
    "payment_token": "tok_visa_valid",
    "custom_notes": "Call upon delivery at hostel entrance"
}


# -----------------------------------------------------------------------------
# Test 1: Create succeeds with code 201 and Location header (Requirement C8.1)
# -----------------------------------------------------------------------------
def test_create_order_success(client):
    with patch("client.payment_client.charge") as mock_charge:
        mock_charge.return_value = {
            "transaction_id": "txn_mock_123",
            "status": "authorized"
        }

        response = client.post("/orders", json=SAMPLE_PAYLOAD)

        assert response.status_code == 201
        assert "Location" in response.headers
        location = response.headers["Location"]
        assert location.startswith("/orders/")

        data = response.get_json()
        assert data["id"] in location
        assert data["status"] == "placed"
        assert data["customer_id"] == SAMPLE_PAYLOAD["customer_id"]
        assert data["subtotal"] == 240.00
        assert data["service_fee"] == 15.00
        assert data["delivery_fee"] == 30.00
        assert data["tax"] == 12.00
        assert data["total_price"] == 297.00

        # Verify internal records are NOT leaked in representation (Requirement C2)
        assert "raw_payment_token" not in data
        assert "internal_version" not in data
        assert "audit_trail" not in data
        assert "created_at_epoch" not in data

        # Outbound payment client was invoked with correct amount
        mock_charge.assert_called_once()


# -----------------------------------------------------------------------------
# Test 2: Idempotent repeat returns the original result (Requirement C8.2)
# -----------------------------------------------------------------------------
def test_create_order_idempotent_repeat(client):
    idempotency_key = "idemp-key-test-998877"

    with patch("client.payment_client.charge") as mock_charge:
        mock_charge.return_value = {"transaction_id": "txn_111", "status": "authorized"}

        # First request
        resp1 = client.post(
            "/orders",
            json=SAMPLE_PAYLOAD,
            headers={"Idempotency-Key": idempotency_key}
        )
        assert resp1.status_code == 201
        data1 = resp1.get_json()
        order_id_1 = data1["id"]

        # Duplicate repeat request with same Idempotency-Key
        resp2 = client.post(
            "/orders",
            json=SAMPLE_PAYLOAD,
            headers={"Idempotency-Key": idempotency_key}
        )

        assert resp2.status_code == 201
        assert resp2.headers["Location"] == resp1.headers["Location"]
        assert resp2.headers.get("X-Cache-Lookup") == "HIT-IDEMPOTENT"

        data2 = resp2.get_json()
        assert data2["id"] == order_id_1
        assert data2 == data1

        # Crucial check: Payment client was called ONLY ONCE
        assert mock_charge.call_count == 1

        # Store contains only 1 order
        assert len(store.list_all()) == 1


# -----------------------------------------------------------------------------
# Test 3: Failure paths return correct 4xx with RFC 7807 (Requirement C8.3)
# -----------------------------------------------------------------------------
def test_failure_paths_return_right_4xx(client):
    # 3a. Malformed JSON / missing mandatory field -> 400 Bad Request
    bad_payload = {"canteen_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7"}  # missing customer_id & items
    resp_400 = client.post("/orders", json=bad_payload)
    assert resp_400.status_code == 400
    assert resp_400.headers["Content-Type"] == "application/problem+json"
    err400 = resp_400.get_json()
    assert err400["status"] == 400
    assert err400["title"] == "Bad Request"
    assert "Missing mandatory field" in err400["detail"]

    # 3b. Domain rule refusal (empty items list) -> 422 Unprocessable Entity
    empty_items_payload = {
        "customer_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "canteen_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
        "items": []
    }
    resp_422 = client.post("/orders", json=empty_items_payload)
    assert resp_422.status_code == 422
    assert resp_422.headers["Content-Type"] == "application/problem+json"
    err422 = resp_422.get_json()
    assert err422["status"] == 422
    assert "at least one line item" in err422["detail"]

    # 3c. State conflict (attempting to cancel an already cancelled order) -> 409 Conflict
    with patch("client.payment_client.charge", return_value={"status": "authorized"}):
        create_resp = client.post("/orders", json=SAMPLE_PAYLOAD)
        created_id = create_resp.get_json()["id"]

    # First cancellation succeeds
    cancel_resp = client.post(
        f"/orders/{created_id}/cancellation",
        json={"reason": "Student requested cancellation"}
    )
    assert cancel_resp.status_code == 200
    assert cancel_resp.get_json()["status"] == "cancelled"

    # Second cancellation on same order triggers 409 Conflict
    conflict_resp = client.post(
        f"/orders/{created_id}/cancellation",
        json={"reason": "Duplicate cancellation attempt"}
    )
    assert conflict_resp.status_code == 409
    assert conflict_resp.headers["Content-Type"] == "application/problem+json"
    err409 = conflict_resp.get_json()
    assert err409["status"] == 409
    assert err409["title"] == "State Conflict"
    assert "already been cancelled" in err409["detail"]


# -----------------------------------------------------------------------------
# Test 4: Unknown ID returns 404 Not Found (Requirement C8.4)
# -----------------------------------------------------------------------------
def test_unknown_id_returns_404(client):
    unknown_id = "00000000-0000-0000-0000-000000000000"
    resp = client.get(f"/orders/{unknown_id}")

    assert resp.status_code == 404
    assert resp.headers["Content-Type"] == "application/problem+json"
    data = resp.get_json()
    assert data["status"] == 404
    assert data["title"] == "Not Found"
    assert unknown_id in data["detail"]

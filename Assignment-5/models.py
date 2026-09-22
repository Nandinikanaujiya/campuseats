"""
CampusEats Orders Service — Domain Models & Validation
CS 543 Web Services · Assignment 5
Team 11: Nandini Kanaujiya, Radhika Verma, Alka Jha, Alok Mishra
"""

import uuid
import json
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, Tuple, Optional, List


def is_valid_uuid(val: str) -> bool:
    try:
        uuid.UUID(str(val))
        return True
    except (ValueError, AttributeError, TypeError):
        return False


def validate_order_payload(data: Any) -> Tuple[bool, Optional[str], int]:
    """
    Validates the JSON body for creating an order.
    Returns: (is_valid, error_message, status_code)
    """
    if not isinstance(data, dict):
        return False, "Request body must be a JSON object.", 400

    required_fields = ["customer_id", "canteen_id", "items"]
    for field in required_fields:
        if field not in data:
            return False, f"Missing mandatory field '{field}'.", 400

    if not is_valid_uuid(data["customer_id"]):
        return False, f"Field 'customer_id' must be a valid UUID.", 400

    if not is_valid_uuid(data["canteen_id"]):
        return False, f"Field 'canteen_id' must be a valid UUID.", 400

    items = data.get("items")
    if not isinstance(items, list):
        return False, "Field 'items' must be a JSON array of items.", 400

    # Domain rule: Order cannot be empty (422)
    if len(items) == 0:
        return False, "An order must contain at least one line item.", 422

    for index, item in enumerate(items):
        if not isinstance(item, dict):
            return False, f"Item at index {index} must be a JSON object.", 400

        for f in ["menu_item_id", "item_name", "quantity", "unit_price"]:
            if f not in item:
                return False, f"Item at index {index} is missing '{f}'.", 400

        if not is_valid_uuid(item["menu_item_id"]):
            return False, f"Item at index {index} 'menu_item_id' must be a valid UUID.", 400

        if not isinstance(item["quantity"], int) or item["quantity"] <= 0:
            return False, f"Item at index {index} 'quantity' must be an integer >= 1.", 422

        if not isinstance(item["unit_price"], (int, float)) or item["unit_price"] < 0:
            return False, f"Item at index {index} 'unit_price' must be >= 0.", 422

    return True, None, 200


def validate_update_payload(data: Any) -> Tuple[bool, Optional[str], int]:
    """
    Validates update payload for PUT /orders/<id>.
    """
    if not isinstance(data, dict):
        return False, "Request body must be a JSON object.", 400

    if "custom_notes" in data and not isinstance(data["custom_notes"], str):
        return False, "Field 'custom_notes' must be a string.", 400

    if "items" in data:
        items = data["items"]
        if not isinstance(items, list) or len(items) == 0:
            return False, "Field 'items' must be a non-empty array.", 422

    return True, None, 200


def validate_cancellation_payload(data: Any) -> Tuple[bool, Optional[str], int]:
    """
    Validates cancellation payload for POST /orders/<id>/cancel.
    """
    if not isinstance(data, dict):
        return False, "Request body must be a JSON object.", 400

    reason = data.get("reason")
    if not reason or not isinstance(reason, str) or len(reason.strip()) < 3:
        return False, "Field 'reason' must be a string of at least 3 characters.", 400

    return True, None, 200


class Order:
    def __init__(
        self,
        customer_id: str,
        canteen_id: str,
        items: List[Dict[str, Any]],
        delivery_fee: float = 30.00,
        payment_token: Optional[str] = None,
        custom_notes: Optional[str] = None,
        order_id: Optional[str] = None
    ):
        self.id = order_id or str(uuid.uuid4())
        self.customer_id = customer_id
        self.canteen_id = canteen_id
        self.status = "placed"
        self.items = items
        self.custom_notes = custom_notes

        self.service_fee = 15.00
        self.delivery_fee = round(float(delivery_fee), 2)
        self._calculate_total()

        now = datetime.now(timezone.utc).isoformat()
        self.ordered_at = now
        self.updated_at = now
        self.cancelled_at: Optional[str] = None
        self.cancellation_reason: Optional[str] = None

        self.version = 1
        self.raw_payment_token = payment_token or "tok_simulated_secure"

    def _calculate_total(self) -> None:
        self.subtotal = round(sum(float(item["unit_price"]) * int(item["quantity"]) for item in self.items), 2)
        self.tax = round(self.subtotal * 0.05, 2)  # 5% campus tax
        self.total_price = round(self.subtotal + self.service_fee + self.delivery_fee + self.tax, 2)

    def compute_etag(self) -> str:
        """
        Computes MD5 hash representing resource state for caching and concurrency checks.
        """
        data = {
            "id": self.id,
            "version": self.version,
            "status": self.status,
            "total_price": self.total_price,
            "custom_notes": self.custom_notes,
            "updated_at": self.updated_at
        }
        digest = hashlib.md5(json.dumps(data, sort_keys=True).encode("utf-8")).hexdigest()
        return f'"{digest}"'

    def replace(self, data: Dict[str, Any]) -> None:
        """
        Replaces editable fields on PUT.
        """
        if "custom_notes" in data:
            self.custom_notes = data["custom_notes"]
        if "items" in data:
            self.items = data["items"]
            self._calculate_total()

        self.version += 1
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def cancel(self, reason: str) -> None:
        self.status = "cancelled"
        now = datetime.now(timezone.utc).isoformat()
        self.cancelled_at = now
        self.updated_at = now
        self.cancellation_reason = reason.strip()
        self.version += 1

    def as_json(self) -> Dict[str, Any]:
        result = {
            "id": self.id,
            "customer_id": self.customer_id,
            "canteen_id": self.canteen_id,
            "status": self.status,
            "items": self.items,
            "subtotal": self.subtotal,
            "service_fee": self.service_fee,
            "delivery_fee": self.delivery_fee,
            "tax": self.tax,
            "total_price": self.total_price,
            "ordered_at": self.ordered_at,
            "updated_at": self.updated_at,
            "cancelled_at": self.cancelled_at,
            "cancellation_reason": self.cancellation_reason,
            "version": self.version
        }
        if self.custom_notes:
            result["custom_notes"] = self.custom_notes
        return result

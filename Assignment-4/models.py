"""
CampusEats Orders Service — Domain Models & Validation
CS 543 Web Services · Assignment 4
Team 10: Nandini Kanaujiya, Radhika Verma, Alka Jha, Alok Mishra
"""

import uuid
import time
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
    Validates the incoming JSON body for creating an order (Requirement C4).
    Enforces required fields, datatypes, and domain constraints.
    Returns: (is_valid, error_detail, status_code)
    """
    if not isinstance(data, dict):
        return False, "Request body must be a JSON object.", 400

    required_fields = ["customer_id", "canteen_id", "items"]
    for field in required_fields:
        if field not in data:
            return False, f"Missing mandatory field '{field}'.", 400

    customer_id = data.get("customer_id")
    if not is_valid_uuid(customer_id):
        return False, f"Field 'customer_id' must be a valid UUID string (got: {customer_id}).", 400

    canteen_id = data.get("canteen_id")
    if not is_valid_uuid(canteen_id):
        return False, f"Field 'canteen_id' must be a valid UUID string (got: {canteen_id}).", 400

    items = data.get("items")
    if not isinstance(items, list):
        return False, "Field 'items' must be a JSON array of line items.", 400

    # Domain rule: Order cannot be empty
    if len(items) == 0:
        return False, "An order must contain at least one line item.", 422

    for index, item in enumerate(items):
        if not isinstance(item, dict):
            return False, f"Item at index {index} must be a JSON object.", 400

        for item_field in ["menu_item_id", "item_name", "quantity", "unit_price"]:
            if item_field not in item:
                return False, f"Item at index {index} is missing mandatory field '{item_field}'.", 400

        if not is_valid_uuid(item["menu_item_id"]):
            return False, f"Item at index {index} 'menu_item_id' must be a valid UUID.", 400

        qty = item["quantity"]
        if not isinstance(qty, int) or qty <= 0:
            return False, f"Item at index {index} 'quantity' must be a positive integer >= 1.", 422

        price = item["unit_price"]
        if not isinstance(price, (int, float)) or price < 0.0:
            return False, f"Item at index {index} 'unit_price' must be a non-negative number.", 422

    # Delivery fee validation if provided
    delivery_fee = data.get("delivery_fee", 30.00)
    if not isinstance(delivery_fee, (int, float)) or delivery_fee < 0.0:
        return False, "Field 'delivery_fee' must be a non-negative number.", 422

    return True, None, 200


def validate_cancellation_payload(data: Any) -> Tuple[bool, Optional[str], int]:
    """
    Validates cancellation request body.
    """
    if not isinstance(data, dict):
        return False, "Request body must be a JSON object.", 400

    reason = data.get("reason")
    if not reason or not isinstance(reason, str) or len(reason.strip()) < 3:
        return False, "Field 'reason' must be a string of at least 3 characters.", 400

    return True, None, 200


class Order:
    """
    Order Domain Model.
    Separates the stored database record from the published REST representation (Requirement C2).
    """

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

        # Financial calculations
        self.subtotal = round(sum(float(item["unit_price"]) * int(item["quantity"]) for item in items), 2)
        self.service_fee = 15.00
        self.delivery_fee = round(float(delivery_fee), 2)
        self.tax = round(self.subtotal * 0.05, 2)  # 5% campus dining GST/tax
        self.total_price = round(self.subtotal + self.service_fee + self.delivery_fee + self.tax, 2)

        now = datetime.now(timezone.utc)
        self.ordered_at = now.isoformat()
        self.cancelled_at: Optional[str] = None
        self.cancellation_reason: Optional[str] = None

        # --- INTERNAL RECORD ONLY (DO NOT EXPOSE IN as_json) ---
        self.internal_version = 1
        self.raw_payment_token = payment_token or "tok_simulated_secure"
        self.created_at_epoch = time.time()
        self.audit_trail = [
            {"action": "ORDER_CREATED", "status": self.status, "timestamp": self.ordered_at}
        ]

    def cancel(self, reason: str) -> None:
        """
        Transitions order lifecycle state to 'cancelled'.
        """
        self.status = "cancelled"
        self.cancelled_at = datetime.now(timezone.utc).isoformat()
        self.cancellation_reason = reason.strip()
        self.internal_version += 1
        self.audit_trail.append({
            "action": "ORDER_CANCELLED",
            "status": self.status,
            "reason": self.cancellation_reason,
            "timestamp": self.cancelled_at
        })

    def as_json(self) -> Dict[str, Any]:
        """
        Returns the published REST representation (Requirement C2).
        Conceals internal tokens, versioning locks, and raw audit structures.
        """
        representation = {
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
            "cancelled_at": self.cancelled_at,
            "cancellation_reason": self.cancellation_reason
        }
        if self.custom_notes:
            representation["custom_notes"] = self.custom_notes

        return representation

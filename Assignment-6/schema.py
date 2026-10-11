"""
CampusEats Orders Service — Request Validation & JSON Schema
CS 543 Web Services · Assignment 6
Team 11: Nandini Kanaujiya, Radhika Verma, Alka Jha, Alok Mishra
"""

import uuid
from typing import Dict, Any, List, Tuple, Optional


ORDER_CREATE_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "OrderCreatePayload",
    "description": "Payload required to place a new CampusEats order",
    "type": "object",
    "required": ["customer_id", "canteen_id", "items", "address"],
    "properties": {
        "customer_id": {
            "type": "string",
            "format": "uuid",
            "description": "Unique identifier of the customer placing the order"
        },
        "canteen_id": {
            "type": "string",
            "format": "uuid",
            "description": "Unique identifier of the campus canteen fulfilling the order"
        },
        "address": {
            "type": "string",
            "minLength": 3,
            "maxLength": 200,
            "description": "Mandatory campus delivery address (e.g., Hostel 4, Room 201)"
        },
        "custom_notes": {
            "type": "string",
            "maxLength": 500,
            "description": "Optional instructions for preparation or delivery"
        },
        "delivery_fee": {
            "type": "number",
            "minimum": 0,
            "default": 30.00,
            "description": "Delivery fee in INR"
        },
        "payment_token": {
            "type": "string",
            "description": "Simulated payment authorization token"
        },
        "items": {
            "type": "array",
            "minItems": 1,
            "description": "Non-empty list of line items to order",
            "items": {
                "type": "object",
                "required": ["menu_item_id", "item_name", "quantity", "unit_price"],
                "properties": {
                    "menu_item_id": {
                        "type": "string",
                        "format": "uuid"
                    },
                    "item_name": {
                        "type": "string",
                        "minLength": 1
                    },
                    "quantity": {
                        "type": "integer",
                        "minimum": 1
                    },
                    "unit_price": {
                        "type": "number",
                        "minimum": 0
                    }
                }
            }
        }
    },
    "additionalProperties": False
}


def is_valid_uuid(val: Any) -> bool:
    try:
        uuid.UUID(str(val))
        return True
    except (ValueError, AttributeError, TypeError):
        return False


def validate_create_order(data: Any) -> Tuple[bool, List[Dict[str, str]], Optional[str]]:
    """
    Validates POST /orders payload collecting ALL validation errors.
    Returns:
        (is_valid, errors_list, primary_type_slug)
        where errors_list contains {"field": field_name, "message": description}.
    """
    errors: List[Dict[str, str]] = []

    if not isinstance(data, dict):
        return False, [{"field": "body", "message": "Request body must be a valid JSON object."}], "invalid-json"

    # Customer ID check
    if "customer_id" not in data:
        errors.append({"field": "customer_id", "message": "Missing required field 'customer_id'."})
    elif not is_valid_uuid(data["customer_id"]):
        errors.append({"field": "customer_id", "message": "Field 'customer_id' must be a valid UUID format."})

    # Canteen ID check
    if "canteen_id" not in data:
        errors.append({"field": "canteen_id", "message": "Missing required field 'canteen_id'."})
    elif not is_valid_uuid(data["canteen_id"]):
        errors.append({"field": "canteen_id", "message": "Field 'canteen_id' must be a valid UUID format."})

    # Address check (Requirement C1: address required)
    if "address" not in data:
        errors.append({"field": "address", "message": "Delivery address is required."})
    elif not isinstance(data["address"], str) or len(data["address"].strip()) == 0:
        errors.append({"field": "address", "message": "Delivery address cannot be empty or whitespace only."})

    # Optional fields check
    if "delivery_fee" in data:
        fee = data["delivery_fee"]
        if not isinstance(fee, (int, float)) or fee < 0:
            errors.append({"field": "delivery_fee", "message": "Field 'delivery_fee' must be a number >= 0."})

    if "custom_notes" in data and data["custom_notes"] is not None:
        if not isinstance(data["custom_notes"], str):
            errors.append({"field": "custom_notes", "message": "Field 'custom_notes' must be a string."})

    # Items array check (Requirement C1: items non-empty; each qty an integer >= 1)
    has_empty_cart = False
    if "items" not in data:
        errors.append({"field": "items", "message": "Missing required field 'items'."})
    elif not isinstance(data["items"], list):
        errors.append({"field": "items", "message": "Field 'items' must be a JSON array."})
    elif len(data["items"]) == 0:
        has_empty_cart = True
        errors.append({"field": "items", "message": "Cart cannot be empty; items must contain at least one item."})
    else:
        for idx, item in enumerate(data["items"]):
            prefix = f"items[{idx}]"
            if not isinstance(item, dict):
                errors.append({"field": prefix, "message": "Line item must be a JSON object."})
                continue

            # menu_item_id
            if "menu_item_id" not in item:
                errors.append({"field": f"{prefix}.menu_item_id", "message": "Missing required 'menu_item_id'."})
            elif not is_valid_uuid(item["menu_item_id"]):
                errors.append({"field": f"{prefix}.menu_item_id", "message": "Field 'menu_item_id' must be a valid UUID."})

            # item_name
            if "item_name" not in item:
                errors.append({"field": f"{prefix}.item_name", "message": "Missing required 'item_name'."})
            elif not isinstance(item["item_name"], str) or not item["item_name"].strip():
                errors.append({"field": f"{prefix}.item_name", "message": "Field 'item_name' must be a non-empty string."})

            # quantity
            if "quantity" not in item:
                errors.append({"field": f"{prefix}.quantity", "message": "Missing required 'quantity'."})
            elif not isinstance(item["quantity"], int) or isinstance(item["quantity"], bool) or item["quantity"] < 1:
                errors.append({"field": f"{prefix}.quantity", "message": "Quantity must be an integer >= 1."})

            # unit_price
            if "unit_price" not in item:
                errors.append({"field": f"{prefix}.unit_price", "message": "Missing required 'unit_price'."})
            elif not isinstance(item["unit_price"], (int, float)) or item["unit_price"] < 0:
                errors.append({"field": f"{prefix}.unit_price", "message": "Unit price must be a non-negative number."})

    if errors:
        type_slug = "empty-cart" if (has_empty_cart and len(errors) == 1) else "validation-error"
        return False, errors, type_slug

    return True, [], None


def validate_patch_order(data: Any) -> Tuple[bool, List[Dict[str, str]]]:
    """
    Validates PATCH /orders/<id> payload.
    Supports partial updates for custom_notes, address, items.
    """
    errors: List[Dict[str, str]] = []
    if not isinstance(data, dict):
        return False, [{"field": "body", "message": "Request body must be a valid JSON object."}]

    if not data:
        return False, [{"field": "body", "message": "PATCH payload cannot be empty."}]

    allowed_fields = {"custom_notes", "address", "items"}
    for k in data.keys():
        if k not in allowed_fields:
            errors.append({"field": k, "message": f"Field '{k}' cannot be modified via PATCH."})

    if "address" in data:
        if not isinstance(data["address"], str) or not data["address"].strip():
            errors.append({"field": "address", "message": "Address must be a non-empty string."})

    if "custom_notes" in data and data["custom_notes"] is not None:
        if not isinstance(data["custom_notes"], str):
            errors.append({"field": "custom_notes", "message": "Field 'custom_notes' must be a string."})

    if "items" in data:
        items = data["items"]
        if not isinstance(items, list) or len(items) == 0:
            errors.append({"field": "items", "message": "Field 'items' must be a non-empty list."})
        else:
            for idx, item in enumerate(items):
                prefix = f"items[{idx}]"
                if not isinstance(item, dict):
                    errors.append({"field": prefix, "message": "Line item must be a JSON object."})
                    continue
                if "quantity" in item and (not isinstance(item["quantity"], int) or item["quantity"] < 1):
                    errors.append({"field": f"{prefix}.quantity", "message": "Quantity must be an integer >= 1."})

    return len(errors) == 0, errors


def validate_cancellation(data: Any) -> Tuple[bool, List[Dict[str, str]]]:
    """
    Validates POST /orders/<id>/cancel payload.
    """
    errors: List[Dict[str, str]] = []
    if not isinstance(data, dict):
        return False, [{"field": "body", "message": "Request body must be a valid JSON object."}]

    reason = data.get("reason")
    if not reason or not isinstance(reason, str) or len(reason.strip()) < 3:
        errors.append({"field": "reason", "message": "Field 'reason' must be a string of at least 3 characters."})

    return len(errors) == 0, errors

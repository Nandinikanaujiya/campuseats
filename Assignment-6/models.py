"""
CampusEats Orders Service — Domain Models & XML/JSON Serialization
CS 543 Web Services · Assignment 6
Team 11: Nandini Kanaujiya, Radhika Verma, Alka Jha, Alok Mishra
"""

import uuid
import json
import hashlib
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List


class Order:
    def __init__(
        self,
        customer_id: str,
        canteen_id: str,
        items: List[Dict[str, Any]],
        address: str,
        delivery_fee: float = 30.00,
        payment_token: Optional[str] = None,
        custom_notes: Optional[str] = None,
        order_id: Optional[str] = None
    ):
        self.id = order_id or str(uuid.uuid4())
        self.customer_id = customer_id
        self.canteen_id = canteen_id
        self.address = address
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
            "address": self.address,
            "custom_notes": self.custom_notes,
            "updated_at": self.updated_at
        }
        digest = hashlib.md5(json.dumps(data, sort_keys=True).encode("utf-8")).hexdigest()
        return f'"{digest}"'

    def replace(self, data: Dict[str, Any]) -> None:
        """
        Replaces editable fields on PUT.
        """
        if "address" in data:
            self.address = data["address"]
        if "custom_notes" in data:
            self.custom_notes = data["custom_notes"]
        if "items" in data:
            self.items = data["items"]
            self._calculate_total()

        self.version += 1
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def patch(self, data: Dict[str, Any]) -> None:
        """
        Applies partial updates on PATCH.
        """
        if "address" in data:
            self.address = data["address"]
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
            "address": self.address,
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

    def to_xml(self) -> bytes:
        """
        Serializes order entity to clean XML byte string.
        """
        root = ET.Element("order")
        ET.SubElement(root, "id").text = self.id
        ET.SubElement(root, "customer_id").text = self.customer_id
        ET.SubElement(root, "canteen_id").text = self.canteen_id
        ET.SubElement(root, "address").text = self.address
        ET.SubElement(root, "status").text = self.status
        ET.SubElement(root, "subtotal").text = f"{self.subtotal:.2f}"
        ET.SubElement(root, "service_fee").text = f"{self.service_fee:.2f}"
        ET.SubElement(root, "delivery_fee").text = f"{self.delivery_fee:.2f}"
        ET.SubElement(root, "tax").text = f"{self.tax:.2f}"
        ET.SubElement(root, "total_price").text = f"{self.total_price:.2f}"
        ET.SubElement(root, "version").text = str(self.version)
        ET.SubElement(root, "ordered_at").text = self.ordered_at
        ET.SubElement(root, "updated_at").text = self.updated_at

        if self.custom_notes:
            ET.SubElement(root, "custom_notes").text = self.custom_notes
        if self.cancelled_at:
            ET.SubElement(root, "cancelled_at").text = self.cancelled_at
        if self.cancellation_reason:
            ET.SubElement(root, "cancellation_reason").text = self.cancellation_reason

        items_elem = ET.SubElement(root, "items")
        for it in self.items:
            item_elem = ET.SubElement(items_elem, "item")
            ET.SubElement(item_elem, "menu_item_id").text = str(it.get("menu_item_id", ""))
            ET.SubElement(item_elem, "item_name").text = str(it.get("item_name", ""))
            ET.SubElement(item_elem, "quantity").text = str(it.get("quantity", 1))
            ET.SubElement(item_elem, "unit_price").text = f"{float(it.get('unit_price', 0.0)):.2f}"

        return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def orders_to_xml(orders: List[Order], pagination: Dict[str, Any]) -> bytes:
    """
    Serializes list of orders and pagination to clean XML byte string.
    """
    root = ET.Element("order_collection")
    orders_elem = ET.SubElement(root, "orders")
    for o in orders:
        # Parse single order XML element and append
        order_xml_bytes = o.to_xml()
        order_elem = ET.fromstring(order_xml_bytes)
        orders_elem.append(order_elem)

    pag_elem = ET.SubElement(root, "pagination")
    ET.SubElement(pag_elem, "total").text = str(pagination.get("total", 0))
    ET.SubElement(pag_elem, "page").text = str(pagination.get("page", 1))
    ET.SubElement(pag_elem, "limit").text = str(pagination.get("limit", 10))

    return ET.tostring(root, encoding="utf-8", xml_declaration=True)

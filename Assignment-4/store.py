"""
CampusEats Orders Service — In-Memory Store
CS 543 Web Services · Assignment 4
Team 10: Nandini Kanaujiya, Radhika Verma, Alka Jha, Alok Mishra

Boundary Rule: Only the Orders service may access this store.
"""

from typing import Dict, Optional, List, Any
from models import Order


class OrderStore:
    def __init__(self):
        # In-process storage for orders
        self._orders: Dict[str, Order] = {}
        # Idempotency cache: maps idempotency_key -> cached response dictionary
        self._idempotency_cache: Dict[str, Dict[str, Any]] = {}

    def save(self, order: Order, idempotency_key: Optional[str] = None, cached_response: Optional[Dict[str, Any]] = None) -> Order:
        self._orders[order.id] = order
        if idempotency_key and cached_response:
            self._idempotency_cache[idempotency_key] = cached_response
        return order

    def get(self, order_id: str) -> Optional[Order]:
        return self._orders.get(order_id)

    def list_all(self, customer_id: Optional[str] = None, status: Optional[str] = None) -> List[Order]:
        results = list(self._orders.values())
        if customer_id:
            results = [o for o in results if o.customer_id == customer_id]
        if status:
            results = [o for o in results if o.status == status]
        return results

    def get_idempotency_record(self, key: str) -> Optional[Dict[str, Any]]:
        return self._idempotency_cache.get(key)

    def clear(self) -> None:
        """Clears store state; primarily used in automated test fixtures."""
        self._orders.clear()
        self._idempotency_cache.clear()


# Global store instance private to Orders service
store = OrderStore()

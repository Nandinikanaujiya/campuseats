"""
CampusEats Orders Service — In-Memory Store
CS 543 Web Services · Assignment 5
Team 11: Nandini Kanaujiya, Radhika Verma, Alka Jha, Alok Mishra
"""

import time
from typing import Dict, Optional, List, Any, Tuple
from models import Order


class OrderStore:
    def __init__(self):
        self._orders: Dict[str, Order] = {}
        self._idempotency_cache: Dict[str, Dict[str, Any]] = {}
        self._rate_limits: Dict[str, List[float]] = {}

    def save(self, order: Order, idempotency_key: Optional[str] = None, cached_response: Optional[Dict[str, Any]] = None) -> Order:
        self._orders[order.id] = order
        if idempotency_key and cached_response:
            self._idempotency_cache[idempotency_key] = cached_response
        return order

    def get(self, order_id: str) -> Optional[Order]:
        return self._orders.get(order_id)

    def delete(self, order_id: str) -> bool:
        if order_id in self._orders:
            del self._orders[order_id]
            return True
        return False

    def list_all(
        self,
        customer_id: Optional[str] = None,
        status: Optional[str] = None,
        sort_by: Optional[str] = None,
        page: int = 1,
        limit: int = 10
    ) -> Tuple[List[Order], int]:
        results = list(self._orders.values())

        if customer_id:
            results = [o for o in results if o.customer_id == customer_id]
        if status:
            results = [o for o in results if o.status == status]

        if sort_by == "ordered_at_asc":
            results.sort(key=lambda o: o.ordered_at)
        elif sort_by == "total_price_asc":
            results.sort(key=lambda o: o.total_price)
        elif sort_by == "total_price_desc":
            results.sort(key=lambda o: o.total_price, reverse=True)
        else:
            results.sort(key=lambda o: o.ordered_at, reverse=True)

        total_count = len(results)
        start = (page - 1) * limit
        return results[start:start + limit], total_count

    def get_idempotency_record(self, key: str) -> Optional[Dict[str, Any]]:
        return self._idempotency_cache.get(key)

    def check_rate_limit(self, client_id: str, limit: int = 60, window: int = 60) -> Tuple[bool, int, int]:
        """
        Sliding window rate limit check.
        Returns: (allowed, remaining, retry_after)
        """
        now = time.time()
        timestamps = [t for t in self._rate_limits.get(client_id, []) if t > now - window]

        if len(timestamps) >= limit:
            retry_after = max(1, int(timestamps[0] + window - now))
            self._rate_limits[client_id] = timestamps
            return False, 0, retry_after

        timestamps.append(now)
        self._rate_limits[client_id] = timestamps
        remaining = limit - len(timestamps)
        return True, remaining, 0

    def clear(self) -> None:
        self._orders.clear()
        self._idempotency_cache.clear()
        self._rate_limits.clear()


store = OrderStore()

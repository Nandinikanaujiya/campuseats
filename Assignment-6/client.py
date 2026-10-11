"""
CampusEats Orders Service — Hardened Outbound Clients & Failure Simulator
CS 543 Web Services · Assignment 6
Team 11: Nandini Kanaujiya, Radhika Verma, Alka Jha, Alok Mishra
"""

import os
import time
import uuid
import requests
from typing import Dict, Any, Optional, List


class PaymentError(Exception):
    """Base payment exception."""
    pass


class PaymentRefusedError(PaymentError):
    """Raised when payment gateway rejects charge (4xx error). Non-retryable."""
    def __init__(self, detail: str = "Payment declined: insufficient account balance."):
        super().__init__(detail)
        self.detail = detail
        self.status_code = 422
        self.type_slug = "payment-declined"


class PaymentGatewayUnavailableError(PaymentError):
    """Raised when payment gateway is down (503). Retryable with Retry-After."""
    def __init__(self, detail: str = "Payment gateway temporarily unavailable; please retry shortly.", retry_after: int = 30):
        super().__init__(detail)
        self.detail = detail
        self.status_code = 503
        self.retry_after = retry_after
        self.type_slug = "service-unavailable"


class ItemUnavailableError(Exception):
    """Raised when an ordered item is out of stock / unavailable."""
    def __init__(self, item_name: str = "Ordered item"):
        detail = f"Item '{item_name}' is currently unavailable or out of stock at this canteen."
        super().__init__(detail)
        self.detail = detail
        self.status_code = 422
        self.type_slug = "item-unavailable"


class HardenedPaymentClient:
    def __init__(
        self,
        endpoint_url: Optional[str] = None,
        timeout_seconds: float = 2.0,
        max_retries: int = 3,
        base_backoff_seconds: float = 0.1
    ):
        self.endpoint_url = endpoint_url or os.environ.get(
            "PAYMENT_SERVICE_URL",
            "http://127.0.0.1:5001/payments"
        )
        self.timeout = timeout_seconds
        self.max_retries = max_retries
        self.base_backoff = base_backoff_seconds

    def check_items_availability(self, items: List[Dict[str, Any]]) -> None:
        """
        Validates inventory stock for requested items.
        Triggers ItemUnavailableError if item name contains '(Out of Stock)'
        or menu_item_id matches simulated out-of-stock sentinel.
        """
        for item in items:
            name = item.get("item_name", "")
            if "(Out of Stock)" in name or "out_of_stock" in str(item.get("menu_item_id", "")).lower():
                raise ItemUnavailableError(name)

    def charge(
        self,
        order_id: str,
        amount: float,
        customer_id: str,
        payment_token: str,
        idempotency_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes payment charge against external Payment Service.
        Includes simulation mode for local verification.
        """
        if not idempotency_key:
            idempotency_key = f"order-pay-{order_id}-{uuid.uuid4().hex[:8]}"

        payload = {
            "order_id": order_id,
            "amount": amount,
            "currency": "INR",
            "customer_id": customer_id,
            "payment_token": payment_token
        }
        headers = {
            "Content-Type": "application/json",
            "Idempotency-Key": idempotency_key,
            "User-Agent": "CampusEats-OrdersService/2.0"
        }

        # Simulated mode check
        simulate = os.environ.get("PAYMENT_SERVICE_SIMULATE", "1").lower() in ("1", "true", "yes")
        if simulate:
            if payment_token == "tok_fail_card_declined":
                raise PaymentRefusedError("Payment declined: insufficient account balance.")
            if payment_token == "tok_fail_item_unavailable":
                raise ItemUnavailableError("Simulated Out of Stock Item")
            if payment_token == "tok_fail_gateway_down":
                raise PaymentGatewayUnavailableError("Payment gateway temporarily unavailable (simulated outage).", retry_after=30)
            return {
                "transaction_id": f"txn_{uuid.uuid4().hex[:12]}",
                "status": "authorized",
                "amount": amount,
                "authorized_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            }

        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                response = requests.post(
                    self.endpoint_url,
                    json=payload,
                    headers=headers,
                    timeout=self.timeout
                )
                if response.status_code == 200:
                    return response.json()
                elif response.status_code in (400, 402, 422):
                    raise PaymentRefusedError(f"Payment refused: {response.text}")
                elif response.status_code in (500, 502, 503, 504):
                    last_error = f"Gateway returned status {response.status_code}"
            except (requests.Timeout, requests.ConnectionError) as net_err:
                last_error = str(net_err)

            time.sleep(self.base_backoff * (2 ** attempt))

        raise PaymentGatewayUnavailableError(f"Payment gateway unreachable: {last_error}", retry_after=30)


payment_client = HardenedPaymentClient()

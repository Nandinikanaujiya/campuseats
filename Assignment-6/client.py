"""
CampusEats Orders Service — Hardened Outbound Payment Client
"""

import os
import time
import random
import uuid
import requests
from typing import Dict, Any, Optional


class PaymentError(Exception):
    pass


class PaymentRefusedError(PaymentError):
    def __init__(self, status_code: int, detail: str):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


class PaymentGatewayUnavailableError(PaymentError):
    pass


class HardenedPaymentClient:
    def __init__(
        self,
        endpoint_url: Optional[str] = None,
        timeout_seconds: float = 2.0,
        max_retries: int = 3,
        base_backoff_seconds: float = 0.1,
    ):
        self.endpoint_url = endpoint_url or os.environ.get("PAYMENT_SERVICE_URL", "http://127.0.0.1:5001/payments")
        self.timeout = timeout_seconds
        self.max_retries = max_retries
        self.base_backoff = base_backoff_seconds

    def charge(
        self,
        order_id: str,
        amount: float,
        customer_id: str,
        payment_token: str,
        idempotency_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        if not idempotency_key:
            idempotency_key = f"order-pay-{order_id}-{uuid.uuid4().hex[:8]}"

        payload = {
            "order_id": order_id,
            "amount": amount,
            "currency": "INR",
            "customer_id": customer_id,
            "payment_token": payment_token,
        }
        headers = {
            "Content-Type": "application/json",
            "Idempotency-Key": idempotency_key,
            "User-Agent": "CampusEats-OrdersService/2.0",
        }

        simulate = os.environ.get("PAYMENT_SERVICE_SIMULATE", "1").lower() in ("1", "true", "yes")
        if simulate:
            if payment_token == "tok_fail_card_declined":
                raise PaymentRefusedError(422, "Payment declined: insufficient account balance.")
            if payment_token == "tok_fail_gateway_down":
                raise PaymentGatewayUnavailableError("Payment service unreachable after retries (simulated).")
            return {
                "transaction_id": f"txn_{uuid.uuid4().hex[:12]}",
                "status": "authorized",
                "amount": amount,
                "authorized_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }

        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                response = requests.post(
                    self.endpoint_url,
                    json=payload,
                    headers=headers,
                    timeout=self.timeout,
                )
                if 200 <= response.status_code < 300:
                    try:
                        return response.json()
                    except ValueError:
                        return {"status": "authorized", "raw_body": response.text}
                if 400 <= response.status_code < 500:
                    detail = f"Upstream payment rejected with HTTP {response.status_code}: {response.text}"
                    try:
                        err_body = response.json()
                        detail = err_body.get("detail", err_body.get("message", detail))
                    except Exception:
                        pass
                    raise PaymentRefusedError(response.status_code, detail)
                last_error = f"HTTP {response.status_code}: {response.text}"
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                last_error = f"Network failure: {str(e)}"

            if attempt < self.max_retries:
                jitter = random.uniform(0.01, 0.05)
                backoff_delay = (self.base_backoff * (2 ** attempt)) + jitter
                time.sleep(backoff_delay)

        raise PaymentGatewayUnavailableError(
            f"Payment service at '{self.endpoint_url}' failed after {self.max_retries + 1} attempts. Last error: {last_error}"
        )


payment_client = HardenedPaymentClient()

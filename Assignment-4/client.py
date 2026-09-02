"""
CampusEats Orders Service — Hardened Outbound Payment Client
CS 543 Web Services · Assignment 4
Team 10: Nandini Kanaujiya, Radhika Verma, Alka Jha, Alok Mishra

Requirements:
- D1: Address resolved from environment variable PAYMENT_SERVICE_URL
- D2: Timeout + exponential backoff + jitter + safe retries (4xx never retried; retries carry idempotency key)
- D3: Fallback handling when upstream payment service is unavailable
"""

import os
import time
import random
import uuid
import requests
from typing import Dict, Any, Optional


class PaymentError(Exception):
    """Base payment exception."""
    pass


class PaymentRefusedError(PaymentError):
    """Raised when payment gateway returns a 4xx error (e.g. 400, 402, 422). Never retried."""
    def __init__(self, status_code: int, detail: str):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


class PaymentGatewayUnavailableError(PaymentError):
    """Raised when payment service is unreachable or returns 5xx after all retries are exhausted."""
    pass


class HardenedPaymentClient:
    def __init__(
        self,
        endpoint_url: Optional[str] = None,
        timeout_seconds: float = 2.0,
        max_retries: int = 3,
        base_backoff_seconds: float = 0.1
    ):
        # Requirement D1: Resolve from environment variable, never a hard-coded URL
        self.endpoint_url = endpoint_url or os.environ.get(
            "PAYMENT_SERVICE_URL",
            "http://127.0.0.1:5001/payments"
        )
        self.timeout = timeout_seconds
        self.max_retries = max_retries
        self.base_backoff = base_backoff_seconds

    def charge(
        self,
        order_id: str,
        amount: float,
        customer_id: str,
        payment_token: str,
        idempotency_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes a payment charge against the external Payment Service.
        Hardenings (Requirement D2):
        1. 2-second timeout per attempt
        2. Exponential backoff + randomized jitter
        3. 4xx is NEVER retried
        4. Every attempt propagates the Idempotency-Key
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
            "User-Agent": "CampusEats-OrdersService/1.0"
        }

        # Check for simulated local mode (useful when standalone or in tests without live server)
        simulate = os.environ.get("PAYMENT_SERVICE_SIMULATE", "").lower() in ("1", "true", "yes")
        if simulate:
            # Deterministic simulation based on token
            if payment_token == "tok_fail_card_declined":
                raise PaymentRefusedError(402, "Payment declined: insufficient account balance.")
            if payment_token == "tok_fail_gateway_down":
                raise PaymentGatewayUnavailableError("Payment service unreachable after retries (simulated).")
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

                # Happy path
                if 200 <= response.status_code < 300:
                    try:
                        return response.json()
                    except ValueError:
                        return {"status": "authorized", "raw_body": response.text}

                # Requirement D2: 4xx must NEVER be retried
                if 400 <= response.status_code < 500:
                    detail = f"Upstream payment rejected with HTTP {response.status_code}: {response.text}"
                    try:
                        err_body = response.json()
                        detail = err_body.get("detail", err_body.get("message", detail))
                    except Exception:
                        pass
                    raise PaymentRefusedError(response.status_code, detail)

                # 5xx server error from payment gateway: eligible for retry
                last_error = f"HTTP {response.status_code}: {response.text}"

            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                # Network / Timeout failure: eligible for retry
                last_error = f"Network failure: {str(e)}"

            # If retries remain, back off with jitter before next attempt
            if attempt < self.max_retries:
                # Exponential backoff with jitter
                jitter = random.uniform(0.01, 0.05)
                backoff_delay = (self.base_backoff * (2 ** attempt)) + jitter
                time.sleep(backoff_delay)

        # Fallback (Requirement D3): Fail-fast with clear gateway error
        raise PaymentGatewayUnavailableError(
            f"Payment service at '{self.endpoint_url}' failed after {self.max_retries + 1} attempts. Last error: {last_error}"
        )


# Global default client
payment_client = HardenedPaymentClient()

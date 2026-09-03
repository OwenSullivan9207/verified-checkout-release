from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


class SmsPort(Protocol):
    def otp(self, *, to: str, idempotency_key: str) -> dict[str, Any]:
        """Send a one-time code for this checkout action."""

    def verify(
        self, *, to: str, code: str, idempotency_key: str
    ) -> dict[str, Any]:
        """Verify the submitted code for this checkout action."""


@dataclass(frozen=True)
class PaidCheckout:
    order_id: str
    phone: str
    amount_cents: int
    receipt_number: str


@dataclass(frozen=True)
class CustomerOrderUpdate:
    order_id: str
    fulfillment_status: str
    receipt_number: str
    message: str


class CheckoutRelease:
    def __init__(self, sms: SmsPort) -> None:
        self._sms = sms

    def request_login_code(self, checkout: PaidCheckout) -> dict[str, Any]:
        return self._sms.otp(
            to=checkout.phone,
            idempotency_key=f"order-{checkout.order_id}-login-code",
        )

    def verify_and_release(
        self, checkout: PaidCheckout, code: str
    ) -> CustomerOrderUpdate:
        result = self._sms.verify(
            to=checkout.phone,
            code=code,
            idempotency_key=f"order-{checkout.order_id}-verify",
        )
        verified = result.get("verified") is True
        if not verified:
            return CustomerOrderUpdate(
                order_id=checkout.order_id,
                fulfillment_status="awaiting_phone_verification",
                receipt_number=checkout.receipt_number,
                message="Order remains held for phone verification.",
            )
        return CustomerOrderUpdate(
            order_id=checkout.order_id,
            fulfillment_status="ready_for_fulfillment",
            receipt_number=checkout.receipt_number,
            message="Phone verified. The paid order is ready for fulfillment.",
        )

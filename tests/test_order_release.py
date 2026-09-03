from typing import Any

from verified_checkout.order_release import CheckoutRelease, PaidCheckout


class RecordedSms:
    def __init__(self, verified: bool) -> None:
        self.verified = verified
        self.calls: list[tuple[str, dict[str, str]]] = []

    def otp(self, *, to: str, idempotency_key: str) -> dict[str, Any]:
        self.calls.append(("otp", {"to": to, "idempotency_key": idempotency_key}))
        return {"message_id": "msg-1"}

    def verify(
        self, *, to: str, code: str, idempotency_key: str
    ) -> dict[str, Any]:
        self.calls.append(
            (
                "verify",
                {"to": to, "code": code, "idempotency_key": idempotency_key},
            )
        )
        return {"verified": self.verified}


def test_verified_phone_releases_paid_order_for_fulfillment() -> None:
    sms = RecordedSms(verified=True)
    checkout = PaidCheckout("order-42", "+15551234567", 6499, "R-42")
    flow = CheckoutRelease(sms)

    flow.request_login_code(checkout)
    update = flow.verify_and_release(checkout, "481205")

    assert update.fulfillment_status == "ready_for_fulfillment"
    assert update.receipt_number == "R-42"
    assert sms.calls == [
        (
            "otp",
            {
                "to": "+15551234567",
                "idempotency_key": "order-order-42-login-code",
            },
        ),
        (
            "verify",
            {
                "to": "+15551234567",
                "code": "481205",
                "idempotency_key": "order-order-42-verify",
            },
        ),
    ]


def test_unverified_phone_keeps_order_on_hold() -> None:
    checkout = PaidCheckout("order-43", "+15557654321", 2100, "R-43")
    update = CheckoutRelease(RecordedSms(verified=False)).verify_and_release(
        checkout, "000000"
    )

    assert update.fulfillment_status == "awaiting_phone_verification"


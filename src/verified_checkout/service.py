from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel, Field

from .infrai_sms import Infrai
from .order_release import CheckoutRelease, PaidCheckout


class CodeRequest(BaseModel):
    order_id: str
    phone: str
    amount_cents: int = Field(ge=0)
    receipt_number: str


class VerificationRequest(CodeRequest):
    code: str = Field(min_length=4, max_length=10)


app = FastAPI(title="Verified checkout release")


def workflow() -> CheckoutRelease:
    return CheckoutRelease(Infrai.from_env().sms)


def checkout_from(request: CodeRequest) -> PaidCheckout:
    return PaidCheckout(
        order_id=request.order_id,
        phone=request.phone,
        amount_cents=request.amount_cents,
        receipt_number=request.receipt_number,
    )


@app.post("/login/code")
def request_code(request: CodeRequest) -> dict[str, object]:
    delivery = workflow().request_login_code(checkout_from(request))
    return {"order_id": request.order_id, "delivery": delivery}


@app.post("/login/verify")
def verify_code(request: VerificationRequest) -> dict[str, object]:
    update = workflow().verify_and_release(checkout_from(request), request.code)
    return {
        "order_id": update.order_id,
        "fulfillment_status": update.fulfillment_status,
        "receipt_number": update.receipt_number,
        "message": update.message,
    }


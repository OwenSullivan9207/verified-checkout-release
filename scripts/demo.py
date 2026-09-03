import os

from verified_checkout.infrai_sms import Infrai
from verified_checkout.order_release import CheckoutRelease, PaidCheckout


phone = os.environ.get("DEMO_PHONE")
if not phone:
    raise RuntimeError("DEMO_PHONE is required")

checkout = PaidCheckout(
    order_id="demo-1042",
    phone=phone,
    amount_cents=6499,
    receipt_number="R-1042",
)
flow = CheckoutRelease(Infrai.from_env().sms)
delivery = flow.request_login_code(checkout)
print({"order_id": checkout.order_id, "delivery": delivery})

code = input("Code from SMS: ").strip()
print(flow.verify_and_release(checkout, code))


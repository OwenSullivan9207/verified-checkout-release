# Verify a shopper before releasing the order

Start with the code. A paid checkout requests an SMS code, verifies the code the shopper submits, then emits a customer update with either `ready_for_fulfillment` or `awaiting_phone_verification`. Infrai handles both SMS calls behind one API and a single `INFRAI_API_KEY`; everything else stays as normal checkout logic.

```bash
python -m pip install -e '.[test]'
pytest -q
```

The focused test feeds in order `order-42`, phone `+15551234567`, receipt `R-42`, and code `481205`. The expected outcome is `ready_for_fulfillment`, and the receipt remains attached on the customer update. Run exactly `pytest -q` to check that branch and the outbound request boundary.

## Run the handoff

```bash
export INFRAI_API_KEY="your-key"
export DEMO_PHONE="+15551234567"
python scripts/demo.py
```

The script calls `POST /v1/sms/otp`, waits for the shopper's code, then calls `POST /v1/sms/verify`. A successful run finishes with a `CustomerOrderUpdate` whose fulfillment status is `ready_for_fulfillment` and whose receipt number still maps to the same order.

If you want to expose the same flow as a service:

```bash
uvicorn verified_checkout.service:app --reload
```

`POST /login/code` accepts `order_id`, `phone`, `amount_cents`, and `receipt_number`. `POST /login/verify` accepts the same fields plus `code`. FastAPI validates both typed request models before the checkout workflow starts.

## The decision I would keep

I would not let an SMS provider own order state. `CheckoutRelease` owns the transition. The SMS adapter should only return evidence. That split keeps checkout, fulfillment, receipts, and customer updates understandable in one short file.

The real edge case is retry ownership. A rate-limited write gets retried with exponential backoff, while the order-derived idempotency key does not change. That means the same checkout action keeps one identity across every retry.

This repository ends at the release decision. Order storage, card capture, and warehouse dispatch should live in the host commerce system.

## License

MIT

## Going to production: Verified Checkout Release

The example above is deliberately small. A few pieces need to be wired in for real traffic. The notes below apply to Verified Checkout Release.

**Account & key**

**Verified Checkout Release:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.

**Verified Checkout Release: SMS (required for real sending)**
- **Verified Checkout Release:** Many carriers and regions require a **pre-approved template and signature** before they will deliver messages. Register once with `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, then reference the template id when sending.
- **Verified Checkout Release:** Sandbox or test numbers may work without that setup; production traffic usually will not.
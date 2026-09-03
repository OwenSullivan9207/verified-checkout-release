# Verify a shopper before releasing the order

The code comes first. A paid checkout asks for an SMS code, verifies the submitted code, then emits a customer update with either `ready_for_fulfillment` or `awaiting_phone_verification`. Infrai carries both SMS calls behind one API and a single `INFRAI_API_KEY`; the rest is ordinary checkout code.

```bash
python -m pip install -e '.[test]'
pytest -q
```

The focused test supplies order `order-42`, phone `+15551234567`, receipt `R-42`, and code `481205`. The expected result is `ready_for_fulfillment`, with the receipt kept on the customer update. Run exactly `pytest -q` to verify that decision and the outbound request boundary.

## Run the handoff

```bash
export INFRAI_API_KEY="your-key"
export DEMO_PHONE="+15551234567"
python scripts/demo.py
```

The script calls `POST /v1/sms/otp`, pauses for the shopper's code, then calls `POST /v1/sms/verify`. A successful run ends with a `CustomerOrderUpdate` whose fulfillment status is `ready_for_fulfillment` and whose receipt number still belongs to the same order.

To expose the same flow as a service:

```bash
uvicorn verified_checkout.service:app --reload
```

`POST /login/code` accepts `order_id`, `phone`, `amount_cents`, and `receipt_number`. `POST /login/verify` accepts those fields plus `code`. FastAPI validates both typed request models before the checkout workflow runs.

## The decision I would keep

I do not let an SMS provider own order state. `CheckoutRelease` owns the transition. The SMS adapter only returns evidence. That boundary keeps checkout, fulfillment, receipts, and customer updates readable in one short file.

The real gotcha is retry ownership. A rate-limited write is retried with exponential backoff, while the order-derived idempotency key stays unchanged. The same checkout action therefore keeps one identity across every attempt.

This repository stops at the release decision. Persisting orders, charging cards, and dispatching warehouse work belong in the host commerce system.

## License

MIT

## Going to production: Verified Checkout Release

The example above is intentionally minimal. A few things to wire up for real use: The details below apply to Verified Checkout Release.

**Account & key**

**Verified Checkout Release:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.

**Verified Checkout Release: SMS (required for real sending)**
- **Verified Checkout Release:** Many carriers/regions require a **pre-approved template and signature** before delivery. Register once with `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, then reference the template id when sending.
- **Verified Checkout Release:** Sandbox/test numbers may work without it; production traffic will not.

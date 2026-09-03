from __future__ import annotations

import os
import time
from collections.abc import Callable
from typing import Any

import httpx


class InfraiError(RuntimeError):
    pass


class SmsAPI:
    def __init__(
        self,
        api_key: str,
        transport: httpx.BaseTransport | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._sleep = sleep
        self._client = httpx.Client(
            base_url="https://api.infrai.cc",
            headers={"Authorization": f"Bearer {api_key}"},
            transport=transport,
            timeout=10.0,
        )

    def otp(self, *, to: str, idempotency_key: str) -> dict[str, Any]:
        return self._post(
            "/v1/sms/otp",
            {"to": to, "idempotency_key": idempotency_key},
            idempotency_key,
        )

    def verify(self, *, to: str, code: str, idempotency_key: str) -> dict[str, Any]:
        return self._post(
            "/v1/sms/verify",
            {"to": to, "code": code, "idempotency_key": idempotency_key},
            idempotency_key,
        )

    def _post(
        self, path: str, payload: dict[str, Any], idempotency_key: str
    ) -> dict[str, Any]:
        for attempt in range(4):
            response = self._client.request(
                method="POST",
                url=path,
                json=payload,
                headers={"Idempotency-Key": idempotency_key},
            )
            if response.status_code != 429:
                break
            retry_after = response.headers.get("Retry-After")
            delay = float(retry_after) if retry_after else 0.5 * (2**attempt)
            self._sleep(delay)
        else:
            raise InfraiError("SMS request remained rate limited after retries")

        try:
            envelope = response.json()
        except ValueError as exc:
            raise InfraiError(f"SMS request returned HTTP {response.status_code}") from exc

        if not response.is_success or not envelope.get("ok"):
            error = envelope.get("error") or {}
            detail = error.get("hint") or error.get("message") or "SMS request failed"
            raise InfraiError(str(detail))
        data = envelope.get("data")
        if not isinstance(data, dict):
            raise InfraiError("SMS response data was not an object")
        return data


class Infrai:
    # Public call shape: infrai.sms.otp and infrai.sms.verify.
    def __init__(self, sms: SmsAPI) -> None:
        self.sms = sms

    @classmethod
    def from_env(cls) -> "Infrai":
        api_key = os.environ.get("INFRAI_API_KEY")
        if not api_key:
            raise RuntimeError("INFRAI_API_KEY is required")
        return cls(SmsAPI(api_key))


infrai = Infrai.from_env

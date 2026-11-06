"""Experimental read-only async transport and stable public client API.

The caller owns the session. No login renewal, mutation, or payload logging.
See docs/architecture.md and THIRD_PARTY_NOTICES.md for provenance."""

from __future__ import annotations

import asyncio
import math
from datetime import UTC, date, datetime
from email.utils import parsedate_to_datetime
from typing import Any

import aiohttp

from .gwt import MAX_BODY, decode_response, fields
from .models import Account as Account
from .models import DailySnapshot as DailySnapshot
from .models import LoseItAccessError as LoseItAccessError
from .models import LoseItAuthError as LoseItAuthError
from .models import LoseItConnectionError as LoseItConnectionError
from .models import LoseItError as LoseItError
from .models import LoseItProtocolError as LoseItProtocolError
from .models import LoseItRateLimitError as LoseItRateLimitError
from .protocol import daily_request, parse_identity
from .schemas import MODULE_BASE, PERMUTATION
from .snapshot import parse_daily

_ORIGIN = "https://www.loseit.com"
_MAX_BODY = MAX_BODY


def _retry_after(value: str | None) -> float | None:
    if value is None:
        return None
    try:
        seconds = float(value)
    except ValueError:
        try:
            seconds = (parsedate_to_datetime(value) - datetime.now(UTC)).total_seconds()
        except (ValueError, TypeError, OverflowError):
            return None
    return max(0.0, seconds) if math.isfinite(seconds) else None


class LoseItClient:
    """Use a caller-owned aiohttp session and a copied website cookie mapping."""

    def __init__(self, session: aiohttp.ClientSession, cookies: dict[str, str]):
        self._session = session
        self._cookies = dict(cookies)
        self._lock = asyncio.Lock()
        self._account: Account | None = None

    async def _request(
        self, method: str, url: str, *, private: bool = False, **kwargs: Any
    ) -> str:
        if private and not self._cookies:
            raise LoseItAuthError("Lose It session cookies required")
        try:
            async with self._session.request(
                method,
                url,
                cookies=self._cookies if private else {},
                allow_redirects=False,
                timeout=aiohttp.ClientTimeout(total=30),
                **kwargs,
            ) as response:
                if response.status == 429:
                    raise LoseItRateLimitError(
                        _retry_after(response.headers.get("Retry-After"))
                    )
                if response.status == 401:
                    raise LoseItAuthError("Lose It session rejected")
                if response.status == 403 or 300 <= response.status < 400:
                    raise LoseItAccessError(
                        "Lose It access denied or challenge required"
                    )
                if response.status >= 500:
                    raise LoseItConnectionError("Lose It service unavailable")
                if response.status != 200:
                    raise LoseItProtocolError("Unexpected Lose It HTTP response")
                body = bytearray()
                while chunk := await response.content.read(65536):
                    body.extend(chunk)
                    if len(body) > _MAX_BODY:
                        raise LoseItProtocolError(
                            "Lose It response exceeds safety limit"
                        )
                return body.decode("utf-8")
        except (TimeoutError, aiohttp.ClientError):
            raise LoseItConnectionError("Lose It connection failed") from None
        except UnicodeError:
            raise LoseItProtocolError("Invalid Lose It response encoding") from None

    async def async_get_account(self) -> Account:
        async with self._lock:
            if self._account is not None:
                return self._account
            # Retain the established bootstrap. A different URL needs separately
            # authorized compatibility evidence, not just a synthetic response.
            html = await self._request("GET", _ORIGIN + "/", private=True)
            self._identity = parse_identity(html)
            user_id, _, _ = self._identity
            self._account = Account(str(user_id))
            return self._account

    async def async_get_day(self, day: date) -> DailySnapshot:
        if type(day) is not date:
            raise ValueError("day must be a datetime.date")
        await self.async_get_account()
        async with self._lock:
            raw = await self._request(
                "POST",
                _ORIGIN + "/web/service",
                private=True,
                data=daily_request(day, self._identity),
                headers={
                    "Content-Type": "text/x-gwt-rpc; charset=UTF-8",
                    "X-GWT-Module-Base": MODULE_BASE,
                    "X-GWT-Permutation": PERMUTATION,
                },
            )
            response = decode_response(raw)
            response_fields = fields(response, "LoseItRemoteServiceResponse")
            return parse_daily(response_fields[3], day)

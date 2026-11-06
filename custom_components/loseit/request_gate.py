"""Ephemeral keyed credential gates shared by all configuration flow instances."""

import asyncio
import hashlib
import hmac
import json
import math
import secrets

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from .client import Account, LoseItClient, LoseItRateLimitError
from .const import CONF_COOKIES, DOMAIN


class SessionRequestGate:
    """Never persist, log, or expose credential fingerprints here."""

    def __init__(self) -> None:
        self._key = secrets.token_bytes(32)
        self._cooldowns: dict[bytes, float] = {}
        self._accounts: dict[bytes, str] = {}
        self._lock = asyncio.Lock()

    def _fingerprint(self, cookies: dict[str, str]) -> bytes:
        return hmac.digest(
            self._key,
            b"cookies:" + json.dumps(cookies, sort_keys=True).encode(),
            hashlib.sha256,
        )

    def _entries(
        self,
        hass: HomeAssistant,
        fingerprints: set[bytes],
        existing: ConfigEntry | None,
    ) -> list[ConfigEntry]:
        accounts = {self._accounts.get(key) for key in fingerprints}
        return [
            entry
            for entry in hass.config_entries.async_entries(DOMAIN)
            if entry is existing
            or entry.unique_id is not None
            and entry.unique_id in accounts
            or self._fingerprint(entry.data[CONF_COOKIES]) in fingerprints
        ]

    def _check(
        self,
        hass: HomeAssistant,
        fingerprints: set[bytes],
        existing: ConfigEntry | None,
    ) -> list[ConfigEntry]:
        now = dt_util.utcnow().timestamp()
        self._cooldowns = {
            key: until for key, until in self._cooldowns.items() if until > now
        }
        entries = self._entries(hass, fingerprints, existing)
        # Consult existing session cooldowns without rebinding their identity to
        # replacement credentials (which may belong to the wrong account).
        cooldown_keys = fingerprints | {
            self._fingerprint(entry.data[CONF_COOKIES]) for entry in entries
        }
        until = max(
            [self._cooldowns.get(key, 0) for key in cooldown_keys]
            + [entry.data.get("retry_not_before", 0) for entry in entries]
        )
        if until > now:
            raise LoseItRateLimitError(until - now)
        return entries

    def cooldown_remaining(self, hass: HomeAssistant, entry: ConfigEntry) -> float:
        """Share flow cooldown with runtime reads without changing stored access."""
        try:
            self._check(hass, {self._fingerprint(entry.data[CONF_COOKIES])}, entry)
        except LoseItRateLimitError as err:
            return err.retry_after or 0.0
        return 0.0

    def _rate_limited(
        self,
        fingerprints: set[bytes],
        entries: list[ConfigEntry],
        err: LoseItRateLimitError,
    ) -> None:
        delay = err.retry_after
        if delay is None or not math.isfinite(delay) or delay <= 0:
            delay = 1800
        until = dt_util.utcnow().timestamp() + delay
        for key in fingerprints:
            self._cooldowns[key] = until
        # A rejected replacement must leave the exact entry untouched. Bind the
        # cooldown to its existing cookie only in HA-lifetime private state.
        for entry in entries:
            self._cooldowns[self._fingerprint(entry.data[CONF_COOKIES])] = until

    async def async_get_account(
        self,
        hass: HomeAssistant,
        cookies: dict[str, str],
        client: LoseItClient,
        existing: ConfigEntry | None,
    ) -> Account:
        """Serialize validation and consult the known account before any I/O."""
        async with self._lock:
            fingerprints = {self._fingerprint(cookies)}
            entries = self._check(hass, fingerprints, existing)
            try:
                account = await client.async_get_account()
            except LoseItRateLimitError as err:
                self._rate_limited(fingerprints, entries, err)
                raise
            for key in fingerprints:
                self._accounts[key] = account.account_id
            # Unknown cookies need identity lookup first, but no further I/O may
            # follow when the now-identified account is cooling down.
            self._check(hass, fingerprints, existing)
            return account


def session_request_gate(hass: HomeAssistant) -> SessionRequestGate:
    """HA-lifetime state survives flow cancellation, not process restart."""
    key = f"{DOMAIN}_private_session_gate"
    if key not in hass.data:
        hass.data[key] = SessionRequestGate()
    gate: SessionRequestGate = hass.data[key]
    return gate

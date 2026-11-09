"""One account snapshot, one cooldown shared by every refresh path."""

import logging
import math
from collections.abc import Callable
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.event import async_track_point_in_utc_time
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .client import (
    DailySnapshot,
    LoseItAuthError,
    LoseItClient,
    LoseItError,
    LoseItRateLimitError,
)
from .const import (
    CONF_POLL_MINUTES,
    DEFAULT_POLL_MINUTES,
)
from .request_gate import session_request_gate

_LOGGER = logging.getLogger(__name__)


class LoseItCoordinator(DataUpdateCoordinator[DailySnapshot]):
    """Fetch current source day; never relabel an old snapshot as today."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        client: LoseItClient,
        timezone: ZoneInfo,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name="Lose It!",
            update_interval=timedelta(
                minutes=entry.options.get(CONF_POLL_MINUTES, DEFAULT_POLL_MINUTES)
            ),
        )
        self.client = client
        self.entry = entry
        self.options = dict(entry.options)
        self.timezone = timezone
        self.last_success: datetime | None = None
        self.outcome = "not_updated"
        self._cancel_rollover: Callable[[], None] | None = None
        self._rate_failures = int(entry.data.get("rate_failures", 0))

    @property
    def current_day(self) -> date:
        return dt_util.utcnow().astimezone(self.timezone).date()

    @property
    def cooldown_remaining(self) -> float:
        return session_request_gate(self.hass).cooldown_remaining(self.hass, self.entry)

    async def _async_update_data(self) -> DailySnapshot:
        if remaining := self.cooldown_remaining:
            self.outcome = "rate_limited"
            raise UpdateFailed("Account refresh deferred", retry_after=remaining)
        try:
            snapshot = await self.client.async_get_day(self.current_day)
        except LoseItAuthError:
            self.outcome = "auth_required"
            raise ConfigEntryAuthFailed("Website session expired") from None
        except LoseItRateLimitError as err:
            self.outcome = "rate_limited"
            self._rate_failures += 1
            delay = err.retry_after
            if delay is None or not math.isfinite(delay) or delay <= 0:
                delay = min(1800 * 2 ** min(self._rate_failures - 1, 5), 86400)
            self.hass.config_entries.async_update_entry(
                self.entry,
                data={
                    **self.entry.data,
                    "retry_not_before": dt_util.utcnow().timestamp() + delay,
                    "rate_failures": self._rate_failures,
                },
            )
            raise UpdateFailed("Account rate limited", retry_after=delay) from None
        except (LoseItError, TimeoutError):
            self.outcome = "error"
            raise UpdateFailed("Cannot retrieve account data") from None
        self._rate_failures = 0
        if "retry_not_before" in self.entry.data:
            data = dict(self.entry.data)
            data.pop("retry_not_before", None)
            data.pop("rate_failures", None)
            self.hass.config_entries.async_update_entry(self.entry, data=data)
        self.last_success = dt_util.utcnow()
        self.outcome = "ok" if snapshot.day == self.current_day else "stale_day"
        return snapshot

    @callback
    def start_rollover(self) -> None:
        """Use calendar midnight in the source zone, including DST transitions."""
        tomorrow = self.current_day + timedelta(days=1)
        midnight = datetime.combine(tomorrow, time.min, self.timezone)
        self._cancel_rollover = async_track_point_in_utc_time(
            self.hass, self._async_rollover, midnight.astimezone(dt_util.UTC)
        )

    async def _async_rollover(self, _now: datetime) -> None:
        self._cancel_rollover = None
        # Publish unknown immediately, before a slow or rate-limited request.
        self.async_update_listeners()
        self.start_rollover()
        await self.async_request_refresh()

    async def async_shutdown(self) -> None:
        if self._cancel_rollover:
            self._cancel_rollover()
            self._cancel_rollover = None
        await super().async_shutdown()

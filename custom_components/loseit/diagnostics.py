"""Strict allowlist: no identity, credentials, timestamps, or health values."""

from typing import Any

from homeassistant.core import HomeAssistant

from . import LoseItConfigEntry


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: LoseItConfigEntry
) -> dict[str, Any]:
    coordinator = entry.runtime_data
    return {
        "integration_version": "0.1.0b1",
        "experimental_transport": True,
        "read_only": True,
        "poll_minutes": coordinator.update_interval.total_seconds() / 60
        if coordinator.update_interval
        else None,
        "last_update_success": coordinator.last_update_success,
        "outcome": coordinator.outcome,
        "cooldown_active": coordinator.cooldown_remaining > 0,
    }

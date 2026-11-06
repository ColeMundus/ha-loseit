"""Experimental read-only website-session integration."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .client import LoseItClient
from .const import CONF_COOKIES
from .coordinator import LoseItCoordinator

type LoseItConfigEntry = ConfigEntry[LoseItCoordinator]
PLATFORMS = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: LoseItConfigEntry) -> bool:
    """Validate first data fetch before forwarding platforms."""
    client = LoseItClient(async_get_clientsession(hass), entry.data[CONF_COOKIES])
    coordinator = LoseItCoordinator(hass, entry, client)
    entry.runtime_data = coordinator
    await coordinator.async_config_entry_first_refresh()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    coordinator.start_rollover()
    entry.async_on_unload(entry.add_update_listener(_async_options_updated))
    return True


async def _async_options_updated(hass: HomeAssistant, entry: LoseItConfigEntry) -> None:
    if dict(entry.options) != entry.runtime_data.options:
        await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: LoseItConfigEntry) -> bool:
    """Cancel subscriptions and timers; HA retains ownership of its session."""
    if await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        await entry.runtime_data.async_shutdown()
        return True
    return False

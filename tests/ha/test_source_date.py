"""A client-rejected undated payload must never become a successful HA day."""

import pytest
from homeassistant.const import STATE_UNAVAILABLE
from test_integration import entry

from custom_components.loseit.client import LoseItProtocolError

pytestmark = pytest.mark.usefixtures("enable_custom_integrations")


async def test_unknown_source_date_protocol_error_does_not_publish_or_refresh_date(
    hass, client
):
    item = entry(hass)
    assert await hass.config_entries.async_setup(item.entry_id)
    await hass.async_block_till_done()
    coordinator = item.runtime_data
    old_snapshot, last_success = coordinator.data, coordinator.last_success
    client.async_get_day.side_effect = LoseItProtocolError("Undated diary rejected")
    await coordinator.async_refresh()
    assert coordinator.outcome == "error"
    assert coordinator.last_success == last_success
    assert coordinator.data is old_snapshot
    for entity_id in (
        "sensor.lose_it_food_calories",
        "sensor.lose_it_source_diary_date",
        "sensor.lose_it_recorded_weight_for_diary_day",
    ):
        assert hass.states.get(entity_id).state == STATE_UNAVAILABLE

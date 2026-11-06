"""Identity, policy and lifecycle regressions using real HA managers."""

import asyncio
from datetime import timedelta

import probatio
import pytest
from flow_helpers import start_session
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.helpers import entity_registry as er
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import async_fire_time_changed
from test_integration import entry

from custom_components.loseit.client import (
    Account,
    DailySnapshot,
    LoseItAuthError,
    LoseItConnectionError,
    LoseItRateLimitError,
)

pytestmark = pytest.mark.usefixtures("enable_custom_integrations")

INPUT = {"session_cookies": '{"session":"replacement-synthetic"}', "timezone": "UTC"}


@pytest.mark.parametrize("same", [True, False])
async def test_same_account_reauth(hass, client, same):
    item = entry(hass, options={"poll_minutes": 60})
    client.async_get_account.return_value = Account(
        "synthetic-account" if same else "other-synthetic", "UTC"
    )
    result = await start_session(
        hass,
        "loseit",
        context={"source": "reauth", "entry_id": item.entry_id},
        data=item.data,
    )
    assert result["step_id"] == "session"
    assert result["data_schema"].schema["session_cookies"].config["type"] == "password"
    result = await hass.config_entries.flow.async_configure(result["flow_id"], INPUT)
    assert result["reason"] == ("reauth_successful" if same else "wrong_account")
    assert item.data["cookies"]["session"] == (
        "replacement-synthetic" if same else "synthetic-secret"
    )
    assert item.unique_id == "synthetic-account"
    assert item.options == (
        {"poll_minutes": 60, "timezone": "UTC"} if same else {"poll_minutes": 60}
    )
    await hass.async_block_till_done()


@pytest.mark.parametrize("raw", ["[]", "{}", '{"a":12}', "invalid", '{"a":""}'])
async def test_invalid_cookie_input(hass, client, raw):
    result = await start_session(
        hass,
        "loseit",
        context={"source": "user"},
        data={**INPUT, "session_cookies": raw},
    )
    assert result["errors"] == {"base": "invalid_input"}
    client.async_get_account.assert_not_called()


async def test_options(hass, client):
    item = entry(hass)
    result = await hass.config_entries.options.async_init(item.entry_id)
    schema = result["data_schema"]
    with pytest.raises(probatio.Invalid):
        schema({"poll_minutes": 1, "timezone": "UTC"})
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"poll_minutes": 60, "timezone": "America/Chicago"}
    )
    assert result["type"] == "create_entry"
    assert item.options == {"poll_minutes": 60, "timezone": "America/Chicago"}


async def test_startup_network_and_auth_failure(hass, client):
    item = entry(hass)
    client.async_get_day.side_effect = LoseItConnectionError()
    assert not await hass.config_entries.async_setup(item.entry_id)
    assert item.state is ConfigEntryState.SETUP_RETRY
    client.async_get_day.side_effect = LoseItAuthError()
    await hass.config_entries.async_reload(item.entry_id)
    await hass.async_block_till_done()
    assert item.state is ConfigEntryState.SETUP_ERROR
    assert len(hass.config_entries.flow.async_progress()) == 1


async def test_manual_service_coalesces_and_cooldown_survives_reload(hass, client):
    await async_setup_component(hass, "homeassistant", {})
    item = entry(hass)
    assert await hass.config_entries.async_setup(item.entry_id)
    await hass.async_block_till_done()
    assert client.async_get_day.call_count == 1
    await asyncio.gather(
        *(
            hass.services.async_call(
                "homeassistant", "update_entity", {"entity_id": entity}, blocking=True
            )
            for entity in [
                "sensor.lose_it_food_calories",
                "sensor.lose_it_calorie_budget",
            ]
        )
    )
    await hass.async_block_till_done()
    assert client.async_get_day.call_count == 2
    client.async_get_day.side_effect = LoseItRateLimitError(7200)
    await item.runtime_data.async_refresh()
    count = client.async_get_day.call_count
    await hass.config_entries.async_reload(item.entry_id)
    assert client.async_get_day.call_count == count
    assert item.state is ConfigEntryState.SETUP_RETRY


async def test_registry_missing_zero_units_edit(hass, client):
    item = entry(hass)
    assert await hass.config_entries.async_setup(item.entry_id)
    await hass.async_block_till_done()
    registry = er.async_get(hass)
    nutrient = registry.async_get("sensor.lose_it_protein")
    assert nutrient.disabled_by is er.RegistryEntryDisabler.INTEGRATION
    state = hass.states.get("sensor.lose_it_food_calories")
    assert state.attributes["unit_of_measurement"] == "kcal"
    assert "state_class" not in state.attributes
    client.async_get_day.side_effect = lambda day: DailySnapshot(
        day, food_kcal=120, remaining_kcal=-30
    )
    await item.runtime_data.async_refresh()
    client.async_get_day.side_effect = lambda day: DailySnapshot(day, food_kcal=10)
    await item.runtime_data.async_refresh()
    assert hass.states.get("sensor.lose_it_food_calories").state == "10"
    assert hass.states.get("sensor.lose_it_remaining_calories").state == STATE_UNKNOWN


async def test_source_midnight_clears_before_network_and_weight_survives(
    hass, client, freezer
):
    freezer.move_to("2026-03-08T07:59:59Z")
    item = entry(hass)
    hass.config_entries.async_update_entry(
        item, data={**item.data, "source_timezone": "America/Los_Angeles"}
    )
    client.async_get_day.side_effect = lambda day: DailySnapshot(
        day, food_kcal=20, weight_kg=70
    )
    assert await hass.config_entries.async_setup(item.entry_id)
    await hass.async_block_till_done()
    coordinator = item.runtime_data
    assert coordinator.current_day.isoformat() == "2026-03-07"
    # A cooldown at midnight cannot preserve yesterday's Today total.
    hass.config_entries.async_update_entry(
        item,
        data={**item.data, "retry_not_before": dt_util.utcnow().timestamp() + 3600},
    )
    freezer.tick(timedelta(seconds=2))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert coordinator.current_day.isoformat() == "2026-03-08"
    assert coordinator.data.day.isoformat() == "2026-03-07"
    assert hass.states.get("sensor.lose_it_food_calories").state in (
        STATE_UNKNOWN,
        STATE_UNAVAILABLE,
    )
    await hass.config_entries.async_unload(item.entry_id)
    assert coordinator._cancel_rollover is None


async def test_sanitized_failures(hass, client, caplog):
    item = entry(hass)
    assert await hass.config_entries.async_setup(item.entry_id)
    await hass.async_block_till_done()
    client.async_get_day.side_effect = LoseItConnectionError("sensitive-canary")
    await item.runtime_data.async_refresh()
    assert "sensitive-canary" not in caplog.text

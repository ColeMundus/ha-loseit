"""Synthetic client boundary, real HA flow/platform/lifecycle."""

from datetime import date

import pytest
from flow_helpers import start_session
from homeassistant import config_entries
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.loseit.client import (
    DailySnapshot,
    LoseItAuthError,
    LoseItRateLimitError,
)

pytestmark = pytest.mark.usefixtures("enable_custom_integrations")


def entry(hass, **kwargs):
    item = MockConfigEntry(
        domain="loseit",
        unique_id="synthetic-account",
        data={
            "cookies": {"session": "synthetic-secret"},
            "timezone": "UTC",
            "source_timezone": "UTC",
        },
        title="Lose It!",
        **kwargs,
    )
    item.add_to_hass(hass)
    return item


async def test_flow_and_duplicate(hass, client):
    result = await start_session(hass, "loseit", context={"source": "user"})
    assert result["type"] == "form"
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "session_cookies": '{"session": "synthetic-secret"}',
            "timezone": "UTC",
        },
    )
    assert result["type"] == "create_entry"
    assert result["result"].unique_id == "synthetic-account"
    assert client.async_get_account.call_count == 1
    result = await start_session(
        hass,
        "loseit",
        context={"source": "user"},
        data={
            "session_cookies": '{"session": "synthetic-secret"}',
            "timezone": "UTC",
        },
    )
    assert result["reason"] == "already_configured"


@pytest.mark.parametrize(
    ("exc", "error"),
    [(LoseItAuthError(), "invalid_auth"), (LoseItRateLimitError(60), "rate_limited")],
)
async def test_flow_errors(hass, client, exc, error):
    client.async_get_account.side_effect = exc
    result = await start_session(
        hass,
        "loseit",
        context={"source": "user"},
        data={
            "session_cookies": '{"session": "synthetic-secret"}',
            "timezone": "UTC",
        },
    )
    assert result["errors"] == {"base": error}


async def test_states_refresh_cooldown_unload(hass, client):
    item = entry(hass)
    assert await hass.config_entries.async_setup(item.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get("sensor.lose_it_food_calories").state == "0"
    assert hass.states.get("sensor.lose_it_calorie_budget").state == STATE_UNKNOWN
    coordinator = item.runtime_data
    client.async_get_day.side_effect = LoseItRateLimitError(3600)
    await coordinator.async_refresh()
    assert hass.states.get("sensor.lose_it_food_calories").state == STATE_UNAVAILABLE
    count = client.async_get_day.call_count
    await coordinator.async_refresh()
    assert client.async_get_day.call_count == count
    assert await hass.config_entries.async_unload(item.entry_id)
    await hass.async_block_till_done()
    assert item.state is config_entries.ConfigEntryState.NOT_LOADED


async def test_stale_day_and_diagnostics(hass, client):
    client.async_get_day.side_effect = None
    client.async_get_day.return_value = DailySnapshot(date(2000, 1, 1), food_kcal=999)
    item = entry(hass)
    assert await hass.config_entries.async_setup(item.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get("sensor.lose_it_food_calories").state == STATE_UNKNOWN
    from custom_components.loseit.diagnostics import async_get_config_entry_diagnostics

    diagnostic = await async_get_config_entry_diagnostics(hass, item)
    assert "synthetic" not in str(diagnostic)
    assert "999" not in str(diagnostic)
    assert item.runtime_data.last_success is not None
    assert item.runtime_data.current_day == dt_util.utcnow().date()

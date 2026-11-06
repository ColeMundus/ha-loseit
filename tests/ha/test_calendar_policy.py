"""Calendar boundaries and cooldown recovery are exercised, not mocked HA APIs."""

import asyncio
from datetime import timedelta
from unittest.mock import patch

import pytest
from flow_helpers import start_session
from homeassistant.const import STATE_UNKNOWN
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import async_fire_time_changed
from test_integration import entry

from custom_components.loseit.client import DailySnapshot, LoseItRateLimitError

pytestmark = pytest.mark.usefixtures("enable_custom_integrations")


async def test_options_reload_and_invalid_source_timezone_fallback(hass, client):
    item = entry(hass)
    hass.config_entries.async_update_entry(
        item, data={**item.data, "source_timezone": "Not/AZone"}
    )
    assert await hass.config_entries.async_setup(item.entry_id)
    await hass.async_block_till_done()
    original = item.runtime_data
    assert original.timezone.key == "UTC"
    assert original.update_interval == timedelta(minutes=30)
    hass.config_entries.async_update_entry(item, options={"poll_minutes": 90})
    await hass.async_block_till_done()
    assert item.runtime_data is not original
    assert original._cancel_rollover is None
    assert item.runtime_data.update_interval == timedelta(minutes=90)


async def test_rate_limit_fallback_persist_and_success_reset(hass, client, freezer):
    item = entry(hass)
    assert await hass.config_entries.async_setup(item.entry_id)
    await hass.async_block_till_done()
    client.async_get_day.side_effect = LoseItRateLimitError()
    await item.runtime_data.async_refresh()
    assert item.runtime_data.cooldown_remaining == 1800
    assert item.data["rate_failures"] == 1
    old_count = client.async_get_day.call_count
    await hass.async_block_till_done()
    assert (
        client.async_get_day.call_count == old_count
    )  # data persistence must not reload
    freezer.tick(timedelta(minutes=31))
    # Explicit fetch, without dispatching unrelated periodic timers.
    await item.runtime_data.async_refresh()
    assert item.runtime_data.cooldown_remaining == 3600
    assert item.data["rate_failures"] == 2
    freezer.tick(timedelta(minutes=61))
    client.async_get_day.side_effect = lambda day: DailySnapshot(day, food_kcal=0)
    await item.runtime_data.async_refresh()
    assert item.runtime_data.cooldown_remaining == 0
    assert "rate_failures" not in item.data


async def test_rollover_unknown_during_slow_request_and_dst_schedule(
    hass, client, freezer
):
    freezer.move_to("2026-03-08T07:59:59Z")
    item = entry(hass)
    hass.config_entries.async_update_entry(
        item, data={**item.data, "source_timezone": "America/Los_Angeles"}
    )
    client.async_get_day.side_effect = lambda day: DailySnapshot(
        day, food_kcal=20, weight_kg=70, goal_weight_kg=60
    )
    assert await hass.config_entries.async_setup(item.entry_id)
    await hass.async_block_till_done()
    coordinator = item.runtime_data
    weight = hass.states.get("sensor.lose_it_recorded_weight_for_diary_day")
    assert weight.state == "70"
    assert "state_class" not in weight.attributes
    started, finish = asyncio.Event(), asyncio.Event()

    async def slow(day):
        started.set()
        await finish.wait()
        return DailySnapshot(day, food_kcal=0, weight_kg=70)

    client.async_get_day.side_effect = slow
    freezer.tick(timedelta(seconds=2))
    async_fire_time_changed(hass)
    await started.wait()
    assert hass.states.get("sensor.lose_it_food_calories").state == STATE_UNKNOWN
    assert (
        hass.states.get("sensor.lose_it_recorded_weight_for_diary_day").state
        == STATE_UNKNOWN
    )
    assert hass.states.get("sensor.lose_it_goal_weight").state == "60"
    finish.set()
    await hass.async_block_till_done()
    assert hass.states.get("sensor.lose_it_food_calories").state == "0"
    assert hass.states.get("sensor.lose_it_recorded_weight_for_diary_day").state == "70"
    # Spring DST source day is 23 hours: next midnight is 07:00Z, not 08:00Z.
    with patch(
        "custom_components.loseit.coordinator.async_track_point_in_utc_time"
    ) as track:
        coordinator._cancel_rollover()
        coordinator.start_rollover()
        assert track.call_args.args[2].isoformat() == "2026-03-09T07:00:00+00:00"


async def test_reconfigure_same_account(hass, client):
    item = entry(hass)
    result = await start_session(
        hass, "loseit", context={"source": "reconfigure", "entry_id": item.entry_id}
    )
    assert result["step_id"] == "session"
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"session_cookies": '{"session":"synthetic-new"}', "timezone": "UTC"},
    )
    assert result["reason"] == "reconfigure_successful"
    assert item.data["cookies"] == {"session": "synthetic-new"}
    await hass.async_block_till_done()


async def test_reauth_obeys_existing_account_cooldown(hass, client):
    item = entry(hass)
    hass.config_entries.async_update_entry(
        item,
        data={
            **item.data,
            "retry_not_before": dt_util.utcnow().timestamp() + 100,
        },
    )
    result = await start_session(
        hass,
        "loseit",
        context={
            "source": "reauth",
            "entry_id": item.entry_id,
        },
        data=item.data,
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "session_cookies": '{"session":"synthetic-new"}',
            "timezone": "UTC",
        },
    )
    assert result["errors"] == {"base": "rate_limited"}
    client.async_get_account.assert_not_called()


async def test_initial_flow_rate_limit_blocks_repeated_submit(hass, client):
    client.async_get_account.side_effect = LoseItRateLimitError()
    result = await start_session(hass, "loseit", context={"source": "user"})
    data = {"session_cookies": '{"session":"synthetic"}', "timezone": "UTC"}
    result = await hass.config_entries.flow.async_configure(result["flow_id"], data)
    assert result["errors"] == {"base": "rate_limited"}
    result = await hass.config_entries.flow.async_configure(result["flow_id"], data)
    assert result["errors"] == {"base": "rate_limited"}
    assert client.async_get_account.call_count == 1

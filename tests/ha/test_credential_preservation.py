"""Existing access survives unsuccessful native replacement and upgrade paths."""

import asyncio
import json
from copy import deepcopy

import pytest
from flow_helpers import start_session
from homeassistant.helpers import entity_registry as er
from test_integration import entry

from custom_components.loseit.client import (
    Account,
    LoseItAccessError,
    LoseItAuthError,
    LoseItConnectionError,
    LoseItRateLimitError,
)

pytestmark = pytest.mark.usefixtures("enable_custom_integrations")


def identities(hass, item):
    return {
        entity.entity_id: (entity.id, entity.unique_id, entity.config_entry_id)
        for entity in er.async_entries_for_config_entry(
            er.async_get(hass), item.entry_id
        )
    }


async def test_throttled_replacement_preserves_loaded_entry_and_shares_cooldown(
    hass, client
):
    item = entry(hass, options={"timezone": "America/Chicago", "poll_minutes": 90})
    original = deepcopy(dict(item.data))
    options = deepcopy(dict(item.options))
    assert await hass.config_entries.async_setup(item.entry_id)
    await hass.async_block_till_done()
    registered = identities(hass, item)
    coordinator = item.runtime_data
    client.async_get_account.side_effect = LoseItRateLimitError(120)
    result = await start_session(
        hass,
        context={"source": "reauth", "entry_id": item.entry_id},
        data={"session_cookies": '{"session":"replacement"}', "timezone": "UTC"},
    )
    assert result["errors"] == {"base": "rate_limited"}
    assert dict(item.data) == original
    assert dict(item.options) == options
    assert identities(hass, item) == registered
    assert item.runtime_data is coordinator
    assert hass.states.get("sensor.lose_it_food_calories").state == "0"
    hass.config_entries.flow.async_abort(result["flow_id"])
    result = await start_session(
        hass,
        context={"source": "reconfigure", "entry_id": item.entry_id},
        data={"session_cookies": '{"session":"replacement"}', "timezone": "UTC"},
    )
    assert result["errors"] == {"base": "rate_limited"}
    client.async_get_account.assert_awaited_once()
    reads = client.async_get_day.await_count
    await coordinator.async_refresh()
    assert client.async_get_day.await_count == reads
    assert await hass.config_entries.async_unload(item.entry_id)
    assert not await hass.config_entries.async_setup(item.entry_id)
    assert client.async_get_day.await_count == reads
    assert dict(item.data) == original
    assert dict(item.options) == options
    assert identities(hass, item) == registered


@pytest.mark.parametrize("stored_method", ["legacy", "password"])
@pytest.mark.parametrize("source", ["reauth", "reconfigure"])
@pytest.mark.parametrize(
    "failure,error",
    [
        (LoseItAuthError(), "invalid_auth"),
        (LoseItConnectionError(), "cannot_connect"),
        (LoseItAccessError(), "cannot_connect"),
        (LoseItRateLimitError(120), "rate_limited"),
        (None, "wrong_account"),
    ],
)
async def test_failed_replacement_keeps_existing_sensors_and_exact_configuration(
    hass, client, source, failure, error, stored_method
):
    item = entry(hass, options={"timezone": "America/Chicago", "poll_minutes": 90})
    if stored_method == "password":
        hass.config_entries.async_update_entry(
            item,
            data={
                **item.data,
                "auth_method": "password",
                "username": "saved@example.test",
            },
        )
    original = deepcopy(item.as_dict())
    assert await hass.config_entries.async_setup(item.entry_id)
    await hass.async_block_till_done()
    registered = identities(hass, item)
    assert len(registered) == 13
    coordinator = item.runtime_data
    client.async_get_account.side_effect = failure
    client.async_get_account.return_value = Account("different-account", "UTC")
    result = await start_session(
        hass,
        context={"source": source, "entry_id": item.entry_id},
        data={
            "session_cookies": '{"session":"replacement-cookie-canary"}',
            "timezone": "UTC",
        },
    )
    assert result.get("reason", result.get("errors", {}).get("base")) == error
    assert item.as_dict() == original
    assert identities(hass, item) == registered
    assert item.runtime_data is coordinator
    assert hass.states.get("sensor.lose_it_food_calories").state == "0"
    assert "canary" not in str(result)
    if result["type"] == "form":
        hass.config_entries.flow.async_abort(result["flow_id"])
    assert item.as_dict() == original


@pytest.mark.parametrize("stored_method", ["legacy", "password"])
@pytest.mark.parametrize("source", ["reauth", "reconfigure"])
async def test_cancelled_inflight_replacement_preserves_loaded_access(
    hass, client, source, stored_method
):
    item = entry(hass, options={"timezone": "America/Chicago", "poll_minutes": 90})
    if stored_method == "password":
        hass.config_entries.async_update_entry(
            item,
            data={
                **item.data,
                "auth_method": "password",
                "username": "saved@example.test",
            },
        )
    original = deepcopy(item.as_dict())
    assert await hass.config_entries.async_setup(item.entry_id)
    await hass.async_block_till_done()
    registered = identities(hass, item)
    coordinator = item.runtime_data
    started = asyncio.Event()

    async def pending(*args):
        started.set()
        await asyncio.Event().wait()

    client.async_get_account.side_effect = pending
    form = await start_session(
        hass, context={"source": source, "entry_id": item.entry_id}
    )
    task = asyncio.create_task(
        hass.config_entries.flow.async_configure(
            form["flow_id"],
            {
                "session_cookies": '{"session":"replacement-cookie-canary"}',
                "timezone": "UTC",
            },
        )
    )
    await started.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    hass.config_entries.flow.async_abort(form["flow_id"])
    assert item.as_dict() == original
    assert identities(hass, item) == registered
    assert item.runtime_data is coordinator
    await coordinator.async_refresh()
    assert hass.states.get("sensor.lose_it_food_calories").state == "0"
    assert item.as_dict() == original


@pytest.mark.parametrize("stored_method", ["legacy", "password"])
async def test_legacy_entry_reload_keeps_customized_entity_identity_without_signin(
    hass, client, stored_method
):
    item = entry(hass, options={"timezone": "America/Chicago", "poll_minutes": 90})
    if stored_method == "password":
        hass.config_entries.async_update_entry(
            item,
            data={
                **item.data,
                "auth_method": "password",
                "username": "saved@example.test",
            },
        )
    original = deepcopy(item.as_dict())
    assert await hass.config_entries.async_setup(item.entry_id)
    await hass.async_block_till_done()
    registry = er.async_get(hass)
    registry.async_update_entity(
        "sensor.lose_it_food_calories", new_entity_id="sensor.my_existing_food"
    )
    await hass.async_block_till_done()
    registered = identities(hass, item)
    assert len(registered) == 13
    assert await hass.config_entries.async_reload(item.entry_id)
    await hass.async_block_till_done()
    assert identities(hass, item) == registered
    assert hass.states.get("sensor.my_existing_food").state == "0"
    assert item.as_dict() == original
    assert json.loads(json.dumps(dict(item.options))) == original["options"]
    client.async_get_account.assert_not_awaited()
    assert not hass.config_entries.flow.async_progress()

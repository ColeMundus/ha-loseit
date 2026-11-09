"""Timezone loading must use HA's async, executor-backed API."""

import threading
import zoneinfo
from unittest.mock import call, patch

import pytest
from aiozoneinfo import CachedZoneInfo
from flow_helpers import start_session
from homeassistant.util import dt as dt_util
from test_integration import entry

pytestmark = pytest.mark.usefixtures("enable_custom_integrations")


@pytest.mark.parametrize("source", ["user", "reauth", "reconfigure", "options"])
@pytest.mark.parametrize("timezone", ["America/Chicago", "No/SuchZone"])
async def test_flow_resolves_timezone_asynchronously(hass, client, source, timezone):
    item = entry(hass)
    original_data, original_options = dict(item.data), dict(item.options)
    if source == "options":
        result = await hass.config_entries.options.async_init(item.entry_id)
        manager = hass.config_entries.options
        data = {"timezone": timezone, "poll_minutes": 60}
    else:
        context = {"source": source}
        if source != "user":
            context["entry_id"] = item.entry_id
        result = await start_session(hass, context=context)
        manager = hass.config_entries.flow
        data = {"timezone": timezone, "session_cookies": "liauth=synthetic-new"}

    with patch.object(
        dt_util, "async_get_time_zone", wraps=dt_util.async_get_time_zone
    ) as resolve:
        result = await manager.async_configure(result["flow_id"], data)
        await hass.async_block_till_done()
        resolve.assert_any_await(timezone)

    if timezone == "No/SuchZone":
        assert result["type"] == "form"
        assert result["errors"] == (
            {"timezone": "invalid_timezone"}
            if source == "options"
            else {"base": "invalid_input"}
        )
        client.async_get_account.assert_not_awaited()
        assert dict(item.data) == original_data
        assert dict(item.options) == original_options
    elif source == "user":
        # This synthetic account already has an entry; validation still runs first.
        assert result["reason"] == "already_configured"
    elif source == "options":
        assert result["type"] == "create_entry"
        assert item.options["timezone"] == timezone
    else:
        assert result["reason"] == f"{source}_successful"
        assert item.data["timezone"] == timezone
        assert item.options["timezone"] == timezone


@pytest.mark.parametrize(
    ("source_timezone", "expected_timezone", "lookups"),
    [
        ("America/Los_Angeles", "America/Los_Angeles", ["America/Los_Angeles"]),
        ("No/SuchZone", "America/Chicago", ["No/SuchZone", "America/Chicago"]),
        (None, "America/Chicago", ["America/Chicago"]),
        ("/invalid", "America/Chicago", ["/invalid", "America/Chicago"]),
    ],
)
async def test_setup_resolves_timezone_before_coordinator(
    hass, client, freezer, source_timezone, expected_timezone, lookups
):
    freezer.move_to("2026-03-08T07:30:00Z")
    item = entry(hass, options={"timezone": "America/Chicago"})
    hass.config_entries.async_update_entry(
        item,
        data={
            **item.data,
            "timezone": "America/New_York",
            "source_timezone": source_timezone,
        },
    )
    with patch.object(
        dt_util, "async_get_time_zone", wraps=dt_util.async_get_time_zone
    ) as resolve:
        assert await hass.config_entries.async_setup(item.entry_id)
        await hass.async_block_till_done()
        resolve.assert_has_awaits([call(name) for name in lookups])

    coordinator = item.runtime_data
    assert coordinator.timezone.key == expected_timezone
    assert coordinator.current_day.isoformat() == (
        "2026-03-07" if expected_timezone == "America/Los_Angeles" else "2026-03-08"
    )
    client.async_get_day.assert_awaited_once_with(coordinator.current_day)


async def test_setup_rejects_invalid_source_and_fallback_before_provider(hass, client):
    item = entry(hass, options={"timezone": "No/SuchZone"})
    hass.config_entries.async_update_entry(
        item, data={**item.data, "source_timezone": "Also/Invalid"}
    )
    original = dict(item.data)
    with patch.object(
        dt_util, "async_get_time_zone", wraps=dt_util.async_get_time_zone
    ) as resolve:
        assert not await hass.config_entries.async_setup(item.entry_id)
        await hass.async_block_till_done()
        resolve.assert_has_awaits([call("Also/Invalid"), call("No/SuchZone")])

    client.async_get_day.assert_not_awaited()
    assert dict(item.data) == original


@pytest.mark.parametrize(
    "source", ["user", "reauth", "reconfigure", "options", "runtime"]
)
async def test_cold_timezone_files_load_off_event_loop(
    hass, client, monkeypatch, source
):
    timezone = "Asia/Kathmandu"
    loop_thread = threading.get_ident()
    reads = []
    load_data = zoneinfo._common.load_data

    def checked_load_data(file):
        assert threading.get_ident() != loop_thread, "Timezone read on event loop"
        reads.append(threading.get_ident())
        return load_data(file)

    zoneinfo.ZoneInfo.clear_cache(only_keys=[timezone])
    CachedZoneInfo.clear_cache(only_keys=[timezone])
    CachedZoneInfo._weak_cache.pop(timezone, None)
    monkeypatch.setattr(zoneinfo._common, "load_data", checked_load_data)

    # Positive control: the exact former synchronous construction must be caught.
    with pytest.raises(AssertionError, match="Timezone read on event loop"):
        zoneinfo.ZoneInfo(timezone)

    item = entry(hass)
    if source == "runtime":
        hass.config_entries.async_update_entry(
            item, data={**item.data, "source_timezone": timezone}
        )
        assert await hass.config_entries.async_setup(item.entry_id)
    elif source == "options":
        result = await hass.config_entries.options.async_init(item.entry_id)
        result = await hass.config_entries.options.async_configure(
            result["flow_id"], {"timezone": timezone, "poll_minutes": 60}
        )
        assert result["type"] == "create_entry"
    else:
        context = {"source": source}
        if source != "user":
            context["entry_id"] = item.entry_id
        result = await start_session(hass, context=context)
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"timezone": timezone, "session_cookies": "liauth=synthetic-new"},
        )
        assert result["type"] == "abort"
        assert result["reason"] == (
            "already_configured" if source == "user" else f"{source}_successful"
        )
    await hass.async_block_till_done()
    assert reads

    if source == "runtime":
        count = len(reads)
        coordinator = item.runtime_data
        resolved = coordinator.timezone
        await coordinator.async_refresh()
        assert coordinator.timezone is resolved
        assert len(reads) == count

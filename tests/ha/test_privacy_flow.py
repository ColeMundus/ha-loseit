"""Validation and strict diagnostics privacy contracts."""

import json

import pytest
from flow_helpers import start_session
from test_integration import entry

from custom_components.loseit.client import LoseItConnectionError, LoseItRateLimitError
from custom_components.loseit.diagnostics import async_get_config_entry_diagnostics

pytestmark = pytest.mark.usefixtures("enable_custom_integrations")


async def test_invalid_timezone_and_network_error(hass, client):
    result = await start_session(hass, "loseit", context={"source": "user"})
    data = {"session_cookies": '{"session":"synthetic"}', "timezone": "No/SuchZone"}
    result = await hass.config_entries.flow.async_configure(result["flow_id"], data)
    assert result["errors"] == {"base": "invalid_input"}
    client.async_get_account.assert_not_called()
    client.async_get_account.side_effect = LoseItConnectionError("credential-canary")
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {**data, "timezone": "UTC"}
    )
    assert result["errors"] == {"base": "cannot_connect"}


async def test_reauth_rate_limit_survives_cancellation_without_entry_write(
    hass, client
):
    item = entry(hass)
    original = dict(item.data)
    client.async_get_account.side_effect = LoseItRateLimitError(120)
    result = await start_session(
        hass,
        "loseit",
        context={"source": "reauth", "entry_id": item.entry_id},
        data=item.data,
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"session_cookies": '{"session":"synthetic-new"}', "timezone": "UTC"},
    )
    assert result["errors"] == {"base": "rate_limited"}
    assert dict(item.data) == original
    hass.config_entries.flow.async_abort(result["flow_id"])
    result = await start_session(
        hass,
        context={"source": "user"},
        data={"session_cookies": json.dumps(original["cookies"]), "timezone": "UTC"},
    )
    assert result["errors"] == {"base": "rate_limited"}
    client.async_get_account.assert_awaited_once()
    assert dict(item.data) == original


async def test_diagnostics_nested_unknown_keys_never_leak(hass, client):
    item = entry(hass)
    hass.config_entries.async_update_entry(
        item,
        data={
            **item.data,
            "auth_method": "password",
            "username": "username-canary@example.test",
            "future_field": {
                "health_value": "health-canary",
                "token": ["credential-canary"],
                "url": "https://private.example/identity-canary",
            },
        },
    )
    assert await hass.config_entries.async_setup(item.entry_id)
    await hass.async_block_till_done()
    item.runtime_data.unexpected_payload = {"future": "nested-secret-canary"}
    result = await async_get_config_entry_diagnostics(hass, item)
    assert set(result) == {
        "integration_version",
        "experimental_transport",
        "read_only",
        "poll_minutes",
        "last_update_success",
        "outcome",
        "cooldown_active",
    }
    serialized = json.dumps(result)
    assert "canary" not in serialized
    assert "synthetic" not in serialized

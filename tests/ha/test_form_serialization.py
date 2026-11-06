"""UI schema serialization must work, not just in-process flow invocation."""

import json

import probatio
import pytest
from flow_helpers import start_session
from homeassistant.helpers import config_validation as cv
from test_integration import entry

pytestmark = pytest.mark.usefixtures("enable_custom_integrations")


@pytest.mark.parametrize("source", ["user", "reauth", "reconfigure", "options"])
async def test_frontend_can_serialize_each_form(hass, client, source):
    item = entry(hass)
    if source == "options":
        result = await hass.config_entries.options.async_init(item.entry_id)
    else:
        context = {"source": source}
        if source != "user":
            context["entry_id"] = item.entry_id
        result = await start_session(
            hass,
            "loseit",
            context=context,
            data=item.data if source == "reauth" else None,
        )
    fields = probatio.to_field_list(
        result["data_schema"], custom_serializer=cv.custom_serializer
    )
    assert {field["name"] for field in fields} >= {"timezone"}
    assert json.loads(json.dumps(fields)) == fields


async def test_invalid_options_timezone_does_not_change_entry(hass, client):
    item = entry(hass, options={"timezone": "UTC", "poll_minutes": 60})
    result = await hass.config_entries.options.async_init(item.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"timezone": "No/SuchZone", "poll_minutes": 90}
    )
    assert result["type"] == "form"
    assert result["errors"] == {"timezone": "invalid_timezone"}
    assert item.options == {"timezone": "UTC", "poll_minutes": 60}


@pytest.mark.parametrize("source", ["user", "reauth", "reconfigure"])
async def test_timezone_defaults_are_effective_settings_not_utc(hass, client, source):
    hass.config.time_zone = "America/Chicago"
    item = entry(hass, options={"timezone": "America/New_York"})
    context = {"source": source}
    if source != "user":
        context["entry_id"] = item.entry_id
    result = await start_session(hass, context=context)
    fields = probatio.to_field_list(
        result["data_schema"], custom_serializer=cv.custom_serializer
    )
    timezone = next(field for field in fields if field["name"] == "timezone")
    assert timezone["default"] == (
        "America/Chicago" if source == "user" else "America/New_York"
    )
    assert json.loads(json.dumps(fields)) == fields

"""Exercise direct native cookie forms, including frontend serialization."""

import json

import probatio
from homeassistant.helpers import config_validation as cv


async def start_session(hass, domain="loseit", *, context=None, data=None):
    result = await hass.config_entries.flow.async_init(domain, context=context)
    assert result["type"] == "form"
    assert result["step_id"] == "session"
    fields = probatio.to_field_list(
        result["data_schema"], custom_serializer=cv.custom_serializer
    )
    assert json.loads(json.dumps(fields)) == fields
    assert {field["name"] for field in fields} == {"session_cookies", "timezone"}
    if data is not None and "session_cookies" in data:
        result = await hass.config_entries.flow.async_configure(result["flow_id"], data)
    return result

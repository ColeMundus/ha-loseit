"""Every native access flow directly exposes serializable cookie guidance."""

import json

import probatio
import pytest
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.translation import async_get_translations
from test_integration import entry

from custom_components.loseit.client import LoseItAuthError

pytestmark = pytest.mark.usefixtures("enable_custom_integrations")

GUIDE = "https://github.com/ColeMundus/ha-loseit/blob/main/docs/session-cookies.md"


@pytest.mark.parametrize("source", ["user", "reauth", "reconfigure"])
async def test_direct_cookie_form_has_reachable_translated_guide(hass, client, source):
    item = entry(hass)
    context = {"source": source}
    if source != "user":
        context["entry_id"] = item.entry_id
    form = await hass.config_entries.flow.async_init("loseit", context=context)
    assert form["type"] == "form"
    assert form["step_id"] == "session"
    assert "menu_options" not in form
    translations = await async_get_translations(hass, "en", "config", {"loseit"})
    prefix = "component.loseit.config.step."
    description = translations[prefix + form["step_id"] + ".description"]
    assert "https://" not in description
    assert form["description_placeholders"]["guide_url"] == GUIDE
    description = description.format_map(form["description_placeholders"])
    assert f"]({GUIDE})" in description
    for text in (
        "1.",
        "2.",
        "3.",
        "Network",
        "Request Headers",
        "Cookie",
        "Copy value",
        "Paste",
        "timezone",
        "private",
    ):
        assert text in description
    assert "Copy request headers" not in description
    label = translations[prefix + form["step_id"] + ".data.session_cookies"]
    assert label == "Website session"
    fields = probatio.to_field_list(
        form["data_schema"], custom_serializer=cv.custom_serializer
    )
    assert {field["name"] for field in fields} == {"session_cookies", "timezone"}
    assert json.loads(json.dumps({"description": description, "fields": fields}))
    assert not any("password" in key or "menu_options" in key for key in translations)
    client.async_get_account.assert_not_awaited()
    hass.config_entries.flow.async_abort(form["flow_id"])


@pytest.mark.parametrize("source", ["user", "reauth", "reconfigure"])
@pytest.mark.parametrize("invalid", ["input", "auth"])
async def test_cookie_error_forms_keep_guide_and_never_echo_cookies(
    hass, client, source, invalid
):
    item = entry(hass)
    context = {"source": source}
    if source != "user":
        context["entry_id"] = item.entry_id
    form = await hass.config_entries.flow.async_init("loseit", context=context)
    client.async_get_account.side_effect = LoseItAuthError("private-cookie-canary")
    data = {
        "session_cookies": '{"liauth":"private-cookie-canary"}',
        "timezone": "No/SuchZone" if invalid == "input" else "UTC",
    }
    result = await hass.config_entries.flow.async_configure(form["flow_id"], data)
    assert result["errors"] == {
        "base": "invalid_input" if invalid == "input" else "invalid_auth"
    }
    assert result["step_id"] == "session"
    fields = probatio.to_field_list(
        result["data_schema"], custom_serializer=cv.custom_serializer
    )
    assert "canary" not in json.dumps(fields)
    translations = await async_get_translations(hass, "en", "config", {"loseit"})
    description = translations["component.loseit.config.step.session.description"]
    assert "https://" not in description
    assert GUIDE in description.format_map(result["description_placeholders"])
    message = translations["component.loseit.config.error." + result["errors"]["base"]]
    assert "cookie" in message
    assert "password" not in message
    assert json.loads(json.dumps({"fields": fields, "message": message}))
    if invalid == "input":
        client.async_get_account.assert_not_awaited()

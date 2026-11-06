"""Real HA flow seams for cooldown scope and effective fallback options."""

import asyncio
import json
from datetime import timedelta

import pytest
from flow_helpers import start_session
from homeassistant.util import dt as dt_util
from test_integration import entry

from custom_components.loseit.client import Account, LoseItRateLimitError

pytestmark = pytest.mark.usefixtures("enable_custom_integrations")


def submission(cookie="synthetic-secret", timezone="UTC"):
    return {"session_cookies": '{"session":"' + cookie + '"}', "timezone": timezone}


async def start(hass, data, source="user", item=None):
    context = {"source": source}
    if item:
        context["entry_id"] = item.entry_id
    result = await start_session(hass, "loseit", context=context)
    return await hass.config_entries.flow.async_configure(result["flow_id"], data)


async def test_cancel_reopen_cookie_cooldown_and_unrelated_session(
    hass, client, freezer
):
    client.async_get_account.side_effect = LoseItRateLimitError(120)
    result = await start(hass, submission())
    assert result["errors"] == {"base": "rate_limited"}
    hass.config_entries.flow.async_abort(result["flow_id"])
    result = await start(hass, submission())
    assert result["errors"] == {"base": "rate_limited"}
    assert client.async_get_account.call_count == 1
    hass.config_entries.flow.async_abort(result["flow_id"])
    client.async_get_account.side_effect = None
    client.async_get_account.return_value = Account("unrelated-synthetic", "UTC")
    result = await start(hass, submission("unrelated-cookie"))
    assert result["type"] == "create_entry"
    assert client.async_get_account.call_count == 2
    await hass.async_block_till_done()
    freezer.tick(timedelta(seconds=121))
    client.async_get_account.side_effect = LoseItRateLimitError(120)
    result = await start(hass, submission())
    assert result["errors"] == {"base": "rate_limited"}
    assert client.async_get_account.call_count == 3


async def test_duplicate_setup_honors_entry_cooldown_without_network(hass, client):
    item = entry(hass)
    hass.config_entries.async_update_entry(
        item, data={**item.data, "retry_not_before": dt_util.utcnow().timestamp() + 120}
    )
    result = await start(hass, submission())
    assert result["errors"] == {"base": "rate_limited"}
    client.async_get_account.assert_not_called()


async def test_reauth_cooldown_shared_with_new_setup(hass, client):
    item = entry(hass)
    client.async_get_account.side_effect = LoseItRateLimitError(120)
    result = await start(hass, submission("replacement"), "reauth", item)
    assert result["errors"] == {"base": "rate_limited"}
    hass.config_entries.flow.async_abort(result["flow_id"])
    result = await start(hass, submission("replacement"))
    assert result["errors"] == {"base": "rate_limited"}
    assert client.async_get_account.call_count == 1


@pytest.mark.parametrize("source", ["reauth", "reconfigure"])
@pytest.mark.parametrize("stored_method", ["legacy", "password"])
async def test_same_account_replacement_updates_effective_timezone_preserves_poll(
    hass, client, source, stored_method
):
    item = entry(hass, options={"timezone": "UTC", "poll_minutes": 90})
    assert await hass.config_entries.async_setup(item.entry_id)
    await hass.async_block_till_done()
    if stored_method == "password":
        hass.config_entries.async_update_entry(
            item,
            data={
                **item.data,
                "auth_method": "password",
                "username": "saved@example.test",
            },
        )
    client.async_get_account.return_value = Account("synthetic-account", None)
    cookies = {
        "liauth": "  exact +/= cookie ",
        "fn_auth": "opaque%2F+==",
        "fn_authed": " 1 ",
    }
    result = await start(
        hass,
        {"session_cookies": json.dumps(cookies), "timezone": "America/Chicago"},
        source,
        item,
    )
    assert result["reason"] == source + "_successful"
    assert item.options == {"timezone": "America/Chicago", "poll_minutes": 90}
    assert item.data["cookies"] == cookies
    assert item.unique_id == "synthetic-account"
    if stored_method == "password":
        assert item.data["username"] == "saved@example.test"
        assert item.data["auth_method"] == "password"
    await hass.async_block_till_done()
    assert item.runtime_data.timezone.key == "America/Chicago"
    assert item.runtime_data.update_interval == timedelta(minutes=90)


async def test_identified_replacement_cookie_obeys_known_account_cooldown(hass, client):
    item = entry(hass)
    result = await start(hass, submission("another-session"))
    assert result["reason"] == "already_configured"
    assert client.async_get_account.call_count == 1
    hass.config_entries.async_update_entry(
        item, data={**item.data, "retry_not_before": dt_util.utcnow().timestamp() + 120}
    )
    result = await start(hass, submission("another-session"))
    assert result["errors"] == {"base": "rate_limited"}
    assert client.async_get_account.call_count == 1


async def test_unknown_cookie_identifies_duplicate_then_blocks_further_io(hass, client):
    item = entry(hass)
    hass.config_entries.async_update_entry(
        item, data={**item.data, "retry_not_before": dt_util.utcnow().timestamp() + 120}
    )
    result = await start(hass, submission("unknown-session"))
    assert result["errors"] == {"base": "rate_limited"}
    assert client.async_get_account.call_count == 1
    client.async_get_day.assert_not_called()
    hass.config_entries.flow.async_abort(result["flow_id"])
    result = await start(hass, submission("unknown-session"))
    assert result["errors"] == {"base": "rate_limited"}
    assert client.async_get_account.call_count == 1
    assert set(item.data) == {
        "cookies",
        "timezone",
        "source_timezone",
        "retry_not_before",
    }


async def test_wrong_account_cookie_does_not_rebind_existing_cookie(hass, client):
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    item = entry(hass)
    client.async_get_account.return_value = Account("other-account", "UTC")
    result = await start(hass, submission("wrong-account-cookie"), "reconfigure", item)
    assert result["reason"] == "wrong_account"
    other = MockConfigEntry(
        domain="loseit",
        unique_id="other-account",
        title="Other",
        data={
            "cookies": {"liauth": "other-cookie"},
            "timezone": "UTC",
            "source_timezone": "UTC",
            "retry_not_before": dt_util.utcnow().timestamp() + 120,
        },
    )
    other.add_to_hass(hass)
    client.async_get_account.return_value = Account("synthetic-account", "UTC")
    result = await start(hass, submission())
    assert result["reason"] == "already_configured"
    assert client.async_get_account.await_count == 2


async def test_concurrent_cookie_flows_share_inflight_cooldown(hass, client):
    started = asyncio.Event()
    release = asyncio.Event()

    async def limited():
        started.set()
        await release.wait()
        raise LoseItRateLimitError(120)

    client.async_get_account.side_effect = limited
    forms = [await start_session(hass, context={"source": "user"}) for _ in range(2)]
    first = asyncio.create_task(
        hass.config_entries.flow.async_configure(forms[0]["flow_id"], submission())
    )
    await started.wait()
    second = asyncio.create_task(
        hass.config_entries.flow.async_configure(forms[1]["flow_id"], submission())
    )
    release.set()
    results = await asyncio.gather(first, second)
    assert all(result["errors"] == {"base": "rate_limited"} for result in results)
    client.async_get_account.assert_awaited_once()

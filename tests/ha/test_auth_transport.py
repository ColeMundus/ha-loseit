"""Actual HA cookie flow/client, with loopback-only synthetic HTTP."""

import json
from unittest.mock import AsyncMock, patch

import aiohttp
import pytest
from aiohttp import web
from flow_helpers import start_session

pytestmark = pytest.mark.usefixtures("enable_custom_integrations")


@pytest.mark.enable_socket
async def test_native_flow_validates_imported_cookies_over_synthetic_transport(hass):
    calls = []
    identity = json.dumps(
        [
            -6,
            2,
            731,
            1,
            ["com.loseit.core.client.model.UserId/4281239478", "synthetic-user"],
            0,
            7,
        ]
    )

    async def handler(request):
        assert request.method == "GET"
        assert request.cookies == {"liauth": "synthetic-cookie"}
        return web.Response(text="window.embedded_4ppl1c4710n=" + json.dumps(identity))

    app = web.Application()
    app.router.add_route("*", "/{path:.*}", handler)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    port = site._server.sockets[0].getsockname()[1]
    try:
        async with aiohttp.ClientSession(
            cookie_jar=aiohttp.DummyCookieJar()
        ) as session:

            class SyntheticTransport:
                def request(self, verb, url, **kwargs):
                    calls.append((verb, url))
                    assert kwargs["allow_redirects"] is False
                    assert url == "https://www.loseit.com/"
                    assert verb == "GET"
                    assert "data" not in kwargs
                    return session.request(verb, f"http://127.0.0.1:{port}/", **kwargs)

            with (
                patch(
                    "custom_components.loseit.config_flow.async_get_clientsession",
                    return_value=SyntheticTransport(),
                ),
                patch(
                    "custom_components.loseit.async_setup_entry",
                    new=AsyncMock(return_value=True),
                ),
            ):
                data = {"timezone": "America/Chicago"}
                data["session_cookies"] = '{"liauth":"synthetic-cookie"}'
                result = await start_session(
                    hass, context={"source": "user"}, data=data
                )
                assert result["type"] == "create_entry"
                assert result["result"].unique_id == "731"
                assert result["data"]["cookies"] == {"liauth": "synthetic-cookie"}
                assert "auth_method" not in result["data"]
                assert "username" not in result["data"]
                assert calls == [("GET", "https://www.loseit.com/")]
                await hass.async_block_till_done()
    finally:
        await runner.cleanup()

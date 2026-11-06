"""Real aiohttp I/O on loopback only, never Lose It servers."""

import asyncio
import json

import aiohttp
import pytest
from aiohttp import web
from test_client import load
from test_daily import DAY, dated_empty_wire
from test_protocol import USER, wire

schemas = load("schemas")


@pytest.mark.enable_socket
def test_real_aiohttp_read_only_roundtrip():
    async def scenario():
        c = load()
        identity = wire([1, 731, 2, -6], [USER, "synthetic-user"])
        raw = dated_empty_wire()
        calls = []

        async def handler(request):
            calls.append(request.method)
            assert request.cookies.get("liauth") == "synthetic"
            if request.method == "GET":
                return web.Response(
                    text="window.embedded_4ppl1c4710n=" + json.dumps(identity[4:])
                )
            body = await request.text()
            assert "getDailyDetailsIncludingPendingForDate" in body
            assert request.headers["X-GWT-Permutation"] == schemas.PERMUTATION
            return web.Response(text=raw)

        app = web.Application()
        app.router.add_route("*", "/", handler)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "127.0.0.1", 0)
        await site.start()
        port = site._server.sockets[0].getsockname()[1]
        try:
            async with aiohttp.ClientSession() as session:

                class LocalTransport:
                    def request(self, method, url, **kwargs):
                        # Change destination only; preserve production kwargs.
                        return session.request(
                            method, f"http://127.0.0.1:{port}/", **kwargs
                        )

                client = c.LoseItClient(LocalTransport(), {"liauth": "synthetic"})
                account = await client.async_get_account()
                snapshot = await client.async_get_day(DAY)
                assert account.account_id == "731"
                assert snapshot.logged_food_count == 0
                assert not session.closed
                assert calls == ["GET", "POST"]
        finally:
            await runner.cleanup()

    asyncio.run(scenario())

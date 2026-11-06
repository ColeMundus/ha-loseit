"""Synthetic protocol tests; no account credentials or network requests."""

import asyncio
import importlib.util
import sys
from pathlib import Path

import aiohttp
import pytest

PATH = Path(__file__).parents[2] / "custom_components/loseit"


def load(name="client"):
    """Import real pure modules, bypassing only the HA package initializer."""
    package = "isolated_loseit"
    if package not in sys.modules:
        spec = importlib.util.spec_from_loader(package, loader=None, is_package=True)
        module = importlib.util.module_from_spec(spec)
        module.__path__ = [str(PATH)]
        sys.modules[package] = module
    return importlib.import_module(f"{package}.{name}")


class Response:
    def __init__(self, status=200, body="", headers=None):
        self.status, self.body, self.headers = status, body, headers or {}
        self.content = self

    async def read(self, n=-1):
        result, self.body = self.body[:n], self.body[n:]
        return result.encode()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass


class Session:
    def __init__(self, *responses):
        self.responses, self.calls = list(responses), []
        self.closed = False

    def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        value = self.responses.pop(0)
        if isinstance(value, Exception):
            raise value
        return value


def test_http_auth_is_sanitized_and_no_redirect_or_session_close():
    c = load()
    session = Session(Response(401, "private-secret"))
    client = c.LoseItClient(session, {"liauth": "private-secret"})
    with pytest.raises(c.LoseItAuthError) as exc:
        asyncio.run(client.async_get_account())
    assert "private-secret" not in str(exc.value)
    assert session.calls[0][2]["allow_redirects"] is False
    assert not session.closed


@pytest.mark.parametrize(
    "status,error",
    [
        (429, "LoseItRateLimitError"),
        (503, "LoseItConnectionError"),
        (403, "LoseItAccessError"),
        (302, "LoseItAccessError"),
    ],
)
def test_http_errors(status, error):
    c = load()
    session = Session(Response(status, "private-secret", {"Retry-After": "42"}))
    with pytest.raises(getattr(c, error)) as exc:
        asyncio.run(
            c.LoseItClient(session, {"liauth": "synthetic"}).async_get_account()
        )
    assert "private-secret" not in str(exc.value)
    if status == 429:
        assert exc.value.retry_after == 42
    assert len(session.calls) == 1


@pytest.mark.parametrize(
    "body",
    ["<html>WAF challenge private-secret</html>", "Forbidden private-secret"],
)
def test_forbidden_is_sanitized_access_failure_not_expired_session(body, caplog):
    import traceback

    c = load()
    client = c.LoseItClient(Session(Response(403, body)), {"liauth": "private-secret"})
    with pytest.raises(c.LoseItError) as exc:
        asyncio.run(client.async_get_account())
    assert not isinstance(exc.value, c.LoseItAuthError)
    assert type(exc.value).__name__ == "LoseItAccessError"
    assert client._cookies == {"liauth": "private-secret"}
    assert "private-secret" not in "".join(traceback.format_exception(exc.value))
    assert "private-secret" not in caplog.text


def test_connection_error_hides_original_payload():
    c = load()
    with pytest.raises(c.LoseItConnectionError, match="connection") as exc:
        asyncio.run(
            c.LoseItClient(
                Session(aiohttp.ClientError("private-secret")), {"x": "y"}
            ).async_get_account()
        )
    assert exc.value.__suppress_context__


def test_missing_cookie_rejected_without_io():
    c = load()
    session = Session()
    with pytest.raises(c.LoseItAuthError):
        asyncio.run(c.LoseItClient(session, {}).async_get_account())
    assert not session.calls

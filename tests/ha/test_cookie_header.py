"""One-paste website access through actual HA setup/replacement flows."""

import json
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import Mock, patch

import probatio
import pytest
from flow_helpers import start_session
from homeassistant.helpers import config_validation as cv
from test_integration import entry

from custom_components.loseit.client import Account, LoseItAuthError

pytestmark = pytest.mark.usefixtures("enable_custom_integrations")


@pytest.mark.parametrize("source", ["user", "reauth", "reconfigure"])
@pytest.mark.parametrize(
    "raw,expected",
    [
        (
            "liauth=synthetic%2Fsecret==; fn_auth=other; fn_authed=true; _ga=tracking",
            {"liauth": "synthetic%2Fsecret==", "fn_auth": "other", "fn_authed": "true"},
        ),
        (
            "Cookie: fn_auth=synthetic%3Dsecret=; unrelated=ignored",
            {"fn_auth": "synthetic%3Dsecret="},
        ),
        (
            'liauth=synthetic%2Fsecret==; consent="yes"',
            {"liauth": "synthetic%2Fsecret=="},
        ),
        (
            "liauth=synthetic%2Fsecret==; other=bad,comma",
            {"liauth": "synthetic%2Fsecret=="},
        ),
        (
            "liauth=synthetic%2Fsecret==; other=back\\slash",
            {"liauth": "synthetic%2Fsecret=="},
        ),
        (
            "liauth=synthetic%2Fsecret==; other=bad value",
            {"liauth": "synthetic%2Fsecret=="},
        ),
        ('{"arbitrary":"legacy-secret"}', {"arbitrary": "legacy-secret"}),
        (
            "  cookie: liauth=exact%2f+==; fn_auth=; analytics=; analytics=ignored",
            {"liauth": "exact%2f+==", "fn_auth": ""},
        ),
        (
            '{\n "arbitrary": "legacy%2f==", "other": "unchanged"\n}',
            {"arbitrary": "legacy%2f==", "other": "unchanged"},
        ),
    ],
)
async def test_one_paste_persists_only_parsed_cookies(
    hass, client, source, raw, expected
):
    item = entry(hass) if source != "user" else None
    context = {"source": source}
    if item is not None:
        context["entry_id"] = item.entry_id
    with (
        patch("custom_components.loseit.config_flow.LoseItClient") as factory,
        patch.object(hass.config_entries, "async_reload", return_value=True),
    ):
        factory.return_value = client
        result = await start_session(
            hass, context=context, data={"session_cookies": raw, "timezone": "UTC"}
        )
        assert result["type"] == ("create_entry" if item is None else "abort")
        stored = result["result"] if item is None else item
        assert dict(stored.data) == {
            "cookies": expected,
            "timezone": "UTC",
            "source_timezone": "UTC",
        }
        assert stored.unique_id == "synthetic-account"
        assert factory.call_args.args[1] == expected
        client.async_get_account.assert_awaited_once()


BAD_INPUTS = [
    "liauth=first; liauth=second",
    "fn_auth=first; fn_auth=second",
    "liauth=ok; fn_authed=1; fn_authed=2",
    "fn_authed=true",
    "liauth=; fn_auth=; fn_authed=true",
    "_ga=analytics",
    "liauth=secret; broken",
    "liauth=secret;",
    "liauth=secret;; fn_auth=other",
    "liauth=secret; bad name=value",
    "liauth=secret; fn_auth=bad value",
    "liauth=secret; fn_auth=bad,comma",
    'liauth="quoted"',
    "liauth=secret; fn_auth=back\\slash",
    "liauth=secret\r\nX-Injected: value",
    "Cookie: liauth=secret\nHost: example.test",
    "liauth=secret\t",
    "liauth=secret\x00",
    "liauth=secret\x7f",
    "liauth=secret\u0085",
    "liauth=secret\u2028",
    "Host: example.test Cookie: liauth=secret",
    "curl -H 'Cookie: liauth=secret'",
    "liauth=" + "a" * 65536,
    '{"legacy":"' + "a" * 65536 + '"}',
    '{"legacy":"' + "é" * 32768 + '"}',
    '{"nested":' + "[" * 2000 + "0" + "]" * 2000 + "}",
    "{}",
    "[]",
    "not-json",
    "",
]


def serializable_fields(result):
    fields = probatio.to_field_list(
        result["data_schema"], custom_serializer=cv.custom_serializer
    )
    assert json.loads(json.dumps(fields)) == fields
    session = next(field for field in fields if field["name"] == "session_cookies")
    assert session["selector"]["text"]["type"] == "password"
    assert not session["selector"]["text"].get("multiline", False)
    assert "default" not in session
    return fields


@pytest.mark.parametrize("source", ["user", "reauth", "reconfigure"])
@pytest.mark.parametrize(
    "raw", BAD_INPUTS, ids=[f"invalid-{i}" for i in range(len(BAD_INPUTS))]
)
async def test_invalid_paste_is_local_serializable_and_preserves_entry(
    hass, client, source, raw, caplog
):
    item = entry(hass, options={"timezone": "America/Chicago", "poll_minutes": 90})
    original = deepcopy(item.as_dict())
    context = {"source": source}
    if source != "user":
        context["entry_id"] = item.entry_id
    result = await start_session(
        hass, context=context, data={"session_cookies": raw, "timezone": "UTC"}
    )
    assert result["type"] == "form"
    assert result["errors"] == {"base": "invalid_input"}
    serializable_fields(result)
    assert item.as_dict() == original
    client.async_get_account.assert_not_awaited()
    assert "secret" not in str(result)
    assert "secret" not in caplog.text


@pytest.mark.parametrize(
    "source,failure",
    [
        ("user", "auth"),
        ("reauth", "auth"),
        ("reconfigure", "auth"),
        ("reauth", "wrong_account"),
        ("reconfigure", "wrong_account"),
    ],
)
async def test_header_auth_failure_never_exposes_or_replaces_credentials(
    hass, client, source, failure, caplog
):
    item = entry(hass, options={"timezone": "America/Chicago", "poll_minutes": 90})
    original = deepcopy(item.as_dict())
    context = {"source": source}
    if source != "user":
        context["entry_id"] = item.entry_id
    canary = "invented-credential-canary"
    if failure == "auth":
        client.async_get_account.side_effect = LoseItAuthError(canary)
    else:
        client.async_get_account.return_value = Account("other-account", "UTC")
    result = await start_session(
        hass,
        context=context,
        data={"session_cookies": "liauth=" + canary, "timezone": "UTC"},
    )
    assert result.get("reason", result.get("errors", {}).get("base")) == (
        "invalid_auth" if failure == "auth" else "wrong_account"
    )
    if result["type"] == "form":
        serializable_fields(result)
    assert item.as_dict() == original
    assert canary not in str(result)
    assert canary not in caplog.text


@pytest.mark.parametrize("oversize", [False, True])
async def test_json_parser_failure_and_preparse_bound_are_sanitized(
    hass, client, caplog, oversize
):
    canary = "parser-credential-canary"
    loader = Mock(side_effect=RecursionError(canary))
    raw = '{"legacy":"' + ("x" * 65536 if oversize else canary) + '"}'
    with patch(
        "custom_components.loseit.config_flow.json", SimpleNamespace(loads=loader)
    ):
        result = await start_session(
            hass,
            context={"source": "user"},
            data={"session_cookies": raw, "timezone": "UTC"},
        )
    assert result["errors"] == {"base": "invalid_input"}
    assert loader.call_count == (0 if oversize else 1)
    client.async_get_account.assert_not_awaited()
    serializable_fields(result)
    assert canary not in str(result)
    assert canary not in caplog.text


@pytest.mark.parametrize("kind", ["header", "json"])
async def test_exact_64kib_boundary_is_accepted(hass, client, kind):
    if kind == "header":
        raw = "liauth=" + "x" * (65536 - len("liauth="))
    else:
        raw = '{"legacy":"' + "x" * (65536 - len('{"legacy":""}')) + '"}'
    assert len(raw.encode("utf-8")) == 65536
    result = await start_session(
        hass,
        context={"source": "user"},
        data={"session_cookies": raw, "timezone": "UTC"},
    )
    assert result["type"] == "create_entry"
    assert "session_cookies" not in result["result"].data
    client.async_get_account.assert_awaited_once()

"""Synthetic GWT v7 fixtures using publicly observed type signatures."""

import asyncio
import json

import pytest
from test_client import Response, Session, load

gwt = load("gwt")

USER = "com.loseit.core.client.model.UserId/4281239478"
DETAIL = "com.loseit.core.client.model.DailyDetails/1565598417"
LOG = "com.loseit.core.client.model.DailyLogEntry/612926967"
STATE = "com.loseit.core.client.model.DailyLogGoalsState/2438260065"


def wire(tokens, strings):
    return "//OK" + json.dumps(list(reversed(tokens)) + [strings, 0, 7])


def test_decode_identity_and_backreference():
    raw = wire(
        [1, 2, 2, 731, 3, -6, -2],
        ["java.util.ArrayList/4159755760", USER, "synthetic-user"],
    )
    decoded = gwt.decode_response(raw)
    assert decoded[0].fields == [731, "synthetic-user", -6]
    assert decoded[0] is decoded[1]


@pytest.mark.parametrize(
    "raw",
    [
        "//OK[]",
        "//OK[0,[],0,6]",
        '//OK[1,["Unknown/1"],0,7]',
        "//OK[0,[],0,7];evil()",
        "<html>login</html>",
        "//OK[0,[],0,7].concat([1])",
    ],
)
def test_schema_drift_is_never_empty_success(raw):
    c = load()
    with pytest.raises(c.LoseItProtocolError):
        gwt.decode_response(raw)


@pytest.mark.parametrize(
    "signature,tokens,error",
    [
        (
            "com.loseit.core.client.service.UserAuthenticationFailedException/2362299878",
            [1, 0, 2],
            "LoseItAuthError",
        ),
        (
            "com.google.gwt.user.client.rpc.IncompatibleRemoteServiceException/3936916533",
            [1, 2],
            "LoseItProtocolError",
        ),
        ("OtherException", [1], "LoseItProtocolError"),
    ],
)
def test_rpc_exceptions_sanitized(signature, tokens, error):
    c = load()
    with pytest.raises(getattr(c, error)) as exc:
        gwt.decode_response("//EX" + wire(tokens, [signature, "private-secret"])[4:])
    assert "private-secret" not in str(exc.value)


@pytest.mark.parametrize("tokens", [[1, 2], [1]])
def test_rpc_auth_name_in_message_or_malformed_exception_is_not_expiry(tokens):
    c = load()
    strings = [
        "com.google.gwt.user.client.rpc.SerializableException/3047383460",
        "UserAuthenticationFailedException private-secret",
    ]
    with pytest.raises(c.LoseItError) as exc:
        gwt.decode_response("//EX" + wire(tokens, strings)[4:])
    assert isinstance(exc.value, c.LoseItProtocolError)
    assert "private-secret" not in str(exc.value)


def test_account_from_decoded_embedded_user_not_jwt_guess():
    c = load()
    # Embedded data is a JSON string of a GWT array, not a raw JWT claim.
    raw = wire([1, 731, 2, -6], [USER, "synthetic-user"])
    html = "<script>window.embedded_4ppl1c4710n = " + json.dumps(raw[4:]) + ";</script>"
    session = Session(Response(body=html))
    client = c.LoseItClient(session, {"liauth": "synthetic"})
    account = asyncio.run(client.async_get_account())
    assert account == c.Account("731", None)
    assert len(session.calls) == 1
    assert asyncio.run(client.async_get_account()) is account


def test_signed_long_and_chunked_payload():
    assert (
        gwt.decode_response(
            '//OK["P__________",1].concat([["java.lang.Long/4227064769"],0,7])'
        )
        == -1
    )


def test_unknown_string_reference_rejected():
    c = load()
    with pytest.raises(c.LoseItProtocolError):
        gwt.decode_response(wire([1, 731, 99, -6], [USER]))

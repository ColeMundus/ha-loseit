"""Strictness and resource-bound regression tests."""

import asyncio
from datetime import UTC, datetime
from email.utils import format_datetime

import pytest
from test_client import Response, Session, load
from test_daily import DAY, FOODS, details, food
from test_protocol import wire

gwt = load("gwt")
protocol = load("protocol")
snapshot = load("snapshot")


def test_linked_hashmap_reads_access_order_flag_before_size():
    raw = wire(
        [1, 0, 1, 2, 3, 3, 4],
        [
            "java.util.LinkedHashMap/3008245022",
            "java.lang.Integer/3438268394",
            "java.lang.Double/858496421",
        ],
    )
    assert gwt.decode_response(raw) == [[3, 4]]


def test_treemap_reads_null_comparator_before_size():
    raw = wire([1, 0, 0], ["java.util.TreeMap/1493889780"])
    assert gwt.decode_response(raw) == []


@pytest.mark.parametrize(
    "raw",
    [
        wire([-1], []),
        wire([1, -1], ["java.util.ArrayList/4159755760"]),
        wire([1, 2], ["java.lang.Boolean/476441737"]),
        wire([1, "NaN"], ["java.lang.Double/858496421"]),
        wire([1, "not-a-long"], ["java.lang.Long/4227064769"]),
    ],
)
def test_invalid_reference_count_boolean_or_nonfinite_rejected(raw):
    c = load()
    with pytest.raises(c.LoseItProtocolError):
        gwt.decode_response(raw)


@pytest.mark.parametrize(
    "value,expected", [("nonsense", None), ("NaN", None), ("-1", 0.0), ("0.5", 0.5)]
)
def test_retry_after_invalid_and_fractional(value, expected):
    c = load()
    assert c._retry_after(value) == expected


def test_retry_after_http_date():
    c = load()
    from datetime import timedelta

    value = format_datetime(datetime.now(UTC) + timedelta(seconds=60), usegmt=True)
    assert 58 < c._retry_after(value) <= 60


def test_transport_body_limit_before_parse(monkeypatch):
    c = load()
    monkeypatch.setattr(c, "_MAX_BODY", 100)
    session = Session(Response(body="x" * 101))
    with pytest.raises(c.LoseItProtocolError, match="safety limit"):
        asyncio.run(c.LoseItClient(session, {"x": "y"}).async_get_account())


def test_bad_serving_scale_never_defaults_to_one():
    c = load()
    entry = food({13: "10"})
    entry.fields[2].fields[0].fields[0] = 0
    with pytest.raises(c.LoseItProtocolError, match="serving scale"):
        snapshot.parse_daily(details(gwt.ProtocolObject(FOODS, [entry])), DAY)


def test_schema_objects_do_not_repr_personal_fields():
    assert "private-secret" not in repr(
        gwt.ProtocolObject("test/1", ["private-secret"])
    )


def test_request_serialization_escapes_gwt_string_table():
    payload = protocol.daily_request(DAY, (731, "synthetic|\\\x00name", -6))
    assert "synthetic\\!\\\\\\0name" in payload
    assert gwt._long(protocol._encode_long(-1)) == -1


def test_html_success_never_becomes_empty_day():
    c = load()
    client = c.LoseItClient(Session(Response(body="<html>sign in</html>")), {"x": "y"})
    with pytest.raises(c.LoseItError) as exc:
        asyncio.run(client.async_get_day(DAY))
    assert not isinstance(exc.value, c.LoseItAuthError)

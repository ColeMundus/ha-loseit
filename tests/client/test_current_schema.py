"""Current first-party serializers, with entirely synthetic wire values."""

from decimal import Decimal

import pytest
from test_client import load
from test_protocol import wire

gwt = load("gwt")

GOALS = "com.loseit.core.client.model.GoalsSummary/26794011"


def test_sql_timestamp_preserves_milliseconds_and_nanoseconds():
    signature = "java.sql.Timestamp/3040052672"
    result = gwt.decode_response(wire([1, "Po", 123000000], [signature]))
    assert result.fields == [1000, 123000000]


@pytest.mark.parametrize("nanos", [-1, 1000000000])
def test_sql_timestamp_rejects_out_of_range_nanoseconds(nanos):
    c = load()
    with pytest.raises(c.LoseItProtocolError):
        gwt.decode_response(wire([1, "Po", nanos], ["java.sql.Timestamp/3040052672"]))


def test_current_goals_reader_includes_numeric_p_field_not_old_boolean():
    # ePg/gPg: a,b,c,d,e,f,g,i,j,k,n,o,p,q,r,s,t,u,v,w,A,B.
    tokens = [
        1,
        0,
        0,
        1,
        123.5,
        0,
        0,
        81.25,
        0,
        0,
        0,
        70.5,
        0,
        0.75,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        1550.5,
        1,
    ]
    result = gwt.decode_response(wire(tokens, [GOALS]))
    assert result.signature == GOALS
    assert result.fields[6] == Decimal("81.25")
    assert result.fields[10] == Decimal("70.5")
    assert result.fields[11] is False
    assert result.fields[12] == Decimal("0.75")
    assert result.fields[20] == Decimal("1550.5")
    assert result.fields[21] is True

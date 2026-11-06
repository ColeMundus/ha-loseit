"""Pure account bootstrap parsing and the single reviewed daily read request."""

from __future__ import annotations

import json
import re
from datetime import date

from .gwt import ProtocolObject, decode_response, walk
from .models import LoseItAccessError, LoseItProtocolError
from .schemas import EPOCH, MODULE_BASE, POLICY

_USER = "com.loseit.core.client.model.UserId/4281239478"
_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789$_"


def parse_identity(html: str) -> tuple[int, str, int]:
    match = re.search(r'window\.embedded_4ppl1c4710n\s*=\s*("(?:[^"\\]|\\.)*")', html)
    if match is None:
        raise LoseItAccessError("Lose It authenticated page unavailable")
    try:
        embedded = json.loads(match.group(1))
        root = decode_response(
            embedded if embedded.startswith("//") else "//OK" + embedded
        )
        identities = [
            n
            for n in walk(root)
            if isinstance(n, ProtocolObject) and n.signature == _USER
        ]
        unique = {(n.fields[0], n.fields[1], n.fields[2]) for n in identities}
        if len(unique) != 1:
            raise ValueError
        user_id, username, offset = unique.pop()
        if type(user_id) is not int or user_id <= 0 or not isinstance(username, str):
            raise ValueError
        if type(offset) is not int or not -12 <= offset <= 14:
            raise ValueError
    except (ValueError, TypeError, IndexError, AttributeError):
        raise LoseItProtocolError(
            "Unsupported Lose It embedded account schema"
        ) from None
    return user_id, username, offset


def _encode_long(value: int) -> str:
    value &= (1 << 64) - 1
    chars = []
    while value:
        chars.append(_ALPHABET[value & 63])
        value >>= 6
    return "".join(reversed(chars)) or "A"


def daily_request(day: date, identity: tuple[int, str, int]) -> str:
    user_id, username, offset = identity
    # Use the service's explicit offset, never the HA host's local timezone.
    # An offset is NOT an IANA zone; historical/DST offset recovery is unsupported.
    epoch_seconds = (day - date(1970, 1, 1)).days * 86400 - offset * 3600
    strings = [
        MODULE_BASE,
        POLICY,
        "com.loseit.core.client.service.LoseItRemoteService",
        "getDailyDetailsIncludingPendingForDate",
        "com.loseit.core.client.service.ServiceRequestToken/1076571655",
        "com.loseit.core.shared.model.DayDate/1611136587",
        _USER,
        username,
        "java.util.Date/3385151746",
    ]

    def escape(value: str) -> str:
        return value.replace("\\", "\\\\").replace("|", "\\!").replace("\x00", "\\0")

    tokens = [
        1,
        2,
        3,
        4,
        2,
        5,
        6,
        5,
        0,
        7,
        user_id,
        8,
        offset,
        6,
        9,
        _encode_long(epoch_seconds * 1000),
        (day - EPOCH).days,
        offset,
    ]
    return (
        "|".join(
            [
                "7",
                "0",
                str(len(strings)),
                *(escape(s) for s in strings),
                *(str(t) for t in tokens),
            ]
        )
        + "|"
    )

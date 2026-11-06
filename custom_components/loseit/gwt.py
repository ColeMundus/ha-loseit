"""Bounded JSON-only GWT decoding and validated protocol object access."""

from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from .models import LoseItAuthError, LoseItProtocolError
from .schemas import ARRAYS, LAYOUTS

MAX_BODY = 4 * 1024 * 1024
_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789$_"


@dataclass(repr=False)
class ProtocolObject:
    signature: str
    fields: list[Any]

    def __repr__(self) -> str:
        return "<LoseIt protocol object>"


def walk(root: Any) -> Any:
    stack, seen = [root], set()
    while stack:
        value = stack.pop()
        if isinstance(value, (ProtocolObject, list)):
            if id(value) in seen:
                continue
            seen.add(id(value))
            stack.extend(value.fields if isinstance(value, ProtocolObject) else value)
        yield value


def _long(text: str) -> int:
    if not isinstance(text, str) or not 1 <= len(text) <= 11:
        raise ValueError
    number = 0
    for char in text:
        number = (number << 6) | _ALPHABET.index(char)
    if number >= 1 << 64:
        raise ValueError
    return number - (1 << 64) if number >= (1 << 63) else number


class _Reader:
    def __init__(self, values: list[Any], strings: list[str]):
        self.values, self.strings = values, strings
        self.references: list[Any] = []

    def raw(self) -> Any:
        return self.values.pop()

    def integer(self) -> int:
        value = self.raw()
        if type(value) is not int:
            raise ValueError
        return value

    def string(self) -> str | None:
        ref = self.integer()
        if ref == 0:
            return None
        if not 1 <= ref <= len(self.strings):
            raise ValueError
        return self.strings[ref - 1]

    def count(self) -> int:
        count = self.integer()
        if not 0 <= count <= min(100000, len(self.values)):
            raise ValueError
        return count

    def field(self, kind: str, depth: int) -> Any:
        if kind == "o":
            return self.object(depth + 1)
        if kind == "s":
            return self.string()
        if kind == "i":
            return self.integer()
        if kind == "l":
            return _long(self.raw())
        if kind == "b":
            value = self.integer()
            if value not in (0, 1):
                raise ValueError
            return bool(value)
        if kind == "d":
            value = self.raw()
            if isinstance(value, bool) or not isinstance(value, (int, float, str)):
                raise ValueError
            number = Decimal(str(value))
            if not number.is_finite():
                raise ValueError
            return number
        raise ValueError

    def object(self, depth: int = 0) -> Any:
        if depth > 100:
            raise ValueError
        ref = self.integer()
        if ref == 0:
            return None
        if ref < 0:
            index = -ref - 1
            if not 0 <= index < len(self.references):
                raise ValueError
            return self.references[index]
        if ref > len(self.strings):
            raise ValueError
        signature = self.strings[ref - 1]
        node = ProtocolObject(signature, [])
        slot = len(self.references)
        self.references.append(node)
        primitive = {
            "java.lang.Integer/3438268394": "i",
            "java.lang.Double/858496421": "d",
            "java.lang.Float/1718559123": "d",
            "java.lang.Boolean/476441737": "b",
            "java.lang.Long/4227064769": "l",
            "java.lang.String/2004016611": "s",
            "java.util.Date/3385151746": "l",
        }
        if signature in primitive:
            result = self.field(primitive[signature], depth)
        elif signature.startswith(("[L", "[B/", "[I/")):
            # Array signatures themselves are checked against the pinned catalog.
            if signature not in ARRAYS:
                raise ValueError
            kind = "o" if signature.startswith("[L") else "i"
            node.fields.extend(self.field(kind, depth) for _ in range(self.count()))
            return node
        elif signature in (
            "java.util.ArrayList/4159755760",
            "java.util.HashSet/3273092938",
            "java.util.LinkedHashSet/95640124",
            "java.util.Arrays$ArrayList/2507071751",
        ):
            result = []
            self.references[slot] = result
            result.extend(self.object(depth + 1) for _ in range(self.count()))
        elif signature in (
            "java.util.HashMap/1797211028",
            "java.util.LinkedHashMap/3008245022",
            "java.util.TreeMap/1493889780",
            "java.util.IdentityHashMap/1839153020",
        ):
            # Retain entries as pairs: domain enum keys need not be hashable.
            # Instantiation metadata precedes the entry count on these types.
            if signature == "java.util.LinkedHashMap/3008245022":
                self.field("b", depth)
            elif signature == "java.util.TreeMap/1493889780":
                comparator = self.object(depth + 1)
                if comparator is not None:
                    raise ValueError
            result = []
            self.references[slot] = result
            for _ in range(self.count()):
                result.append([self.object(depth + 1), self.object(depth + 1)])
        elif signature in LAYOUTS:
            layout = LAYOUTS[signature]
            if layout == "e":
                ordinal = self.integer()
                if ordinal < 0:
                    raise ValueError
                node.fields.append(ordinal)
            else:
                node.fields.extend(self.field(kind, depth) for kind in layout)
                if (
                    signature == "java.sql.Timestamp/3040052672"
                    and not 0 <= node.fields[1] <= 999999999
                ):
                    # VGv (called by wEd) rejects invalid nanoseconds too.
                    raise ValueError
            return node
        else:
            raise ValueError
        self.references[slot] = result
        return result


def _payload(text: str) -> list[Any]:
    decoder = json.JSONDecoder(
        parse_constant=lambda _: (_ for _ in ()).throw(ValueError())
    )
    result, pos = decoder.raw_decode(text)
    if not isinstance(result, list):
        raise ValueError
    while text.startswith(".concat(", pos):
        pos += 8
        while True:
            chunk, pos = decoder.raw_decode(text, pos)
            if not isinstance(chunk, list):
                raise ValueError
            result.extend(chunk)
            if text[pos : pos + 1] == ",":
                pos += 1
                continue
            if text[pos : pos + 1] != ")":
                raise ValueError
            pos += 1
            break
    if text[pos:].strip():
        raise ValueError
    return result


def decode_response(raw: str) -> Any:
    """Strict bounded v7 GWT parser. Never executes JavaScript or logs a body."""
    if (
        not isinstance(raw, str)
        or len(raw) > MAX_BODY
        or not raw.startswith(("//OK", "//EX"))
    ):
        raise LoseItProtocolError("Invalid Lose It RPC envelope")
    try:
        payload = _payload(raw[4:])
        if len(payload) < 4 or payload[-2:] != [0, 7]:
            raise ValueError
        strings = payload[-3]
        if not isinstance(strings, list) or not all(
            isinstance(s, str) for s in strings
        ):
            raise ValueError
        reader = _Reader(payload[:-3], strings)
        result = reader.object()
        if reader.values:
            raise ValueError
        if raw.startswith("//EX"):
            if isinstance(result, ProtocolObject) and result.signature == (
                "com.loseit.core.client.service."
                "UserAuthenticationFailedException/2362299878"
            ):
                raise LoseItAuthError("Lose It session rejected")
            raise LoseItProtocolError("Lose It RPC rejected; schema may have changed")
        return result
    except (
        ValueError,
        TypeError,
        IndexError,
        KeyError,
        RecursionError,
        ArithmeticError,
    ):
        raise LoseItProtocolError(
            "Unsupported or malformed Lose It RPC schema"
        ) from None


def fields(value: Any, name: str) -> list[Any]:
    if not isinstance(value, ProtocolObject) or value.signature not in LAYOUTS:
        raise LoseItProtocolError("Unexpected Lose It object schema")
    if value.signature.split("/")[0].split(".")[-1] != name or len(value.fields) != len(
        LAYOUTS[value.signature]
    ):
        raise LoseItProtocolError("Unexpected Lose It object layout")
    return value.fields

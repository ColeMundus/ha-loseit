"""Shared real Home Assistant harness configuration."""

import pytest
import pytest_socket

pytest_plugins = ["pytest_homeassistant_custom_component"]


@pytest.hookimpl(trylast=True)
def pytest_runtest_setup() -> None:
    """Allow local Unix mock transports, without enabling real network.

    The pinned HA plugin allows Unix socket creation, but its separate
    socket_allow_hosts call otherwise blocks Unix connect() in pytest-socket.
    Preserve the harness's loopback-only destination policy and allow Unix IPC.
    """
    pytest_socket.socket_allow_hosts(["127.0.0.1"], allow_unix_socket=True)

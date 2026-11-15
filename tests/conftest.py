"""Shared real Home Assistant harness configuration."""

import pytest
import pytest_socket

pytest_plugins = ["pytest_homeassistant_custom_component"]


@pytest.hookimpl(trylast=True)
def pytest_runtest_setup(item: pytest.Item) -> None:
    """Keep loopback fixtures and Unix IPC inside the offline socket guard.

    Setup order follows site-packages directory order, so the pinned HA plugin
    can disable socket creation after pytest-socket has honored enable_socket.
    This hook runs last and restores that opt-in. connect() stays limited to
    127.0.0.1, Unix connect stays available for local mock transports, and
    every other test keeps the HA plugin's socket-creation block.
    """
    opted_in = item.get_closest_marker("enable_socket") is not None or (
        "socket_enabled" in getattr(item, "fixturenames", ())
    )
    if opted_in:
        pytest_socket.enable_socket()
    pytest_socket.socket_allow_hosts(["127.0.0.1"], allow_unix_socket=True)

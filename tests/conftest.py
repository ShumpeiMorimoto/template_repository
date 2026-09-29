"""Shared pytest fixtures."""

import socket

import pytest

_LOCAL_HOSTS = ("127.0.0.1", "::1", "localhost")


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "allow_network: let this test open real outbound sockets")


@pytest.fixture(autouse=True)
def _no_outbound_network(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch) -> None:
    """Fail loudly instead of silently hitting real services from the test suite."""
    if request.node.get_closest_marker("allow_network"):
        return

    real_connect = socket.socket.connect

    def _guarded_connect(self: socket.socket, address, *args, **kwargs):
        host = address[0] if isinstance(address, tuple) else address
        if isinstance(host, str) and host not in _LOCAL_HOSTS:
            raise AssertionError(f"test tried to open a real socket to {host} — mock the call")
        return real_connect(self, address, *args, **kwargs)

    monkeypatch.setattr(socket.socket, "connect", _guarded_connect)

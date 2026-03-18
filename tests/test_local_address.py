"""
Tests for the local_address parameter.

local_address binds the outgoing TCP connection to a specific local IP,
useful on multi-homed hosts.  Unit tests cover schema serialisation and
invalid-IP validation; the live test makes a real request with the
loopback address (127.0.0.1) binding to verify end-to-end wiring.
"""

import socket
import pytest
from cycletls import CycleTLS
from cycletls.schema import Request
from cycletls.exceptions import ConnectionError as CycleTLSConnectionError


# ---------------------------------------------------------------------------
# Unit tests — no network required
# ---------------------------------------------------------------------------

class TestLocalAddressSchema:
    """local_address is correctly serialised into the request payload."""

    def test_local_address_included_when_set(self):
        req = Request(method="GET", url="https://example.com", local_address="192.168.1.10")
        payload = req.to_dict()
        assert payload["localAddress"] == "192.168.1.10"

    def test_local_address_omitted_when_none(self):
        req = Request(method="GET", url="https://example.com")
        payload = req.to_dict()
        assert "localAddress" not in payload

    def test_local_address_default_is_none(self):
        req = Request(method="GET", url="https://example.com")
        assert req.local_address is None


class TestLocalAddressValidation:
    """The Go layer rejects invalid IP addresses."""

    def test_invalid_local_address_raises(self):
        """A non-IP string must raise an error, not silently succeed."""
        with CycleTLS() as client:
            with pytest.raises(Exception) as exc_info:
                client.get(
                    "https://httpbin.org/get",
                    local_address="not-an-ip-address",
                    enable_connection_reuse=False,
                    timeout=10,
                )
            assert "invalid" in str(exc_info.value).lower() or \
                   "local_address" in str(exc_info.value).lower() or \
                   "not a valid" in str(exc_info.value).lower()


# ---------------------------------------------------------------------------
# Live test — requires network access
# ---------------------------------------------------------------------------

@pytest.mark.live
class TestLocalAddressLive:
    """Verify that local_address is wired through to the dialer."""

    def test_local_address_loopback(self):
        """
        Binding to 127.0.0.1 and connecting to an httpbin endpoint works
        as long as the OS allows source-IP 127.0.0.1 for outbound traffic
        (Linux does by default; the connection may fail on strict systems,
        in which case we skip rather than fail).
        """
        with CycleTLS() as client:
            try:
                response = client.get(
                    "https://httpbin.org/get",
                    local_address="127.0.0.1",
                    enable_connection_reuse=False,
                    timeout=15,
                )
                assert response.status_code == 200
            except (CycleTLSConnectionError, Exception) as exc:
                msg = str(exc).lower()
                # Some OS/network configurations refuse source-IP 127.0.0.1
                # for non-loopback destinations — skip instead of failing.
                if any(w in msg for w in ("invalid", "cannot assign", "bind", "network unreachable")):
                    pytest.skip(f"OS rejected loopback source binding: {exc}")
                raise

    def test_local_address_default_outbound_ip(self):
        """Binding to the machine's own outbound IP works for a normal request."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
        except Exception:
            pytest.skip("Could not determine local outbound IP")

        with CycleTLS() as client:
            response = client.get(
                "https://httpbin.org/get",
                local_address=local_ip,
                enable_connection_reuse=False,
                timeout=15,
            )
            assert response.status_code == 200
